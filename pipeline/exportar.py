"""Export a ONNX y verificación de que el artefacto desplegado piensa igual."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch

from pipeline.etiquetas import cargar_espacio
from pipeline.modelo import BACKBONE_POR_DEFECTO, ModeloJerarquico

NOMBRE_ENTRADA = "imagen"
NOMBRES_SALIDA = ["logits_orden", "logits_familia"]


def exportar_onnx(modelo: torch.nn.Module, ruta: Path, *, lado: int = 224) -> None:
    """Exporta con eje de lote dinámico. El modelo queda en modo evaluación."""
    modelo.eval()
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        modelo,
        torch.randn(1, 3, lado, lado),
        str(ruta),
        input_names=[NOMBRE_ENTRADA],
        output_names=NOMBRES_SALIDA,
        dynamic_axes={
            NOMBRE_ENTRADA: {0: "lote"},
            NOMBRES_SALIDA[0]: {0: "lote"},
            NOMBRES_SALIDA[1]: {0: "lote"},
        },
        opset_version=17,
        # Exportador clásico (TorchScript), explícito. Desde PyTorch 2.9 el
        # predeterminado es el de dynamo, que exige onnxscript y declara los
        # ejes dinámicos con otra API (`dynamic_shapes`). Probado el
        # 2026-09-19 con torch 2.14: ambos pasan la paridad, pero dynamo tarda
        # de 8 a 21 s por export frente a menos de 3 s. El clásico está
        # marcado como obsoleto: si una versión futura de torch lo retira,
        # migrar a dynamo=True con dynamic_shapes y volver a verificar la
        # paridad.
        dynamo=False,
    )


def verificar_paridad(
    modelo: torch.nn.Module, ruta_onnx: Path, *, tolerancia: float = 1e-4, lado: int = 224
) -> dict:
    """Compara las salidas de PyTorch y ONNX sobre la misma entrada."""
    import onnxruntime as ort

    modelo.eval()
    entrada = torch.randn(2, 3, lado, lado)

    with torch.no_grad():
        orden_torch, familia_torch = modelo(entrada)

    sesion = ort.InferenceSession(str(ruta_onnx), providers=["CPUExecutionProvider"])
    orden_onnx, familia_onnx = sesion.run(None, {NOMBRE_ENTRADA: entrada.numpy()})

    diferencia = max(
        float(np.abs(orden_torch.numpy() - orden_onnx).max()),
        float(np.abs(familia_torch.numpy() - familia_onnx).max()),
    )
    return {"coincide": diferencia < tolerancia, "diferencia_maxima": diferencia}


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta el modelo entrenado a ONNX")
    parser.add_argument("--pesos", default="modelo/mejor.pth")
    parser.add_argument("--etiquetas", default="modelo/etiquetas.json")
    parser.add_argument("--salida", default="modelo/insectos.onnx")
    parser.add_argument("--backbone", default=BACKBONE_POR_DEFECTO)
    args = parser.parse_args()

    espacio = cargar_espacio(Path(args.etiquetas))
    modelo = ModeloJerarquico(
        len(espacio.ordenes), len(espacio.familias), backbone=args.backbone, preentrenado=False
    )
    modelo.load_state_dict(torch.load(args.pesos, map_location="cpu"))

    exportar_onnx(modelo, Path(args.salida))
    resultado = verificar_paridad(modelo, Path(args.salida))
    print(f"Diferencia máxima torch vs onnx: {resultado['diferencia_maxima']:.2e}")
    if not resultado["coincide"]:
        raise SystemExit("El ONNX no coincide con PyTorch: NO desplegar este artefacto.")
    print(f"Exportado y verificado: {args.salida}")


if __name__ == "__main__":
    main()
