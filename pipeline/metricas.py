"""Métricas de evaluación.

La exactitud global engaña con clases desbalanceadas: un modelo que ignora
las familias raras puede lucir bien y ser inservible. La métrica de
aceptación del proyecto es el macro-F1.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np


def matriz_confusion(y_true: list[int], y_pred: list[int], n_clases: int) -> np.ndarray:
    matriz = np.zeros((n_clases, n_clases), dtype=np.int64)
    for verdadero, predicho in zip(y_true, y_pred):
        matriz[verdadero, predicho] += 1
    return matriz


def f1_por_clase(matriz: np.ndarray) -> np.ndarray:
    """F1 de cada clase. Devuelve 0 —no NaN— para clases sin datos."""
    verdaderos = np.diag(matriz).astype(np.float64)
    predichos = matriz.sum(axis=0).astype(np.float64)
    reales = matriz.sum(axis=1).astype(np.float64)

    with np.errstate(divide="ignore", invalid="ignore"):
        precision = np.where(predichos > 0, verdaderos / predichos, 0.0)
        exhaustividad = np.where(reales > 0, verdaderos / reales, 0.0)
        suma = precision + exhaustividad
        f1 = np.where(suma > 0, 2 * precision * exhaustividad / suma, 0.0)
    return f1


def macro_f1(y_true: list[int], y_pred: list[int], n_clases: int) -> float:
    return float(f1_por_clase(matriz_confusion(y_true, y_pred, n_clases)).mean())


def exactitud(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true:
        return 0.0
    aciertos = sum(1 for v, p in zip(y_true, y_pred) if v == p)
    return aciertos / len(y_true)


def exactitud_jerarquica(
    orden_true: list[int], orden_pred: list[int], fam_true: list[int], fam_pred: list[int]
) -> float:
    """Fracción de casos con orden Y familia correctos."""
    if not orden_true:
        return 0.0
    aciertos = sum(
        1
        for ov, op, fv, fp in zip(orden_true, orden_pred, fam_true, fam_pred)
        if ov == op and fv == fp
    )
    return aciertos / len(orden_true)


def top_k(probs: np.ndarray, y_true: list[int], k: int = 3) -> float:
    """Fracción de casos donde la clase correcta está entre las k más probables."""
    if len(y_true) == 0:
        return 0.0
    mejores = np.argsort(-probs, axis=1)[:, :k]
    aciertos = sum(1 for fila, verdadero in zip(mejores, y_true) if verdadero in fila)
    return aciertos / len(y_true)


def cobertura_y_exactitud(
    confianzas: list[float], aciertos: list[bool], umbral: float
) -> tuple[float, float]:
    """Qué fracción responde el sistema con confianza >= umbral, y con qué acierto."""
    if not confianzas:
        return 0.0, 0.0
    seleccionados = [a for c, a in zip(confianzas, aciertos) if c >= umbral]
    cobertura = len(seleccionados) / len(confianzas)
    if not seleccionados:
        return 0.0, 0.0
    return cobertura, sum(seleccionados) / len(seleccionados)


def tabla_por_clase(matriz: np.ndarray, nombres: list[str]) -> str:
    """Tabla markdown con F1 y soporte de cada clase. Ninguna se esconde."""
    f1 = f1_por_clase(matriz)
    soporte = matriz.sum(axis=1)
    lineas = ["| Clase | Soporte | F1 |", "| --- | ---: | ---: |"]
    for indice, nombre in enumerate(nombres):
        lineas.append(f"| {nombre} | {int(soporte[indice])} | {f1[indice]:.3f} |")
    return "\n".join(lineas)


def guardar_matriz_png(matriz: np.ndarray, nombres: list[str], ruta: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    normalizada = matriz.astype(np.float64)
    filas = normalizada.sum(axis=1, keepdims=True)
    normalizada = np.divide(normalizada, filas, out=np.zeros_like(normalizada), where=filas > 0)

    lado = max(6, len(nombres) * 0.45)
    figura, eje = plt.subplots(figsize=(lado, lado))
    eje.imshow(normalizada, cmap="Blues", vmin=0, vmax=1)
    eje.set_xticks(range(len(nombres)), nombres, rotation=90, fontsize=7)
    eje.set_yticks(range(len(nombres)), nombres, fontsize=7)
    eje.set_xlabel("predicho")
    eje.set_ylabel("real")
    figura.tight_layout()
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(ruta, dpi=150)
    plt.close(figura)
