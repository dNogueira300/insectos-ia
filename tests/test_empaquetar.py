import csv
import hashlib
import zipfile
from pathlib import Path

import pytest

from pipeline.empaquetar import ErrorEmpaquetado, empaquetar


def _preparar(tmp_path: Path) -> dict:
    curado = tmp_path / "curado"
    splits = tmp_path / "splits"
    splits.mkdir()
    for archivo in ("A/X/1.jpg", "A/X/2.jpg", "B/_sin_familia/3.jpg", "A/X/huerfana.jpg"):
        ruta = curado / archivo
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(b"jpg de " + archivo.encode())
    reparto = {"train": ["A/X/1.jpg", "B/_sin_familia/3.jpg"], "val": ["A/X/2.jpg"], "test": []}
    for split, archivos in reparto.items():
        with (splits / f"{split}.csv").open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=["archivo", "orden", "familia"])
            escritor.writeheader()
            escritor.writerows({"archivo": a, "orden": a[0], "familia": ""} for a in archivos)
    ontologia = tmp_path / "clases.yaml"
    ontologia.write_text("version: 1\n", encoding="utf-8")
    return {"ruta_splits": splits, "raiz_imagenes": curado, "ruta_ontologia": ontologia}


def test_el_paquete_lleva_splits_ontologia_y_solo_las_imagenes_referenciadas(tmp_path: Path):
    destino = tmp_path / "paquete" / "dataset.zip"
    resumen = empaquetar(destino=destino, **_preparar(tmp_path))
    with zipfile.ZipFile(destino) as z:
        nombres = set(z.namelist())
    assert nombres == {
        "splits/train.csv",
        "splits/val.csv",
        "splits/test.csv",
        "ontologia/clases.yaml",
        "curado/A/X/1.jpg",
        "curado/A/X/2.jpg",
        "curado/B/_sin_familia/3.jpg",
    }
    assert resumen["imagenes"] == 3


def test_el_contenido_de_las_imagenes_se_conserva(tmp_path: Path):
    destino = tmp_path / "dataset.zip"
    empaquetar(destino=destino, **_preparar(tmp_path))
    with zipfile.ZipFile(destino) as z:
        assert z.read("curado/A/X/1.jpg") == b"jpg de A/X/1.jpg"


def test_una_imagen_referenciada_que_falta_detiene_sin_dejar_paquete(tmp_path: Path):
    """Un zip incompleto se descubriría recién en Colab, a mitad de una época."""
    datos = _preparar(tmp_path)
    (datos["raiz_imagenes"] / "A/X/2.jpg").unlink()
    destino = tmp_path / "dataset.zip"
    with pytest.raises(ErrorEmpaquetado, match="A/X/2.jpg"):
        empaquetar(destino=destino, **datos)
    assert not destino.exists()
    assert list(tmp_path.glob("*.tmp")) == []


def test_la_huella_sha256_corresponde_al_paquete(tmp_path: Path):
    destino = tmp_path / "dataset.zip"
    resumen = empaquetar(destino=destino, **_preparar(tmp_path))
    real = hashlib.sha256(destino.read_bytes()).hexdigest()
    assert resumen["sha256"] == real
    assert destino.with_suffix(".sha256").read_text(encoding="utf-8").split()[0] == real
