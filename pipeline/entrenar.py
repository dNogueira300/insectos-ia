"""Bucle de entrenamiento del modelo jerárquico.

Dos fases: primero las cabezas solas sobre un backbone congelado, después
todo descongelado con tasa menor. La parada temprana vigila el macro-F1 de
familia en validación, que es la métrica que decide el proyecto.

Reanudable (adenda del Plan 02): el entrenamiento corre en Colab gratuito, que
corta sesiones sin aviso, y dos cuentas se turnan sobre la misma carpeta de
Drive. Al cerrar cada época se escribe `ultimo.pth` de forma atómica, con todo
lo necesario para que una corrida cortada y reanudada sea indistinguible de
una sin cortes: pesos, optimizador, escalador de precisión mixta, estado de
los generadores aleatorios, historial y mejor métrica.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from collections.abc import Callable
from pathlib import Path

import numpy as np
import torch

from pipeline import metricas
from pipeline.datos_torch import LADO, cargadores, leer_split, pesos_de_familia
from pipeline.etiquetas import SIN_FAMILIA_IDX, EspacioEtiquetas, construir_espacio
from pipeline.inferencia import enmascarar, softmax
from pipeline.modelo import (
    BACKBONE_POR_DEFECTO,
    SUAVIZADO,
    ModeloJerarquico,
    PerdidaCombinada,
)
from pipeline.ontologia import cargar_ontologia

SEMILLA = 42
EPOCAS_CONGELADO = 2
PACIENCIA = 4

# Fracción de la tasa inicial a la que se llega al final del entrenamiento. El
# v1 entrenó con tasa fija y se estancó: los últimos pasos seguían siendo tan
# grandes como los primeros y el modelo oscilaba en torno al mismo punto.
FRACCION_TASA_FINAL = 0.02

ARCHIVO_ULTIMO = "ultimo.pth"
ARCHIVO_MEJOR = "mejor.pth"
ARCHIVO_CONFIG = "config.json"


class ErrorCorrida(Exception):
    """La carpeta de destino no admite la corrida pedida (ver `entrenar`)."""


def fijar_semilla(valor: int = SEMILLA) -> None:
    random.seed(valor)
    np.random.seed(valor)
    torch.manual_seed(valor)
    torch.cuda.manual_seed_all(valor)


def epoca_entrenamiento(
    modelo, cargador, perdida, optimizador, dispositivo, escalador=None
) -> dict:
    """Una pasada por el cargador. Con `escalador` usa precisión mixta (GPU)."""
    modelo.train()
    sumas = {"perdida": 0.0, "perdida_orden": 0.0, "perdida_familia": 0.0}
    lotes = 0

    for imagenes, y_orden, y_familia in cargador:
        imagenes = imagenes.to(dispositivo)
        y_orden = y_orden.to(dispositivo)
        y_familia = y_familia.to(dispositivo)

        optimizador.zero_grad()
        with torch.autocast(device_type="cuda", enabled=escalador is not None):
            logits_orden, logits_familia = modelo(imagenes)
            total, de_orden, de_familia = perdida(
                logits_orden.float(), logits_familia.float(), y_orden, y_familia
            )
        if escalador is not None:
            escalador.scale(total).backward()
            escalador.step(optimizador)
            escalador.update()
        else:
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
        with torch.autocast(device_type="cuda", enabled=str(dispositivo) == "cuda"):
            logits_orden, logits_familia = modelo(imagenes.to(dispositivo))
        logits_orden = logits_orden.float().cpu().numpy()
        logits_familia = logits_familia.float().cpu().numpy()

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


def _fase(epoca: int) -> str:
    return "congelado" if epoca < EPOCAS_CONGELADO else "descongelado"


def _optimizador_de_fase(modelo, epoca: int, tasa: float, epocas: int):
    """Congela o descongela el backbone, y arma optimizador y planificador.

    Durante el calentamiento la tasa es fija: son dos épocas en las que solo se
    acomodan las cabezas. Al descongelar, la tasa baja en coseno hasta una
    fracción de la inicial a lo largo de las épocas que queden, para afinar al
    final en vez de seguir dando saltos grandes.
    """
    if _fase(epoca) == "congelado":
        modelo.congelar_backbone()
        optimizador = torch.optim.AdamW(
            [p for p in modelo.parameters() if p.requires_grad], lr=tasa
        )
        return optimizador, None

    modelo.descongelar_backbone()
    inicial = tasa / 10
    optimizador = torch.optim.AdamW(modelo.parameters(), lr=inicial)
    planificador = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizador,
        # Un paso menos que las épocas descongeladas: así la última entrena ya
        # en el mínimo, en vez de quedarse a medio camino del descenso.
        T_max=max(1, epocas - EPOCAS_CONGELADO - 1),
        eta_min=inicial * FRACCION_TASA_FINAL,
    )
    return optimizador, planificador


def _guardar_atomico(objeto, ruta: Path) -> None:
    """Un corte de Colab a mitad de la escritura no puede dañar el checkpoint:
    se escribe un temporal y se reemplaza solo cuando está completo."""
    temporal = ruta.with_name(ruta.name + ".tmp")
    torch.save(objeto, temporal)
    os.replace(temporal, ruta)


def _estado_rng() -> dict:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
    }


def _restaurar_rng(estado: dict) -> None:
    random.setstate(estado["python"])
    np.random.set_state(estado["numpy"])
    torch.set_rng_state(estado["torch"])
    if estado["cuda"] is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(estado["cuda"])


def _fabricar_por_defecto(n_ordenes: int, n_familias: int, backbone: str):
    return ModeloJerarquico(n_ordenes, n_familias, backbone=backbone)


def _verificar_config(destino: Path, config: dict) -> None:
    guardada = json.loads((destino / ARCHIVO_CONFIG).read_text(encoding="utf-8"))
    distintas = [
        f"{clave} (guardada {guardada.get(clave)!r}, pedida {valor!r})"
        for clave, valor in config.items()
        if guardada.get(clave) != valor
    ]
    if distintas:
        raise ErrorCorrida(
            f"{destino} es una corrida con otra configuración: {'; '.join(distintas)}. "
            "No se reanuda una corrida con otros hiperparámetros: usar otro --destino."
        )


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
    suavizado: float = SUAVIZADO,
    lado: int = LADO,
    trabajadores: int = 4,
    reanudar: bool = False,
    al_terminar_epoca: Callable[[int], None] | None = None,
    fabricar_modelo: Callable = _fabricar_por_defecto,
) -> dict:
    """Entrena (o reanuda) una corrida en `destino`.

    - Si `destino` ya tiene `ultimo.pth` y no se pide `reanudar`, falla: en una
      carpeta de Drive compartida, pisar la corrida del compañero por olvidar
      la opción borraría horas de GPU.
    - Con `reanudar` y sin checkpoint, empieza de cero (el cuaderno de Colab
      siempre pasa la opción).
    - `al_terminar_epoca(epoca)` se llama después de guardar el checkpoint de
      esa época: lo usa el turno compartido para actualizar su latido.
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Dispositivo: {dispositivo}")

    filas_train = leer_split(Path(ruta_splits) / "train.csv")
    filas_val = leer_split(Path(ruta_splits) / "val.csv")
    config = {
        "semilla": SEMILLA,
        "backbone": backbone,
        "epocas": epocas,
        "lote": lote,
        "tasa": tasa,
        "lambda_familia": lambda_familia,
        "suavizado": suavizado,
        "lado": lado,
        "n_train": len(filas_train),
        "n_val": len(filas_val),
    }

    ruta_ultimo = destino / ARCHIVO_ULTIMO
    estado = None
    if ruta_ultimo.is_file():
        if not reanudar:
            raise ErrorCorrida(
                f"{destino} ya tiene una corrida ({ARCHIVO_ULTIMO}). Para continuarla, "
                "usar --reanudar; para empezar otra, usar otro --destino."
            )
        _verificar_config(destino, config)
        estado = torch.load(ruta_ultimo, map_location=dispositivo, weights_only=False)
        if estado["terminado"]:
            print(f"La corrida de {destino} ya había terminado; no se entrena de nuevo.")
            return estado["resultado"]
        print(f"Reanudando desde la época {estado['epoca'] + 1}")
    else:
        (destino / ARCHIVO_CONFIG).write_text(
            json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    fijar_semilla()
    onto = cargar_ontologia(ruta_ontologia)
    espacio = construir_espacio(filas_train, onto)
    espacio.guardar(destino / "etiquetas.json")
    print(f"{len(espacio.ordenes)} órdenes, {len(espacio.familias)} familias")

    cargador_train, cargador_val = cargadores(
        filas_train, filas_val, raiz_imagenes, espacio,
        lote=lote, trabajadores=trabajadores, lado=lado,
    )
    modelo = fabricar_modelo(len(espacio.ordenes), len(espacio.familias), backbone).to(dispositivo)
    perdida = PerdidaCombinada(
        pesos_familia=pesos_de_familia(filas_train, espacio).to(dispositivo),
        lambda_familia=lambda_familia,
        suavizado=suavizado,
    )
    escalador = torch.amp.GradScaler("cuda") if dispositivo == "cuda" else None

    planificador = None
    mejor, mejor_epoca, historial, inicio = -1.0, -1, [], 0
    if estado is not None:
        modelo.load_state_dict(estado["modelo"])
        if escalador is not None and estado["escalador"] is not None:
            escalador.load_state_dict(estado["escalador"])
        mejor, mejor_epoca = estado["mejor"], estado["mejor_epoca"]
        historial = estado["historial"]
        inicio = estado["epoca"] + 1
        # Al final: construir el modelo y los cargadores consume azar, y lo que
        # debe continuar es el azar tal como quedó al cerrar la última época.
        _restaurar_rng(estado["rng"])

    resultado: dict = {}
    for epoca in range(inicio, epocas):
        if epoca == inicio or epoca == EPOCAS_CONGELADO:
            optimizador, planificador = _optimizador_de_fase(modelo, epoca, tasa, epocas)
            # El estado del optimizador solo sirve dentro de su misma fase: al
            # cruzar a la fase descongelada, la corrida sin cortes también
            # empieza con un optimizador nuevo. El planificador viaja con él:
            # sin su estado, al reanudar la tasa volvería a su valor inicial.
            if estado is not None and epoca == inicio and _fase(epoca) == _fase(estado["epoca"]):
                optimizador.load_state_dict(estado["optimizador"])
                if planificador is not None and estado["planificador"] is not None:
                    planificador.load_state_dict(estado["planificador"])

        tasa_actual = optimizador.param_groups[0]["lr"]

        resumen_train = epoca_entrenamiento(
            modelo, cargador_train, perdida, optimizador, dispositivo, escalador
        )
        resumen_val = evaluar_cargador(modelo, cargador_val, espacio, dispositivo)
        if planificador is not None:
            planificador.step()
        historial.append({"epoca": epoca, "tasa": tasa_actual, **resumen_train, **resumen_val})
        print(
            f"época {epoca:2d} | pérdida {resumen_train['perdida']:.3f} | "
            f"F1 orden {resumen_val['macro_f1_orden']:.3f} | "
            f"F1 familia {resumen_val['macro_f1_familia']:.3f}",
            flush=True,
        )

        detener = epoca == epocas - 1
        if resumen_val["macro_f1_familia"] > mejor:
            mejor = resumen_val["macro_f1_familia"]
            mejor_epoca = epoca
            _guardar_atomico(modelo.state_dict(), destino / ARCHIVO_MEJOR)
        elif epoca - mejor_epoca >= PACIENCIA:
            print(f"parada temprana en la época {epoca}")
            detener = True

        if detener:
            resultado = {
                **config,
                "epocas_corridas": len(historial),
                "mejor_epoca": mejor_epoca,
                "mejor_macro_f1_familia_val": mejor,
                "historial": historial,
            }
            (destino / "metricas.json").write_text(
                json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
            )

        _guardar_atomico(
            {
                "epoca": epoca,
                "modelo": modelo.state_dict(),
                "optimizador": optimizador.state_dict(),
                "planificador": planificador.state_dict() if planificador is not None else None,
                "escalador": escalador.state_dict() if escalador is not None else None,
                "mejor": mejor,
                "mejor_epoca": mejor_epoca,
                "historial": historial,
                "rng": _estado_rng(),
                "terminado": detener,
                "resultado": resultado,
            },
            ruta_ultimo,
        )
        if al_terminar_epoca is not None:
            al_terminar_epoca(epoca)
        if detener:
            break

    return resultado


def construir_parser() -> argparse.ArgumentParser:
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
    parser.add_argument("--suavizado", type=float, default=SUAVIZADO)
    parser.add_argument(
        "--lado", type=int, default=LADO,
        help="resolución de entrada; exportar y evaluar la toman de config.json",
    )
    parser.add_argument("--trabajadores", type=int, default=4)
    parser.add_argument(
        "--reanudar",
        action="store_true",
        help="continúa la corrida de --destino desde su último checkpoint, si existe",
    )
    return parser


def main() -> None:
    args = construir_parser().parse_args()
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
        suavizado=args.suavizado,
        lado=args.lado,
        trabajadores=args.trabajadores,
        reanudar=args.reanudar,
    )
    print(f"Mejor macro-F1 de familia en validación: {resultado['mejor_macro_f1_familia_val']:.3f}")


if __name__ == "__main__":
    main()
