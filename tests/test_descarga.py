import csv
import io
from pathlib import Path

import numpy as np
import pytest
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


def test_escritura_interrumpida_no_trunca_el_manifiesto_anterior(tmp_path: Path, monkeypatch):
    """Una escritura que revienta a mitad de camino no debe tocar el archivo anterior.

    `escribir_manifiesto` nunca debe escribir directamente sobre el destino:
    arma el CSV completo en un temporal y solo lo promueve con `os.replace`
    cuando termina sin errores. Se simula el corte parcheando
    `csv.DictWriter.writerows` (el paso que vuelca el cuerpo del CSV, ya con
    la cabecera escrita) para que falle, sin matar el proceso de verdad.
    """
    ruta = tmp_path / "manifiesto.csv"
    filas_previas = [
        {c: "" for c in COLUMNAS_MANIFIESTO} | {"archivo": f"A/B/{i}.jpg", "obs_id": str(i)}
        for i in range(1, 51)
    ]
    escribir_manifiesto(filas_previas, ruta)
    contenido_previo = ruta.read_text(encoding="utf-8")
    assert len(leer_manifiesto(ruta)) == 50

    def _revienta(self, filas):
        raise OSError("fallo de disco simulado a mitad de la reescritura")

    monkeypatch.setattr(csv.DictWriter, "writerows", _revienta)

    filas_nuevas = filas_previas + [
        {c: "" for c in COLUMNAS_MANIFIESTO} | {"archivo": "A/B/99.jpg", "obs_id": "99"}
    ]
    with pytest.raises(OSError):
        escribir_manifiesto(filas_nuevas, ruta)

    assert ruta.read_text(encoding="utf-8") == contenido_previo
    assert len(leer_manifiesto(ruta)) == 50


def test_escritura_interrumpida_no_deja_temporales_huerfanos(tmp_path: Path, monkeypatch):
    ruta = tmp_path / "manifiesto.csv"
    escribir_manifiesto([], ruta)

    def _revienta(self, filas):
        raise OSError("fallo de disco simulado a mitad de la reescritura")

    monkeypatch.setattr(csv.DictWriter, "writerows", _revienta)

    with pytest.raises(OSError):
        escribir_manifiesto([{c: "" for c in COLUMNAS_MANIFIESTO}], ruta)

    restantes = sorted(p.name for p in tmp_path.iterdir())
    assert restantes == ["manifiesto.csv"]


def test_manifiesto_se_persiste_a_mitad_de_una_clase(tmp_path: Path, monkeypatch):
    """Un corte a mitad de una clase no debe dejar el manifiesto vacío.

    Se fuerza un fallo en `guardar_jpeg` (no capturado por `descargar_clase`,
    a diferencia de los fallos de descarga de imagen) después de la quinta
    observación, simulando que el proceso muere ahí. Con
    `intervalo_persistencia=2` deben quedar en disco las filas de los dos
    últimos volcados parciales completados (4), no ninguna.
    """
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(i) for i in range(1, 6)]))

    contador = {"n": 0}
    guardar_original = mod.imagenes.guardar_jpeg

    def guardar_que_revienta_en_la_quinta(img, ruta):
        contador["n"] += 1
        if contador["n"] == 5:
            raise RuntimeError("corte simulado a mitad de la clase")
        guardar_original(img, ruta)

    monkeypatch.setattr(mod.imagenes, "guardar_jpeg", guardar_que_revienta_en_la_quinta)

    with pytest.raises(RuntimeError):
        descargar_clase(
            "OrdenA", "FamiliaX", 62956,
            cupo=5, raiz=tmp_path, ya_descargados=set(),
            sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
            intervalo_persistencia=2,
        )

    filas_persistidas = leer_manifiesto(tmp_path / "manifiesto.csv")
    assert len(filas_persistidas) == 4
    assert [f["obs_id"] for f in filas_persistidas] == ["1", "2", "3", "4"]
