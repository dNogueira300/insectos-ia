from pathlib import Path

import numpy as np
import torch
from PIL import Image

from pipeline.datos_torch import (
    LADO,
    DatasetInsectos,
    leer_split,
    pesos_de_familia,
    transformaciones_entrenamiento,
    transformaciones_evaluacion,
)
from pipeline.etiquetas import SIN_FAMILIA_IDX, EspacioEtiquetas

ESPACIO = EspacioEtiquetas(
    ordenes=("OrdenA", "OrdenB"),
    familias=("FamX", "FamY"),
    matriz=((True, False), (False, True)),
)


def escribir_imagen(raiz: Path, relativo: str, semilla: int = 1, lado: int = 300):
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    destino = raiz / relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(base).resize((lado, lado), Image.BICUBIC).save(destino, "JPEG")


def fila(archivo, orden, familia):
    return {"archivo": archivo, "orden": orden, "familia": familia}


def test_dataset_devuelve_tensor_e_indices(tmp_path: Path):
    escribir_imagen(tmp_path, "a.jpg")
    conjunto = DatasetInsectos(
        [fila("a.jpg", "OrdenA", "FamX")], tmp_path, ESPACIO, transformaciones_evaluacion()
    )
    tensor, idx_orden, idx_familia = conjunto[0]
    assert tensor.shape == (3, LADO, LADO)
    assert idx_orden == 0
    assert idx_familia == 0


def test_familia_vacia_devuelve_indice_de_ignorar(tmp_path: Path):
    escribir_imagen(tmp_path, "a.jpg")
    conjunto = DatasetInsectos(
        [fila("a.jpg", "OrdenB", "")], tmp_path, ESPACIO, transformaciones_evaluacion()
    )
    _, idx_orden, idx_familia = conjunto[0]
    assert idx_orden == 1
    assert idx_familia == SIN_FAMILIA_IDX


def test_longitud_del_dataset(tmp_path: Path):
    for nombre in ("a.jpg", "b.jpg", "c.jpg"):
        escribir_imagen(tmp_path, nombre)
    filas = [fila(n, "OrdenA", "FamX") for n in ("a.jpg", "b.jpg", "c.jpg")]
    assert len(DatasetInsectos(filas, tmp_path, ESPACIO, transformaciones_evaluacion())) == 3


def test_transformacion_de_entrenamiento_tambien_da_224(tmp_path: Path):
    escribir_imagen(tmp_path, "a.jpg", lado=500)
    conjunto = DatasetInsectos(
        [fila("a.jpg", "OrdenA", "FamX")], tmp_path, ESPACIO, transformaciones_entrenamiento()
    )
    tensor, _, _ = conjunto[0]
    assert tensor.shape == (3, LADO, LADO)


def test_imagen_en_escala_de_grises_se_convierte_a_tres_canales(tmp_path: Path):
    destino = tmp_path / "gris.jpg"
    Image.new("L", (300, 300), color=128).save(destino)
    conjunto = DatasetInsectos(
        [fila("gris.jpg", "OrdenA", "FamX")], tmp_path, ESPACIO, transformaciones_evaluacion()
    )
    tensor, _, _ = conjunto[0]
    assert tensor.shape[0] == 3


def test_normalizacion_deja_valores_fuera_de_cero_uno(tmp_path: Path):
    escribir_imagen(tmp_path, "a.jpg")
    conjunto = DatasetInsectos(
        [fila("a.jpg", "OrdenA", "FamX")], tmp_path, ESPACIO, transformaciones_evaluacion()
    )
    tensor, _, _ = conjunto[0]
    assert tensor.min() < 0.0  # si no, falta Normalize


def test_pesos_de_familia_favorecen_a_la_rara():
    filas = [fila("x", "OrdenA", "FamX")] * 100 + [fila("y", "OrdenB", "FamY")] * 4
    pesos = pesos_de_familia(filas, ESPACIO)
    assert pesos.shape == (2,)
    assert pesos[1] > pesos[0]


def test_pesos_de_familia_estan_acotados():
    filas = [fila("x", "OrdenA", "FamX")] * 10000 + [fila("y", "OrdenB", "FamY")]
    pesos = pesos_de_familia(filas, ESPACIO)
    assert torch.all(pesos >= 0.2) and torch.all(pesos <= 5.0)


def test_pesos_ignoran_filas_sin_familia():
    filas = [fila("x", "OrdenA", "FamX")] * 10 + [fila("z", "OrdenA", "")] * 500
    pesos = pesos_de_familia(filas, ESPACIO)
    assert torch.isfinite(pesos).all()


def test_leer_split_devuelve_diccionarios(tmp_path: Path):
    csv = tmp_path / "train.csv"
    csv.write_text("archivo,orden,familia\na.jpg,OrdenA,FamX\n", encoding="utf-8")
    filas = leer_split(csv)
    assert filas == [{"archivo": "a.jpg", "orden": "OrdenA", "familia": "FamX"}]
