"""Enmascaramiento jerárquico y decisión final. Sin torch, solo numpy.

Es lo único que el backend necesita además de onnxruntime: mantenerlo libre
de torch evita arrastrar cientos de megabytes al despliegue.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from pipeline.etiquetas import EspacioEtiquetas

# Por debajo de esta confianza el sistema declara la familia incierta y
# muestra el top-3 en vez de afirmar una respuesta.
UMBRAL_FAMILIA = 0.45


@dataclass(frozen=True)
class Prediccion:
    orden: str
    confianza_orden: float
    familia: str
    confianza_familia: float
    familia_incierta: bool
    top_familias: tuple[tuple[str, float], ...]


def softmax(x: np.ndarray) -> np.ndarray:
    estable = np.exp(x - np.max(x))
    return estable / estable.sum()


def enmascarar(probs_familia: np.ndarray, indice_orden: int, matriz: np.ndarray) -> np.ndarray:
    """Anula las familias que no pertenecen al orden predicho y renormaliza."""
    mascara = matriz[:, indice_orden]
    filtradas = np.where(mascara, probs_familia, 0.0)
    total = filtradas.sum()
    return filtradas / total if total > 0 else filtradas


def predecir(
    logits_orden: np.ndarray,
    logits_familia: np.ndarray,
    espacio: EspacioEtiquetas,
    *,
    umbral: float = UMBRAL_FAMILIA,
    top: int = 3,
) -> Prediccion:
    """Convierte los logits crudos del modelo en una respuesta jerárquica."""
    probs_orden = softmax(np.asarray(logits_orden, dtype=np.float64))
    indice_orden = int(np.argmax(probs_orden))

    matriz = np.array(espacio.matriz, dtype=bool)
    probs_familia = enmascarar(
        softmax(np.asarray(logits_familia, dtype=np.float64)), indice_orden, matriz
    )

    candidatas = np.flatnonzero(matriz[:, indice_orden])
    if candidatas.size == 0:
        # El orden no tiene ninguna familia entrenada: se responde solo el orden.
        return Prediccion(
            orden=espacio.ordenes[indice_orden],
            confianza_orden=float(probs_orden[indice_orden]),
            familia="",
            confianza_familia=0.0,
            familia_incierta=True,
            top_familias=(),
        )

    ordenadas = sorted(candidatas, key=lambda i: float(probs_familia[i]), reverse=True)
    mejor = ordenadas[0]
    confianza = float(probs_familia[mejor])

    return Prediccion(
        orden=espacio.ordenes[indice_orden],
        confianza_orden=float(probs_orden[indice_orden]),
        familia=espacio.familias[mejor],
        confianza_familia=confianza,
        familia_incierta=confianza < umbral,
        top_familias=tuple(
            (espacio.familias[i], float(probs_familia[i])) for i in ordenadas[:top]
        ),
    )
