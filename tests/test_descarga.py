import io
from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.descarga import (
    COLUMNAS_MANIFIESTO,
    descargar_clase,
    escribir_manifiesto,
    leer_manifiesto,
)
from pipeline.inat import Observacion


def bytes_imagen(lado=400):
    rng = np.random.default_rng(1)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(base).resize((lado, lado)).save(buffer, "JPEG")
    return buffer.getvalue()


class SesionImagenOK:
    def __init__(self, lado=400):
        self.contenido = bytes_imagen(lado)
        self.pedidos = []

    def get(self, url, timeout=None):
        self.pedidos.append(url)
        return type("R", (), {"content": self.contenido, "raise_for_status": lambda s: None})()


def obs(oid, licencia="cc-by", observador=None):
    return Observacion(
        id=oid,
        taxon_id=62956,
        taxon_nombre="Ejemplo sp.",
        rango="species",
        observador=observador or f"u{oid}",
        foto_url=f"https://x/{oid}/medium.jpg",
        licencia=licencia,
        atribucion="(c) alguien",
        latitud=-3.7,
        longitud=-73.2,
        fecha="2026-02-01",
    )


def falso_iterador(observaciones):
    def _iterar(taxon_id, *, limite, **kwargs):
        for i, o in enumerate(observaciones):
            if i >= limite:
                return
            yield o

    return _iterar


def test_descarga_guarda_archivos_y_devuelve_filas(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(1), obs(2)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert len(filas) == 2
    for fila in filas:
        assert set(fila) == set(COLUMNAS_MANIFIESTO)
        assert (tmp_path / fila["archivo"]).exists()


def test_ruta_de_archivo_refleja_orden_y_familia(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(7)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=1, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert filas[0]["archivo"] == "OrdenA/FamiliaX/7.jpg"


def test_sin_familia_va_a_carpeta_propia(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(8)]))
    filas = descargar_clase(
        "OrdenA", "", 47208,
        cupo=1, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert filas[0]["archivo"] == "OrdenA/_sin_familia/8.jpg"
    assert filas[0]["familia"] == ""


def test_descarta_licencias_no_permitidas(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(
        mod, "iterar_observaciones", falso_iterador([obs(1, licencia=""), obs(2, licencia="cc0")])
    )
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert [f["obs_id"] for f in filas] == [2]


def test_salta_observaciones_ya_descargadas(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(1), obs(2), obs(3)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados={1, 3},
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert [f["obs_id"] for f in filas] == [2]


def test_respeta_el_cupo(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(i) for i in range(1, 30)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=4, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert len(filas) == 4


def test_imagen_chica_no_entra_al_manifiesto(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(1)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(lado=100), pausa=0,
    )
    assert filas == []


def test_manifiesto_ida_y_vuelta(tmp_path: Path):
    filas = [
        {c: "" for c in COLUMNAS_MANIFIESTO} | {"archivo": "A/B/1.jpg", "obs_id": 1, "observador": "u1"}
    ]
    ruta = tmp_path / "manifiesto.csv"
    escribir_manifiesto(filas, ruta)
    leidas = leer_manifiesto(ruta)
    assert leidas[0]["archivo"] == "A/B/1.jpg"
    assert leidas[0]["obs_id"] == "1"


def test_leer_manifiesto_inexistente_da_lista_vacia(tmp_path: Path):
    assert leer_manifiesto(tmp_path / "no_existe.csv") == []
