from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.campo import detectar_colisiones, ingerir
from pipeline.ontologia import cargar_ontologia


def escribir_imagen(raiz: Path, relativo: str, semilla: int, lado: int = 300, formato: str = "JPEG"):
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    destino = raiz / relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(base).resize((lado, lado), Image.BICUBIC).save(destino, formato, quality=90)


def test_ingerir_lee_orden_y_familia_de_la_ruta(tmp_path: Path, ruta_ontologia: Path):
    # La raíz de campo vive en su propia subcarpeta, separada de donde el
    # fixture `ruta_ontologia` escribe clases.yaml: si compartieran tmp_path,
    # `ingerir` (que ahora reporta cualquier archivo que no encaje, en vez de
    # ignorarlo en silencio) marcaría clases.yaml como un archivo fuera de la
    # estructura esperada. No es una entrega de la Facultad; no debe mezclarse
    # con la carpeta que sí se recorre.
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Coleoptera/Curculionidae/foto1.jpg", 1)
    filas, errores = ingerir(raiz, onto)
    assert errores == []
    assert filas[0]["orden"] == "Coleoptera"
    assert filas[0]["familia"] == "Curculionidae"
    assert filas[0]["fuente"] == "campo"
    assert filas[0]["hash"]


def test_ingerir_acepta_carpeta_sin_familia(tmp_path: Path, ruta_ontologia: Path):
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Coleoptera/_sin_familia/foto1.jpg", 2)
    filas, errores = ingerir(raiz, onto)
    assert errores == []
    assert filas[0]["familia"] == ""


def test_ingerir_reporta_orden_desconocido(tmp_path: Path, ruta_ontologia: Path):
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Inventado/FamY/foto1.jpg", 3)
    filas, errores = ingerir(raiz, onto)
    assert filas == []
    assert any("Inventado" in e for e in errores)


def test_ingerir_reporta_familia_de_otro_orden(tmp_path: Path, ruta_ontologia: Path):
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Odonata/Curculionidae/foto1.jpg", 4)
    filas, errores = ingerir(raiz, onto)
    assert filas == []
    assert any("Curculionidae" in e for e in errores)


def test_ingerir_reporta_archivo_ilegible(tmp_path: Path, ruta_ontologia: Path):
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    destino = raiz / "Coleoptera" / "Curculionidae" / "roto.jpg"
    destino.parent.mkdir(parents=True)
    destino.write_bytes(b"basura")
    filas, errores = ingerir(raiz, onto)
    assert filas == []
    assert any("roto.jpg" in e for e in errores)


def test_ingerir_reporta_extension_no_reconocida(tmp_path: Path, ruta_ontologia: Path):
    """Una extensión que no se reconoce debe reportarse, no desaparecer.

    Fotos de campo tomadas con celular llegan a menudo en formatos como
    .heic (iPhone): si el archivo se descarta en silencio, alguien puede
    entregar 200 fotos y ver un conteo final que no las incluye todas, sin
    ninguna pista de que faltan.
    """
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    destino = raiz / "Coleoptera" / "Curculionidae" / "foto1.heic"
    destino.parent.mkdir(parents=True)
    destino.write_bytes(b"contenido de una foto heic simulada, no se llega a abrir")
    filas, errores = ingerir(raiz, onto)
    assert filas == []
    assert any("foto1.heic" in e and ".heic" in e for e in errores)


def test_ingerir_ignora_archivos_de_metadatos_del_sistema(tmp_path: Path, ruta_ontologia: Path):
    """Thumbs.db, .DS_Store y demás basura de sistema no son entregas: se
    ignoran sin generar error, a diferencia de un archivo con extensión
    desconocida que sí fue puesto ahí por una persona."""
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Coleoptera/Curculionidae/foto1.jpg", 6)
    carpeta = raiz / "Coleoptera" / "Curculionidae"
    (carpeta / "Thumbs.db").write_bytes(b"basura de windows")
    (carpeta / ".DS_Store").write_bytes(b"basura de macos")
    filas, errores = ingerir(raiz, onto)
    assert errores == []
    assert len(filas) == 1


def test_ingerir_acepta_webp(tmp_path: Path, ruta_ontologia: Path):
    """WEBP se acepta porque Pillow lo decodifica de forma nativa."""
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Coleoptera/Curculionidae/foto1.webp", 7, formato="WEBP")
    filas, errores = ingerir(raiz, onto)
    assert errores == []
    assert filas[0]["hash"]


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
