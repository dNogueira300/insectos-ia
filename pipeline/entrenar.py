"""Bucle de entrenamiento del modelo jerárquico.

Dos fases: primero las cabezas solas sobre un backbone congelado, después
todo descongelado con tasa menor. La parada temprana vigila el macro-F1 de
familia en validación, que es la métrica que decide el proyecto.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch

from pipeline import metricas
from pipeline.datos_torch import cargadores, leer_split, pesos_de_familia
from pipeline.etiquetas import SIN_FAMILIA_IDX, EspacioEtiquetas, construir_espacio
from pipeline.inferencia import enmascarar, softmax
from pipeline.modelo import BACKBONE_POR_DEFECTO, ModeloJerarquico, PerdidaCombinada
from pipeline.ontologia import cargar_ontologia

SEMILLA = 42
EPOCAS_CONGELADO = 2
PACIENCIA = 4


def fijar_semilla(valor: int = SEMILLA) -> None:
    random.seed(valor)
    np.random.seed(valor)
    torch.manual_seed(valor)
    torch.cuda.manual_seed_all(valor)


def epoca_entrenamiento(modelo, cargador, perdida, optimizador, dispositivo) -> dict:
    modelo.train()
    sumas = {"perdida": 0.0, "perdida_orden": 0.0, "perdida_familia": 0.0}
    lotes = 0

    for imagenes, y_orden, y_familia in cargador:
        imagenes = imagenes.to(dispositivo)
        y_orden = y_orden.to(dispositivo)
        y_familia = y_familia.to(dispositivo)

        optimizador.zero_grad()
        logits_orden, logits_familia = modelo(imagenes)
        total, de_orden, de_familia = perdida(logits_orden, logits_familia, y_orden, y_familia)
        total.backward()
        optimizador.step()

        sumas["perdida"] += float(total.detach())
        sumas["perdida_orden"] += float(de_orden.detach())
        sumas["perdida_familia"] += float(de_familia.detach())
        lotes += 1

    return {clave: valor / max(lotes, 1) for clave, valor in sumas.items()}


@torch.no_grad()
def evaluar_cargador(modelo, cargador, espacio: EspacioEtiquetas, dispositivo) -> dict:
    """Evalúa aplicando el mismo enmascaramiento jerárquico que usa el backend."""
    modelo.eval()
    matriz = np.array(espacio.matriz, dtype=bool)

    orden_real: list[int] = []
    orden_pred: list[int] = []
    fam_real: list[int] = []
    fam_pred: list[int] = []
    probs_familia_todas: list[np.ndarray] = []

    for imagenes, y_orden, y_familia in cargador:
        logits_orden, logits_familia = modelo(imagenes.to(dispositivo))
        logits_orden = logits_orden.cpu().numpy()
        logits_familia = logits_familia.cpu().numpy()

        for i in range(len(y_orden)):
            probs_o = softmax(logits_orden[i].astype(np.float64))
            predicho_o = int(np.argmax(probs_o))
            orden_real.append(int(y_orden[i]))
            orden_pred.append(predicho_o)

            if int(y_familia[i]) == SIN_FAMILIA_IDX:
                continue
            probs_f = enmascarar(
                softmax(logits_familia[i].astype(np.float64)), predicho_o, matriz
            )
            fam_real.append(int(y_familia[i]))
            fam_pred.append(int(np.argmax(probs_f)))
            probs_familia_todas.append(probs_f)

    n_ordenes = len(espacio.ordenes)
    n_familias = len(espacio.familias)
    probs = (
        np.vstack(probs_familia_todas)
        if probs_familia_todas
        else np.zeros((0, n_familias))
    )

    return {
        "macro_f1_orden": metricas.macro_f1(orden_real, orden_pred, n_ordenes),
        "macro_f1_familia": (
            metricas.macro_f1(fam_real, fam_pred, n_familias) if fam_real else 0.0
        ),
        "exactitud_orden": metricas.exactitud(orden_real, orden_pred),
        "exactitud_familia": metricas.exactitud(fam_real, fam_pred) if fam_real else 0.0,
        "exactitud_jerarquica": (
            metricas.exactitud_jerarquica(
                orden_real[: len(fam_real)], orden_pred[: len(fam_real)], fam_real, fam_pred
            )
            if fam_real
            else 0.0
        ),
        "top3_familia": metricas.top_k(probs, fam_real, k=3) if fam_real else 0.0,
    }


def entrenar(
    *,
    ruta_ontologia: Path,
    raiz_imagenes: Path,
    ruta_splits: Path,
    destino: Path,
    backbone: str = BACKBONE_POR_DEFECTO,
    epocas: int = 25,
    lote: int = 32,
    tasa: float = 1e-3,
    lambda_familia: float = 1.0,
) -> dict:
    fijar_semilla()
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Dispositivo: {dispositivo}")

    onto = cargar_ontologia(ruta_ontologia)
    filas_train = leer_split(Path(ruta_splits) / "train.csv")
    filas_val = leer_split(Path(ruta_splits) / "val.csv")

    espacio = construir_espacio(filas_train, onto)
    destino = Path(destino)
    espacio.guardar(destino / "etiquetas.json")
    print(f"{len(espacio.ordenes)} órdenes, {len(espacio.familias)} familias")

    cargador_train, cargador_val = cargadores(
        filas_train, filas_val, raiz_imagenes, espacio, lote=lote
    )

    modelo = ModeloJerarquico(
        len(espacio.ordenes), len(espacio.familias), backbone=backbone
    ).to(dispositivo)
    perdida = PerdidaCombinada(
        pesos_familia=pesos_de_familia(filas_train, espacio).to(dispositivo),
        lambda_familia=lambda_familia,
    )

    mejor = -1.0
    mejor_epoca = -1
    historial = []

    for epoca in range(epocas):
        if epoca == 0:
            modelo.congelar_backbone()
            optimizador = torch.optim.AdamW(
                [p for p in modelo.parameters() if p.requires_grad], lr=tasa
            )
        elif epoca == EPOCAS_CONGELADO:
            modelo.descongelar_backbone()
            optimizador = torch.optim.AdamW(modelo.parameters(), lr=tasa / 10)

        resumen_train = epoca_entrenamiento(
            modelo, cargador_train, perdida, optimizador, dispositivo
        )
        resumen_val = evaluar_cargador(modelo, cargador_val, espacio, dispositivo)
        historial.append({"epoca": epoca, **resumen_train, **resumen_val})
        print(
            f"época {epoca:2d} | pérdida {resumen_train['perdida']:.3f} | "
            f"F1 orden {resumen_val['macro_f1_orden']:.3f} | "
            f"F1 familia {resumen_val['macro_f1_familia']:.3f}"
        )

        if resumen_val["macro_f1_familia"] > mejor:
            mejor = resumen_val["macro_f1_familia"]
            mejor_epoca = epoca
            torch.save(modelo.state_dict(), destino / "mejor.pth")
        elif epoca - mejor_epoca >= PACIENCIA:
            print(f"parada temprana en la época {epoca}")
            break

    resultado = {
        "semilla": SEMILLA,
        "backbone": backbone,
        "epocas_corridas": len(historial),
        "mejor_epoca": mejor_epoca,
        "mejor_macro_f1_familia_val": mejor,
        "n_train": len(filas_train),
        "n_val": len(filas_val),
        "historial": historial,
    }
    (destino / "metricas.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena el modelo jerárquico")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--imagenes", default="datos/curado")
    parser.add_argument("--splits", default="datos/splits")
    parser.add_argument("--destino", default="modelo")
    parser.add_argument("--backbone", default=BACKBONE_POR_DEFECTO)
    parser.add_argument("--epocas", type=int, default=25)
    parser.add_argument("--lote", type=int, default=32)
    parser.add_argument("--tasa", type=float, default=1e-3)
    parser.add_argument("--lambda-familia", type=float, default=1.0)
    args = parser.parse_args()

    Path(args.destino).mkdir(parents=True, exist_ok=True)
    resultado = entrenar(
        ruta_ontologia=Path(args.ontologia),
        raiz_imagenes=Path(args.imagenes),
        ruta_splits=Path(args.splits),
        destino=Path(args.destino),
        backbone=args.backbone,
        epocas=args.epocas,
        lote=args.lote,
        tasa=args.tasa,
        lambda_familia=args.lambda_familia,
    )
    print(f"Mejor macro-F1 de familia en validación: {resultado['mejor_macro_f1_familia_val']:.3f}")


if __name__ == "__main__":
    main()
