"""Evaluación final contra el test de repositorio y el test de campo."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from pipeline.corrida import opcion_de_corrida
from pipeline.datos_torch import (
    LADO,
    DatasetInsectos,
    leer_split,
    transformaciones_evaluacion,
)
from pipeline.entrenar import evaluar_cargador
from pipeline.etiquetas import EspacioEtiquetas, cargar_espacio
from pipeline.modelo import BACKBONE_POR_DEFECTO, ModeloJerarquico

META_ORDEN = 0.90
META_FAMILIA = 0.85


def evaluar_split(
    modelo, filas: list[dict], raiz: Path, espacio, dispositivo, *, lado: int = LADO
) -> dict:
    conjunto = DatasetInsectos(filas, raiz, espacio, transformaciones_evaluacion(lado))
    cargador = DataLoader(conjunto, batch_size=32, shuffle=False)
    return {**evaluar_cargador(modelo, cargador, espacio, dispositivo), "n": len(filas)}


def reporte_markdown(
    resultados: dict[str, dict],
    espacio: EspacioEtiquetas,
    meta_orden: float = META_ORDEN,
    meta_familia: float = META_FAMILIA,
) -> str:
    conjuntos = list(resultados)
    filas_metricas = [
        ("macro-F1 de orden", "macro_f1_orden"),
        ("macro-F1 de familia", "macro_f1_familia"),
        ("Exactitud de orden", "exactitud_orden"),
        ("Exactitud de familia", "exactitud_familia"),
        ("Exactitud jerárquica", "exactitud_jerarquica"),
        ("Top-3 de familia", "top3_familia"),
    ]

    lineas = [
        "# Informe de métricas",
        "",
        f"Espacio de clases: **{len(espacio.ordenes)} órdenes**, "
        f"**{len(espacio.familias)} familias**.",
        "",
        "| Métrica | " + " | ".join(conjuntos) + " |",
        "| --- | " + " | ".join("---:" for _ in conjuntos) + " |",
    ]
    for etiqueta, clave in filas_metricas:
        valores = " | ".join(f"{resultados[c][clave]:.3f}" for c in conjuntos)
        lineas.append(f"| {etiqueta} | {valores} |")
    lineas.append(
        "| Imágenes | " + " | ".join(str(resultados[c]["n"]) for c in conjuntos) + " |"
    )

    lineas += ["", "## Criterio de aceptación", ""]
    if "campo" in resultados:
        campo = resultados["campo"]
        for etiqueta, clave, meta in (
            ("Orden", "macro_f1_orden", meta_orden),
            ("Familia", "macro_f1_familia", meta_familia),
        ):
            estado = "ALCANZADA" if campo[clave] >= meta else "NO ALCANZADA"
            lineas.append(
                f"- **{etiqueta}**: macro-F1 de {campo[clave]:.3f} en campo "
                f"frente a la meta de {meta:.2f} — meta **{estado}**."
            )
        if "test" in resultados:
            brecha = resultados["test"]["macro_f1_familia"] - campo["macro_f1_familia"]
            lineas += [
                "",
                f"**Brecha repositorio → campo en familia: {brecha:.2f}.** Es la caída "
                "al pasar de fotos curadas de iNaturalist a fotos tomadas en parcela. "
                "Una brecha grande indica que el modelo aprendió el estilo de las fotos "
                "de repositorio más que el insecto, y se corrige con más aumentos de "
                "datos y más material de campo, no con más épocas.",
            ]
    else:
        lineas.append(
            "- Evaluado **sin conjunto de campo**. Estas cifras son optimistas: "
            "miden desempeño sobre fotos curadas de repositorio, no sobre fotos de "
            "parcela. No usarlas para declarar la meta alcanzada."
        )

    return "\n".join(lineas) + "\n"


def destino_resultados(ruta_pesos: Path) -> Path:
    """Los resultados van junto a los pesos evaluados, no a una ruta fija:
    en Colab la corrida vive en Drive y `modelo/` no existe."""
    return Path(ruta_pesos).with_name("evaluacion.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluación final del modelo")
    parser.add_argument("--pesos", default="modelo/mejor.pth")
    parser.add_argument("--etiquetas", default="modelo/etiquetas.json")
    parser.add_argument("--splits", default="datos/splits")
    parser.add_argument("--curado", default="datos/curado")
    parser.add_argument("--campo", default="datos/campo_crudo")
    parser.add_argument("--backbone", default=None)
    parser.add_argument("--lado", type=int, default=None)
    parser.add_argument("--salida", default="docs/informe_metricas.md")
    args = parser.parse_args()

    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    pesos = Path(args.pesos)
    backbone = opcion_de_corrida(
        pesos, "backbone", pedido=args.backbone, defecto=BACKBONE_POR_DEFECTO
    )
    lado = opcion_de_corrida(pesos, "lado", pedido=args.lado, defecto=LADO)
    print(f"Backbone {backbone} a {lado} px (según la corrida)")

    espacio = cargar_espacio(Path(args.etiquetas))
    modelo = ModeloJerarquico(
        len(espacio.ordenes), len(espacio.familias), backbone=backbone, preentrenado=False
    )
    modelo.load_state_dict(torch.load(pesos, map_location=dispositivo))
    modelo.to(dispositivo)

    resultados = {
        "test": evaluar_split(
            modelo, leer_split(Path(args.splits) / "test.csv"), Path(args.curado),
            espacio, dispositivo, lado=lado,
        )
    }

    ruta_campo = Path(args.splits) / "campo.csv"
    filas_campo = leer_split(ruta_campo) if ruta_campo.exists() else []
    if filas_campo:
        resultados["campo"] = evaluar_split(
            modelo, filas_campo, Path(args.campo), espacio, dispositivo, lado=lado
        )

    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(reporte_markdown(resultados, espacio), encoding="utf-8")
    destino_resultados(Path(args.pesos)).write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Informe en {args.salida}")
    for conjunto, valores in resultados.items():
        print(f"  {conjunto}: F1 familia {valores['macro_f1_familia']:.3f}")


if __name__ == "__main__":
    main()
