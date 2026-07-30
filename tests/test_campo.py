from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.campo import detectar_colisiones, ingerir
from pipeline.ontologia import cargar_ontologia


def escribir_imagen(raiz: Path, relativo: str, semilla: int, lado: int = 300):
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    destino = raiz / relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(base).resize((lado, lado), Image.BICUBIC).save(destino, "JPEG", quality=90)


def test_ingerir_lee_orden_y_familia_de_la_ruta(tmp_path: Path, ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(tmp_path, "Coleoptera/Curculionidae/foto1.jpg", 1)
    filas, errores = ingerir(tmp_path, onto)
    assert errores == []
    assert filas[0]["orden"] == "Coleoptera"
    assert filas[0]["familia"] == "Curculionidae"
    assert filas[0]["fuente"] == "campo"
    assert filas[0]["hash"]


def test_ingerir_acepta_carpeta_sin_familia(tmp_path: Path, ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(tmp_path, "Coleoptera/_sin_familia/foto1.jpg", 2)
    filas, errores = ingerir(tmp_path, onto)
    assert errores == []
    assert filas[0]["familia"] == ""


def test_ingerir_reporta_orden_desconocido(tmp_path: Path, ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(tmp_path, "Inventado/FamY/foto1.jpg", 3)
    filas, errores = ingerir(tmp_path, onto)
    assert filas == []
    assert any("Inventado" in e for e in errores)


def test_ingerir_reporta_familia_de_otro_orden(tmp_path: Path, ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(tmp_path, "Odonata/Curculionidae/foto1.jpg", 4)
    filas, errores = ingerir(tmp_path, onto)
    assert filas == []
    assert any("Curculionidae" in e for e in errores)


def test_ingerir_reporta_archivo_ilegible(tmp_path: Path, ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    destino = tmp_path / "Coleoptera" / "Curculionidae" / "roto.jpg"
    destino.parent.mkdir(parents=True)
    destino.write_bytes(b"basura")
    filas, errores = ingerir(tmp_path, onto)
    assert filas == []
    assert any("roto.jpg" in e for e in errores)


def test_detecta_colision_con_entrenamiento():
    campo = [{"archivo": "c1.jpg", "hash": "ffff0000ffff0000"}]
    train = [{"archivo": "t1.jpg", "hash": "ffff0000ffff0000"}]
    colisiones = detectar_colisiones(campo, train)
    assert len(colisiones) == 1
    assert "c1.jpg" in colisiones[0]


def test_sin_colision_cuando_las_imagenes_difieren():
    campo = [{"archivo": "c1.jpg", "hash": "ffff0000ffff0000"}]
    train = [{"archivo": "t1.jpg", "hash": "0000ffff0000ffff"}]
    assert detectar_colisiones(campo, train) == []
