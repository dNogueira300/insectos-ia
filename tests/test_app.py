import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app import crear_app
from backend.servicio import ErrorImagen
from pipeline.inferencia import Prediccion

PREDICCION = Prediccion(
    orden="Coleoptera",
    confianza_orden=0.93,
    familia="Curculionidae",
    confianza_familia=0.71,
    familia_incierta=False,
    top_familias=(("Curculionidae", 0.71), ("Chrysomelidae", 0.22)),
)


class ServicioFalso:
    def __init__(self, prediccion=PREDICCION, falla=False):
        self.prediccion = prediccion
        self.falla = falla

    def predecir_bytes(self, datos):
        if self.falla:
            raise ErrorImagen("el archivo no es una imagen válida")
        return self.prediccion

    def clases(self):
        return {
            "ordenes": ["Coleoptera", "Odonata"],
            "familias": ["Curculionidae"],
            "matriz": [[True, False]],
        }

    def version(self):
        return {
            "modelo": "insectos.onnx",
            "n_ordenes": 2,
            "n_familias": 1,
            "umbral_familia": 0.7,
            "lado": 288,
        }


class RepositorioFalso:
    def __init__(self, fichas=None, hay_base=True):
        self.fichas = fichas if fichas is not None else [{"ID": "INS-0001", "Nombre_comun": "gorgojo"}]
        self.hay_base = hay_base

    def disponible(self):
        return self.hay_base

    def por_taxon(self, orden, familia=""):
        self.consultado = (orden, familia)
        return self.fichas

    def resumen_por_orden(self):
        return [{"orden": "Coleoptera", "registros": 1}]


def cliente(servicio=None, repositorio=None):
    return TestClient(crear_app(servicio or ServicioFalso(), repositorio or RepositorioFalso()))


def archivo_jpg():
    rng = np.random.default_rng(1)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(base).resize((300, 300)).save(buffer, "JPEG")
    buffer.seek(0)
    return {"archivo": ("insecto.jpg", buffer, "image/jpeg")}


def test_salud_responde_ok():
    respuesta = cliente().get("/salud")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["n_ordenes"] == 2
    assert cuerpo["bd_disponible"] is True


def test_salud_reporta_base_ausente():
    cuerpo = cliente(repositorio=RepositorioFalso(hay_base=False)).get("/salud").json()
    assert cuerpo["bd_disponible"] is False


def test_clases_devuelve_la_ontologia():
    cuerpo = cliente().get("/clases").json()
    assert cuerpo["ordenes"] == ["Coleoptera", "Odonata"]


def test_predecir_devuelve_la_jerarquia():
    cuerpo = cliente().post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["orden"] == "Coleoptera"
    assert cuerpo["familia"] == "Curculionidae"
    assert cuerpo["confianza_orden"] == pytest.approx(0.93)
    assert cuerpo["familia_incierta"] is False


def test_predecir_incluye_el_top_de_familias_con_nombres():
    cuerpo = cliente().post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["top_familias"][0] == {"familia": "Curculionidae", "confianza": pytest.approx(0.71)}


def test_predecir_adjunta_las_fichas_de_la_base():
    cuerpo = cliente().post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["fichas"][0]["Nombre_comun"] == "gorgojo"


def test_predecir_sin_base_devuelve_fichas_vacias():
    repositorio = RepositorioFalso(fichas=[], hay_base=False)
    cuerpo = cliente(repositorio=repositorio).post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["fichas"] == []
    assert cuerpo["orden"] == "Coleoptera"  # la predicción sigue funcionando


def test_predecir_con_archivo_invalido_da_400_en_espanol():
    respuesta = cliente(servicio=ServicioFalso(falla=True)).post("/predecir", files=archivo_jpg())
    assert respuesta.status_code == 400
    assert "imagen" in respuesta.json()["detail"].lower()


def test_predecir_sin_archivo_da_422():
    assert cliente().post("/predecir").status_code == 422


def test_familia_incierta_se_propaga_al_cliente():
    incierta = Prediccion(
        orden="Coleoptera",
        confianza_orden=0.88,
        familia="Curculionidae",
        confianza_familia=0.31,
        familia_incierta=True,
        top_familias=(("Curculionidae", 0.31), ("Chrysomelidae", 0.29)),
    )
    cuerpo = cliente(servicio=ServicioFalso(incierta)).post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["familia_incierta"] is True


def test_taxon_devuelve_las_fichas_del_orden():
    cuerpo = cliente().get("/taxon/Coleoptera").json()
    assert cuerpo["orden"] == "Coleoptera"
    assert len(cuerpo["fichas"]) == 1


def test_taxon_acepta_familia_por_query():
    cuerpo = cliente().get("/taxon/Coleoptera", params={"familia": "Curculionidae"}).json()
    assert cuerpo["familia"] == "Curculionidae"


def test_cors_permite_al_frontend_de_desarrollo():
    respuesta = cliente().get("/salud", headers={"Origin": "http://localhost:5173"})
    assert respuesta.headers.get("access-control-allow-origin") is not None


def test_salud_informa_la_resolucion_del_modelo():
    assert cliente().get("/salud").json()["lado"] == 288


def test_con_familia_incierta_las_fichas_son_del_orden():
    """Si la familia es incierta no se muestra la ficha de la candidata como si
    estuviera confirmada: se buscan las fichas del orden."""
    incierta = Prediccion(
        orden="Coleoptera",
        confianza_orden=0.88,
        familia="Curculionidae",
        confianza_familia=0.31,
        familia_incierta=True,
        top_familias=(("Curculionidae", 0.31), ("Chrysomelidae", 0.29)),
    )
    repositorio = RepositorioFalso()
    cliente(servicio=ServicioFalso(incierta), repositorio=repositorio).post(
        "/predecir", files=archivo_jpg()
    )
    assert repositorio.consultado == ("Coleoptera", "")


def test_con_familia_segura_las_fichas_son_de_la_familia():
    repositorio = RepositorioFalso()
    cliente(repositorio=repositorio).post("/predecir", files=archivo_jpg())
    assert repositorio.consultado == ("Coleoptera", "Curculionidae")
