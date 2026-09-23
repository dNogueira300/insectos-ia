"""Servicio de inferencia sobre ONNX.

Sin PyTorch: solo onnxruntime, numpy y Pillow. El enmascaramiento jerárquico
se reutiliza tal cual de `pipeline.inferencia`, así el backend y la
evaluación toman exactamente la misma decisión.
"""
from __future__ import annotations

from pathlib import Path

import onnxruntime as ort

from backend.preproceso import desde_bytes
from pipeline.etiquetas import cargar_espacio
from pipeline.inferencia import UMBRAL_FAMILIA, Prediccion, predecir


class ErrorImagen(ValueError):
    """El archivo recibido no es una imagen que se pueda procesar."""


class ServicioInsectos:
    """Carga el modelo una vez y responde predicciones jerárquicas."""

    def __init__(
        self,
        ruta_onnx: Path,
        ruta_etiquetas: Path,
        *,
        umbral: float = UMBRAL_FAMILIA,
    ) -> None:
        self.ruta_onnx = Path(ruta_onnx)
        self.espacio = cargar_espacio(Path(ruta_etiquetas))
        self.umbral = umbral
        self.sesion = ort.InferenceSession(
            str(self.ruta_onnx), providers=["CPUExecutionProvider"]
        )
        entrada = self.sesion.get_inputs()[0]
        self.nombre_entrada = entrada.name
        # El exportador deja libre solo el lote: alto y ancho vienen fijos en el
        # ONNX. Leerlos de ahí impide preparar la foto a otro tamaño que el de
        # entrenamiento (la v4 usa 288, no 224).
        self.lado = int(entrada.shape[2])

    def predecir_bytes(self, datos: bytes) -> Prediccion:
        try:
            tensor = desde_bytes(datos, lado=self.lado)
        except ValueError as error:
            raise ErrorImagen(str(error)) from error

        logits_orden, logits_familia = self.sesion.run(None, {self.nombre_entrada: tensor})
        return predecir(
            logits_orden[0], logits_familia[0], self.espacio, umbral=self.umbral
        )

    def clases(self) -> dict:
        return {
            "ordenes": list(self.espacio.ordenes),
            "familias": list(self.espacio.familias),
            "matriz": [list(r) for r in self.espacio.matriz],
        }

    def version(self) -> dict:
        return {
            "modelo": self.ruta_onnx.name,
            "n_ordenes": len(self.espacio.ordenes),
            "n_familias": len(self.espacio.familias),
            "umbral_familia": self.umbral,
            "lado": self.lado,
        }
