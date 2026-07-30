import csv
from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.campo import (
    SALIDA_COLISIONES,
    SALIDA_FALTA_REFERENCIA,
    SALIDA_RECHAZOS,
    SPLITS_DE_REFERENCIA,
    detectar_colisiones,
    ingerir,
    main,
)
from pipeline.curacion import COLUMNAS_CURADO
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


# --- Verificación anti-fuga desde la línea de comandos -----------------------


def escribir_split(directorio: Path, split: str, hashes=()) -> None:
    directorio.mkdir(parents=True, exist_ok=True)
    with (directorio / f"{split}.csv").open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
        escritor.writeheader()
        for i, huella in enumerate(hashes):
            fila = {c: "" for c in COLUMNAS_CURADO}
            fila.update(archivo=f"{split}/img{i}.jpg", hash=huella)
            escritor.writerow(fila)


def preparar(tmp_path: Path, ruta_ontologia: Path, *, splits=SPLITS_DE_REFERENCIA):
    """Monta un caso completo y devuelve (argv, ruta de salida, raíz de campo)."""
    raiz_campo = tmp_path / "campo_crudo"
    raiz_campo.mkdir(parents=True, exist_ok=True)
    directorio_splits = tmp_path / "splits"
    for split in splits:
        escribir_split(directorio_splits, split)
    salida = tmp_path / "salida" / "campo.csv"
    argv = [
        "--ontologia", str(ruta_ontologia),
        "--campo", str(raiz_campo),
        "--splits", str(directorio_splits),
        "--salida", str(salida),
    ]
    return argv, salida, raiz_campo, directorio_splits


def test_main_falla_si_falta_un_archivo_de_referencia(tmp_path: Path, ruta_ontologia: Path, capsys):
    """La verificación anti-fuga no puede fallar en abierto.

    Con `--splits` apuntando a un directorio incompleto —un typo, o correr
    `campo.py` antes que `splits.py`— el programa no puede seguir, informar
    éxito y escribir `campo.csv`: esa verificación es el único guardián del
    conjunto de campo.
    """
    argv, salida, raiz_campo, _ = preparar(tmp_path, ruta_ontologia, splits=("train", "val"))
    escribir_imagen(raiz_campo, "Coleoptera/Curculionidae/foto1.jpg", 11)

    codigo = main(argv)

    assert codigo == SALIDA_FALTA_REFERENCIA
    assert codigo != 0
    assert not salida.exists(), "no debe escribirse campo.csv sin poder verificar la fuga"
    assert "test.csv" in capsys.readouterr().out


def test_main_falla_si_no_existe_el_directorio_de_splits(tmp_path: Path, ruta_ontologia: Path):
    argv, salida, raiz_campo, directorio = preparar(tmp_path, ruta_ontologia, splits=())
    escribir_imagen(raiz_campo, "Coleoptera/Curculionidae/foto1.jpg", 12)

    assert main(argv) == SALIDA_FALTA_REFERENCIA
    assert not salida.exists()


def test_main_exitoso_devuelve_cero_y_escribe_campo_csv(tmp_path: Path, ruta_ontologia: Path):
    argv, salida, raiz_campo, _ = preparar(tmp_path, ruta_ontologia)
    escribir_imagen(raiz_campo, "Coleoptera/Curculionidae/foto1.jpg", 13)

    assert main(argv) == 0
    assert salida.exists()
    with salida.open(encoding="utf-8", newline="") as f:
        assert len(list(csv.DictReader(f))) == 1


def test_main_detecta_colision_contra_validacion(tmp_path: Path, ruta_ontologia: Path, capsys):
    """El diseño (§7) prohíbe que una foto de campo esté en entrenamiento **ni
    en validación**. Comprobar solo contra train deja pasar la mitad del riesgo."""
    argv, salida, raiz_campo, directorio = preparar(tmp_path, ruta_ontologia)
    escribir_imagen(raiz_campo, "Coleoptera/Curculionidae/foto1.jpg", 14)
    filas, _ = ingerir(raiz_campo, cargar_ontologia(ruta_ontologia))
    escribir_split(directorio, "val", hashes=[filas[0]["hash"]])

    codigo = main(argv)

    assert codigo == SALIDA_COLISIONES
    salida_texto = capsys.readouterr().out
    assert "COLISIÓN" in salida_texto
    assert "val" in salida_texto


def test_main_detecta_colision_contra_test(tmp_path: Path, ruta_ontologia: Path, capsys):
    argv, salida, raiz_campo, directorio = preparar(tmp_path, ruta_ontologia)
    escribir_imagen(raiz_campo, "Coleoptera/Curculionidae/foto1.jpg", 15)
    filas, _ = ingerir(raiz_campo, cargar_ontologia(ruta_ontologia))
    escribir_split(directorio, "test", hashes=[filas[0]["hash"]])

    assert main(argv) == SALIDA_COLISIONES
    assert "test" in capsys.readouterr().out


def test_main_devuelve_codigo_de_error_si_hubo_archivos_rechazados(
    tmp_path: Path, ruta_ontologia: Path
):
    """Un archivo rechazado es una foto que la Facultad entregó y no llegó al
    conjunto de campo: debe notarse en el código de salida para poder
    encadenar `campo.py` en un script."""
    argv, salida, raiz_campo, _ = preparar(tmp_path, ruta_ontologia)
    escribir_imagen(raiz_campo, "Coleoptera/Curculionidae/foto1.jpg", 16)
    destino = raiz_campo / "Coleoptera" / "Curculionidae" / "foto2.heic"
    destino.write_bytes(b"formato no soportado")

    codigo = main(argv)

    assert codigo == SALIDA_RECHAZOS
    assert salida.exists(), "las fotos válidas sí se escriben; solo cambia el código de salida"
