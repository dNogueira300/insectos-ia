import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from backend.servicio import ErrorImagen, ServicioInsectos
from pipeline.etiquetas import EspacioEtiquetas

ESPACIO = EspacioEtiquetas(
    ordenes=("OrdenA", "OrdenB"),
    familias=("FamA1", "FamA2", "FamB1"),
    matriz=((True, False), (True, False), (False, True)),
)


def exportar_diminuto(carpeta: Path, lado: int) -> tuple[Path, Path]:
    """Exporta un ONNX diminuto con dos salidas, sin entrenar nada.

    Como el exportador real, fija alto y ancho y deja libre solo el lote.
    """
    torch = pytest.importorskip("torch")

    class Diminuto(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.orden = torch.nn.Linear(3, 2)
            self.familia = torch.nn.Linear(3, 3)

        def forward(self, x):
            rasgos = x.mean(dim=(2, 3))
            return self.orden(rasgos), self.familia(rasgos)

    ruta_onnx = carpeta / f"m{lado}.onnx"
    torch.onnx.export(
        Diminuto(),
        torch.randn(1, 3, lado, lado),
        str(ruta_onnx),
        input_names=["imagen"],
        output_names=["logits_orden", "logits_familia"],
        dynamic_axes={"imagen": {0: "lote"}},
        opset_version=17,
    )
    ruta_etiquetas = carpeta / "etiquetas.json"
    ESPACIO.guardar(ruta_etiquetas)
    return ruta_onnx, ruta_etiquetas


@pytest.fixture
def modelo_falso(tmp_path: Path) -> tuple[Path, Path]:
    return exportar_diminuto(tmp_path, 224)


def bytes_imagen(lado=300):
    rng = np.random.default_rng(3)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(base).resize((lado, lado)).save(buffer, "JPEG")
    return buffer.getvalue()


def test_predecir_devuelve_orden_y_familia_del_espacio(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    prediccion = servicio.predecir_bytes(bytes_imagen())
    assert prediccion.orden in ESPACIO.ordenes
    assert prediccion.familia in ESPACIO.familias


def test_la_familia_siempre_pertenece_al_orden_predicho(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    prediccion = servicio.predecir_bytes(bytes_imagen())
    indice_familia = ESPACIO.familias.index(prediccion.familia)
    indice_orden = ESPACIO.ordenes.index(prediccion.orden)
    assert ESPACIO.matriz[indice_familia][indice_orden] is True


def test_las_confianzas_estan_entre_cero_y_uno(modelo_falso):
    prediccion = ServicioInsectos(*modelo_falso).predecir_bytes(bytes_imagen())
    assert 0.0 <= prediccion.confianza_orden <= 1.0
    assert 0.0 <= prediccion.confianza_familia <= 1.0


def test_umbral_alto_marca_la_familia_como_incierta(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso, umbral=1.1)
    assert servicio.predecir_bytes(bytes_imagen()).familia_incierta is True


def test_umbral_cero_nunca_marca_incertidumbre(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso, umbral=0.0)
    assert servicio.predecir_bytes(bytes_imagen()).familia_incierta is False


def test_imagen_invalida_lanza_error_de_imagen(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    with pytest.raises(ErrorImagen):
        servicio.predecir_bytes(b"no soy una imagen")


def test_clases_expone_la_ontologia_vigente(modelo_falso):
    clases = ServicioInsectos(*modelo_falso).clases()
    assert clases["ordenes"] == list(ESPACIO.ordenes)
    assert clases["familias"] == list(ESPACIO.familias)


def test_version_reporta_los_artefactos_cargados(modelo_falso):
    version = ServicioInsectos(*modelo_falso).version()
    assert version["n_ordenes"] == 2
    assert version["n_familias"] == 3
    assert "umbral_familia" in version


def test_el_servicio_toma_la_resolucion_del_modelo(tmp_path):
    """La v4 se entrenó a 288: el backend debe prepararle las fotos a 288.

    onnxruntime rechaza una entrada de otro tamaño, así que un servicio que
    preparara siempre a 224 fallaría aquí.
    """
    servicio = ServicioInsectos(*exportar_diminuto(tmp_path, 288))
    assert servicio.lado == 288
    assert servicio.predecir_bytes(bytes_imagen()).orden in ESPACIO.ordenes


def test_version_incluye_la_resolucion(modelo_falso):
    assert ServicioInsectos(*modelo_falso).version()["lado"] == 224


def test_el_modelo_se_carga_una_sola_vez(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    primera = servicio.sesion
    servicio.predecir_bytes(bytes_imagen())
    servicio.predecir_bytes(bytes_imagen())
    assert servicio.sesion is primera


def test_prediccion_es_determinista(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    datos = bytes_imagen()
    a = servicio.predecir_bytes(datos)
    b = servicio.predecir_bytes(datos)
    assert a == b
