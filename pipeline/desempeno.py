"""Desempeño por clase de un modelo exportado, sobre el conjunto de prueba.

El informe de `pipeline.evaluar` da cifras globales. Para decidir qué mejorar
hace falta ver qué clases fallan y con cuál se confunden. Ejemplo: en el
modelo v1, familias de órdenes distintos aparecían "confundidas" con
Acrididae; en realidad había fallado el orden y el enmascaramiento jerárquico
forzó la familia dentro del orden equivocado. Solo la tabla por clase lo deja
ver.

Usa el ONNX exportado (lo mismo que se desplegará) y lee la resolución de la
corrida desde su `config.json`: analizar a 224 un modelo entrenado a 288
mediría otro encuadre.

    python -m pipeline.desempeno --corrida modelo/v3_b2_288 --salida docs/desempeno_por_clase_v3.md
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from pipeline.metricas import f1_por_clase, matriz_confusion

UMBRALES_COBERTURA = (0.0, 0.5, 0.6, 0.7, 0.8, 0.9)


def tabla_por_clase(real: list[int], pred: list[int], nombres: tuple[str, ...]) -> str:
    """F1, cantidad y confusión principal de cada clase, de la más débil a la más fuerte."""
    matriz = matriz_confusion(real, pred, len(nombres))
    f1 = f1_por_clase(matriz)
    apoyo = matriz.sum(axis=1)
    lineas = ["| Clase | F1 | Imágenes | Confusión principal |", "| --- | ---: | ---: | --- |"]
    for i in np.argsort(f1, kind="stable"):
        if not apoyo[i]:
            continue
        fila = matriz[i].copy()
        fila[i] = 0
        peor = int(fila.argmax())
        confusion = f"{nombres[peor]} ({fila[peor]})" if fila[peor] else "—"
        lineas.append(f"| {nombres[i]} | {f1[i]:.2f} | {apoyo[i]} | {confusion} |")
    return "\n".join(lineas)


def tabla_cobertura(
    confianzas: list[float], aciertos: list[bool], umbrales=UMBRALES_COBERTURA
) -> str:
    """Qué fracción responde el sistema si exige cada confianza mínima, y con qué acierto."""
    conf = np.asarray(confianzas)
    ac = np.asarray(aciertos, dtype=bool)
    lineas = ["| Umbral | Responde | Acierta cuando responde |", "| --- | ---: | ---: |"]
    for umbral in umbrales:
        sel = conf >= umbral
        if sel.any():
            lineas.append(f"| {umbral:.1f} | {100 * sel.mean():.0f}% | {100 * ac[sel].mean():.1f}% |")
        else:
            lineas.append(f"| {umbral:.1f} | 0% | — |")
    return "\n".join(lineas)


def analizar(corrida: Path, ruta_split: Path, raiz_imagenes: Path) -> str:
    import csv

    import onnxruntime as ort
    from PIL import Image

    from pipeline.corrida import opcion_de_corrida
    from pipeline.datos_torch import LADO, transformaciones_evaluacion
    from pipeline.etiquetas import cargar_espacio
    from pipeline.inferencia import enmascarar, softmax

    corrida = Path(corrida)
    lado = opcion_de_corrida(corrida / "mejor.pth", "lado", pedido=None, defecto=LADO)
    espacio = cargar_espacio(corrida / "etiquetas.json")
    pertenencia = np.array(espacio.matriz, dtype=bool)
    sesion = ort.InferenceSession(str(corrida / "insectos.onnx"), providers=["CPUExecutionProvider"])
    transformar = transformaciones_evaluacion(lado)

    with Path(ruta_split).open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))

    o_real, o_pred, f_real, f_pred, confianzas, aciertos = [], [], [], [], [], []
    for inicio in range(0, len(filas), 32):
        lote = filas[inicio : inicio + 32]
        x = np.stack([
            transformar(Image.open(Path(raiz_imagenes) / fila["archivo"]).convert("RGB")).numpy()
            for fila in lote
        ])
        logits_orden, logits_familia = sesion.run(None, {"imagen": x})
        for j, fila in enumerate(lote):
            orden = int(softmax(logits_orden[j].astype(np.float64)).argmax())
            o_real.append(espacio.indice_orden(fila["orden"]))
            o_pred.append(orden)
            if not fila["familia"]:
                continue
            probs = enmascarar(softmax(logits_familia[j].astype(np.float64)), orden, pertenencia)
            real = espacio.indice_familia(fila["familia"])
            f_real.append(real)
            f_pred.append(int(probs.argmax()))
            confianzas.append(float(probs.max()))
            aciertos.append(real == int(probs.argmax()))
        if inicio % 640 == 0:
            print(f"  {inicio}/{len(filas)}", flush=True)

    return "\n".join([
        f"# Desempeño por clase — {corrida.name}",
        "",
        f"Conjunto: `{ruta_split}` ({len(filas)} imágenes), resolución {lado} px.",
        "",
        "## Órdenes",
        "",
        tabla_por_clase(o_real, o_pred, espacio.ordenes),
        "",
        "## Familias",
        "",
        "Una familia de otro orden como \"confusión principal\" suele indicar que falló el "
        "orden y el enmascaramiento jerárquico forzó la familia dentro del orden equivocado.",
        "",
        tabla_por_clase(f_real, f_pred, espacio.familias),
        "",
        "## Cobertura contra confianza (familias)",
        "",
        tabla_cobertura(confianzas, aciertos),
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Desempeño por clase de un modelo exportado")
    parser.add_argument("--corrida", required=True, help="carpeta con insectos.onnx, etiquetas.json y config.json")
    parser.add_argument("--split", default="datos/splits/test.csv")
    parser.add_argument("--imagenes", default="datos/curado")
    parser.add_argument("--salida", required=True)
    args = parser.parse_args()

    texto = analizar(Path(args.corrida), Path(args.split), Path(args.imagenes))
    Path(args.salida).write_text(texto, encoding="utf-8")
    print(f"Escrito {args.salida}")


if __name__ == "__main__":
    main()
