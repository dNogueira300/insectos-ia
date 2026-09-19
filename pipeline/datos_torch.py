"""Dataset, transformaciones y cargadores para el entrenamiento."""
from __future__ import annotations

import csv
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from pipeline.etiquetas import SIN_FAMILIA_IDX, EspacioEtiquetas

LADO = 224
MEDIA = (0.485, 0.456, 0.406)      # estadísticas de ImageNet: el backbone las espera
DESVIACION = (0.229, 0.224, 0.225)

PESO_MINIMO = 0.2
PESO_MAXIMO = 5.0


def transformaciones_entrenamiento() -> transforms.Compose:
    """Aumentos suaves: el insecto puede aparecer en cualquier escala y encuadre."""
    return transforms.Compose(
        [
            transforms.RandomResizedCrop(LADO, scale=(0.6, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(MEDIA, DESVIACION),
        ]
    )


def transformaciones_evaluacion() -> transforms.Compose:
    """Determinista. El Plan 03 debe replicarla exactamente en numpy."""
    return transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(LADO),
            transforms.ToTensor(),
            transforms.Normalize(MEDIA, DESVIACION),
        ]
    )


class DatasetInsectos(Dataset):
    """Cada elemento es (imagen, índice de orden, índice de familia)."""

    def __init__(
        self,
        filas: list[dict],
        raiz: Path,
        espacio: EspacioEtiquetas,
        transformacion,
    ) -> None:
        self.filas = filas
        self.raiz = Path(raiz)
        self.espacio = espacio
        self.transformacion = transformacion

    def __len__(self) -> int:
        return len(self.filas)

    def __getitem__(self, indice: int):
        fila = self.filas[indice]
        with Image.open(self.raiz / fila["archivo"]) as img:
            imagen = self.transformacion(img.convert("RGB"))
        return (
            imagen,
            self.espacio.indice_orden(fila["orden"]),
            self.espacio.indice_familia(fila["familia"]),
        )


def leer_split(ruta_csv: Path) -> list[dict]:
    with Path(ruta_csv).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def pesos_de_familia(filas: list[dict], espacio: EspacioEtiquetas) -> torch.Tensor:
    """Pesos por clase inversos a la raíz de la frecuencia, acotados.

    La raíz amortigua: pesar por el inverso puro hace que una familia con 150
    imágenes domine el gradiente frente a una con 3000 y desestabilice todo.
    """
    conteo = torch.zeros(len(espacio.familias))
    for fila in filas:
        if fila["familia"]:
            conteo[espacio.indice_familia(fila["familia"])] += 1

    conteo = torch.clamp(conteo, min=1.0)
    pesos = conteo.sum().sqrt() / conteo.sqrt()
    pesos = pesos / pesos.mean()
    return torch.clamp(pesos, PESO_MINIMO, PESO_MAXIMO)


def cargadores(
    filas_train: list[dict],
    filas_val: list[dict],
    raiz: Path,
    espacio: EspacioEtiquetas,
    *,
    lote: int = 32,
    trabajadores: int = 4,
) -> tuple[DataLoader, DataLoader]:
    entrenamiento = DatasetInsectos(filas_train, raiz, espacio, transformaciones_entrenamiento())
    validacion = DatasetInsectos(filas_val, raiz, espacio, transformaciones_evaluacion())
    return (
        DataLoader(
            entrenamiento,
            batch_size=lote,
            shuffle=True,
            num_workers=trabajadores,
            pin_memory=torch.cuda.is_available(),
            drop_last=True,
        ),
        DataLoader(
            validacion,
            batch_size=lote,
            shuffle=False,
            num_workers=trabajadores,
            pin_memory=torch.cuda.is_available(),
        ),
    )
