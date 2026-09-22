"""Export a ONNX y verificación de que el artefacto desplegado piensa igual."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from pipeline.corrida import opcion_de_corrida
from pipeline.datos_torch import LADO
from pipeline.etiquetas import cargar_espacio
from pipeline.modelo import BACKBONE_POR_DEFECTO, ModeloJerarquico

NOMBRE_ENTRADA = "imagen"
NOMBRES_SALIDA = ["logits_orden", "logits_familia"]


def exportar_onnx(modelo: torch.nn.Module, ruta: Path, *, lado: int = LADO) -> None:
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


def _softmax(logits: np.ndarray) -> np.ndarray:
    desplazados = logits - logits.max(axis=1, keepdims=True)
    exponentes = np.exp(desplazados)
    return exponentes / exponentes.sum(axis=1, keepdims=True)


def muestra_real(
    ruta_csv: Path, raiz_imagenes: Path, *, n: int = 32, lado: int = LADO
) -> torch.Tensor:
    """Las primeras `n` fotos de un split, con la transformación de evaluación."""
    from pipeline.datos_torch import leer_split, transformaciones_evaluacion

    transformar = transformaciones_evaluacion(lado)
    lote = []
    for fila in leer_split(ruta_csv)[:n]:
        with Image.open(Path(raiz_imagenes) / fila["archivo"]) as img:
            lote.append(transformar(img.convert("RGB")))
    return torch.stack(lote)


def verificar_paridad(
    modelo: torch.nn.Module,
    ruta_onnx: Path,
    *,
    tolerancia: float = 1e-4,
    lado: int = LADO,
    entrada: torch.Tensor | None = None,
) -> dict:
    """Compara PyTorch y ONNX en lo que usa el sistema: probabilidades y clase.

    No se compara la diferencia absoluta de logits contra una tolerancia fija.
    Con pesos entrenados y una entrada de ruido, los logits llegan a ~500, y el
    redondeo normal de float32 acumulado en decenas de capas da diferencias
    absolutas de ~1 aunque el ONNX sea fiel. Eso pasó en la prueba de humo del
    2026-09-19: sobre 64 imágenes reales, las probabilidades diferían en 1e-7 y
    la clase elegida coincidía en el 100% de los casos. Las probabilidades no
    dependen de la escala de los logits, y un ONNX realmente distinto sí las
    cambia. La diferencia de logits se informa igual, como diagnóstico.

    `entrada` debería ser un lote de fotos reales (ver `muestra_real`). Con
    ruido gaussiano, una red entrenada produce activaciones extremas que
    ninguna foto genera, y en ese régimen torch y ONNX sí se separan algo
    (2.8e-4 en probabilidades en la prueba de humo), aunque sea irrelevante
    para el despliegue. El ruido queda solo como último recurso.
    """
    import onnxruntime as ort

    modelo.eval()
    if entrada is None:
        entrada = torch.randn(2, 3, lado, lado)

    with torch.no_grad():
        salidas_torch = [s.numpy() for s in modelo(entrada)]

    sesion = ort.InferenceSession(str(ruta_onnx), providers=["CPUExecutionProvider"])
    salidas_onnx = sesion.run(None, {NOMBRE_ENTRADA: entrada.numpy()})

    diferencia_probs = max(
        float(np.abs(_softmax(t) - _softmax(o)).max())
        for t, o in zip(salidas_torch, salidas_onnx, strict=True)
    )
    diferencia_logits = max(
        float(np.abs(t - o).max()) for t, o in zip(salidas_torch, salidas_onnx, strict=True)
    )
    misma_clase = all(
        bool((t.argmax(axis=1) == o.argmax(axis=1)).all())
        for t, o in zip(salidas_torch, salidas_onnx, strict=True)
    )
    return {
        "coincide": diferencia_probs < tolerancia and misma_clase,
        "diferencia_maxima": diferencia_probs,
        "diferencia_logits": diferencia_logits,
        "misma_clase": misma_clase,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta el modelo entrenado a ONNX")
    parser.add_argument("--pesos", default="modelo/mejor.pth")
    parser.add_argument("--etiquetas", default="modelo/etiquetas.json")
    parser.add_argument("--salida", default="modelo/insectos.onnx")
    parser.add_argument("--backbone", default=None)
    parser.add_argument("--lado", type=int, default=None)
    parser.add_argument(
        "--muestra", default="datos/splits/val.csv",
        help="split con fotos reales para verificar la paridad",
    )
    parser.add_argument("--imagenes", default="datos/curado")
    args = parser.parse_args()

    pesos = Path(args.pesos)
    backbone = opcion_de_corrida(pesos, "backbone", pedido=args.backbone, defecto=BACKBONE_POR_DEFECTO)
    lado = opcion_de_corrida(pesos, "lado", pedido=args.lado, defecto=LADO)
    print(f"Backbone {backbone} a {lado} px (según la corrida)")

    espacio = cargar_espacio(Path(args.etiquetas))
    modelo = ModeloJerarquico(
        len(espacio.ordenes), len(espacio.familias), backbone=backbone, preentrenado=False
    )
    modelo.load_state_dict(torch.load(pesos, map_location="cpu"))

    exportar_onnx(modelo, Path(args.salida), lado=lado)
    entrada = None
    if Path(args.muestra).is_file():
        entrada = muestra_real(Path(args.muestra), Path(args.imagenes), lado=lado)
    else:
        print(f"AVISO: no existe {args.muestra}; la paridad se verifica con ruido, menos fiable.")
    resultado = verificar_paridad(modelo, Path(args.salida), entrada=entrada, lado=lado)
    print(
        f"Paridad torch vs onnx: probabilidades {resultado['diferencia_maxima']:.2e}, "
        f"logits {resultado['diferencia_logits']:.2e}, misma clase: {resultado['misma_clase']}"
    )
    if not resultado["coincide"]:
        raise SystemExit("El ONNX no coincide con PyTorch: NO desplegar este artefacto.")
    print(f"Exportado y verificado: {args.salida}")


if __name__ == "__main__":
    main()
