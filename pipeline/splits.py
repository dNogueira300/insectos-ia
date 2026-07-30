"""Particionado train/val/test agrupado por observador y regla de admisión.

Agrupar por observador es la defensa contra la fuga de datos: las fotos de una
misma persona comparten cámara, fondo y a menudo el mismo individuo. Si se
reparten entre train y test, la métrica sube y el sistema falla en campo.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from pipeline.curacion import COLUMNAS_CURADO
from pipeline.ontologia import PREFIJO_OTROS, Ontologia, cargar_ontologia

PROPORCIONES = {"train": 0.70, "val": 0.15, "test": 0.15}

# Placeholder que pipeline.inat asigna al campo `observador` cuando la
# observación de iNaturalist no trae usuario registrado (ver
# `Observacion.observador` en pipeline/inat.py). No representa a una persona:
# es un cajón donde caen observaciones anónimas de gente distinta. Se
# mantiene como un observador más para el agrupamiento (separarlas sin saber
# quién las tomó arriesgaría fuga si en realidad compartieran fotógrafo),
# pero su peso debe quedar visible en el reporte.
OBSERVADOR_DESCONOCIDO = "desconocido"


def asignar_grupos(
    filas: list[dict], *, proporciones: dict[str, float] = PROPORCIONES
) -> dict[str, str]:
    """Asigna cada observador a un split. Determinista y balanceado por tamaño."""
    tamanos: dict[str, int] = defaultdict(int)
    for fila in filas:
        tamanos[fila["observador"]] += 1

    total = sum(tamanos.values())
    cupos = {split: proporcion * total for split, proporcion in proporciones.items()}
    asignados: dict[str, int] = {split: 0 for split in proporciones}
    asignacion: dict[str, str] = {}

    # De mayor a menor, con el nombre como desempate: el resultado no depende
    # del orden en que llegaron las filas.
    for observador in sorted(tamanos, key=lambda o: (-tamanos[o], o)):
        elegido = max(cupos, key=lambda s: cupos[s] - asignados[s])
        asignacion[observador] = elegido
        asignados[elegido] += tamanos[observador]
    return asignacion


def aplicar_regla_admision(
    filas: list[dict], asignacion: dict[str, str], onto: Ontologia
) -> tuple[list[dict], dict[str, str]]:
    """Reetiqueta como `Otros_<Orden>` las familias que no llegan al umbral."""
    conteo: dict[tuple[str, str], int] = defaultdict(int)
    for fila in filas:
        if fila["familia"]:
            conteo[(fila["familia"], asignacion[fila["observador"]])] += 1

    decisiones: dict[str, str] = {}
    for familia in {f["familia"] for f in filas if f["familia"]}:
        suficiente = (
            conteo[(familia, "train")] >= onto.minimo_familia_train
            and conteo[(familia, "test")] >= onto.minimo_familia_test
        )
        decisiones[familia] = "admitida" if suficiente else "agrupada"

    salida = []
    for fila in filas:
        copia = dict(fila)
        if copia["familia"] and decisiones[copia["familia"]] == "agrupada":
            copia["familia"] = f"{PREFIJO_OTROS}{copia['orden']}"
        salida.append(copia)
    return salida, decisiones


def particionar(filas: list[dict], onto: Ontologia) -> tuple[dict[str, list[dict]], dict]:
    """Devuelve las tres particiones y el resumen de lo decidido."""
    asignacion = asignar_grupos(filas)
    reetiquetadas, decisiones = aplicar_regla_admision(filas, asignacion, onto)

    particiones: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for fila in reetiquetadas:
        particiones[asignacion[fila["observador"]]].append(fila)

    # Imágenes y observadores únicos por clase y split, contados sobre la
    # asignación real (las particiones ya resueltas), no sobre una estimación.
    # Es la única forma de detectar que un split "suficiente" en imágenes
    # puede, aun así, provenir de una sola persona.
    imagenes_por_clase: dict[str, dict[str, int]] = defaultdict(
        lambda: {"train": 0, "val": 0, "test": 0}
    )
    observadores_por_clase: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"train": set(), "val": set(), "test": set()}
    )
    anonimos_por_split: dict[str, int] = {"train": 0, "val": 0, "test": 0}
    for split, filas_split in particiones.items():
        for fila in filas_split:
            clase = f"{fila['orden']}/{fila['familia'] or '_sin_familia'}"
            imagenes_por_clase[clase][split] += 1
            observadores_por_clase[clase][split].add(fila["observador"])
            if fila["observador"] == OBSERVADOR_DESCONOCIDO:
                anonimos_por_split[split] += 1

    por_clase = {
        clase: {
            split: {
                "imagenes": imagenes_por_clase[clase][split],
                "observadores": len(observadores_por_clase[clase][split]),
            }
            for split in ("train", "val", "test")
        }
        for clase in imagenes_por_clase
    }

    resumen = {
        "total": len(filas),
        "por_split": {split: len(v) for split, v in particiones.items()},
        "decisiones": decisiones,
        "por_clase": por_clase,
        "anonimos_por_split": anonimos_por_split,
    }
    return particiones, resumen


def escribir_particiones(particiones: dict[str, list[dict]], destino: Path) -> None:
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    for split, filas in particiones.items():
        with (destino / f"{split}.csv").open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
            escritor.writeheader()
            for fila in filas:
                escritor.writerow({c: fila.get(c, "") for c in COLUMNAS_CURADO})


def reporte_markdown(resumen: dict) -> str:
    lineas = [
        "# Reporte de particionado",
        "",
        f"Total de imágenes: **{resumen['total']}**",
        "",
        "| Split | Imágenes |",
        "| --- | ---: |",
    ]
    for split, cantidad in resumen["por_split"].items():
        lineas.append(f"| {split} | {cantidad} |")

    lineas += [
        "",
        "El particionado agrupa por **observador**: ninguna persona aparece en dos "
        "splits. Es la defensa contra la fuga de datos descrita en el diseño (§7).",
        "",
        "## Decisiones de admisión de familias",
        "",
        "| Familia | Decisión |",
        "| --- | --- |",
    ]
    for familia, decision in sorted(resumen["decisiones"].items()):
        lineas.append(f"| {familia} | {decision} |")

    agrupadas = [f for f, d in resumen["decisiones"].items() if d == "agrupada"]
    lineas += [
        "",
        (
            f"**{len(agrupadas)} familias no alcanzaron el umbral** y quedaron dentro de "
            f"`Otros_<Orden>`: {', '.join(sorted(agrupadas))}. Llevar esta lista a la "
            "Facultad: o se consiguen más imágenes para ellas, o se sustituyen por otras."
            if agrupadas
            else "Todas las familias alcanzaron el umbral."
        ),
        "",
        "## Distribución por clase",
        "",
        "Cada celda muestra **imágenes / observadores distintos**: si el número de "
        "observadores es bajo —sobre todo en test— el número de imágenes por sí solo "
        "engaña sobre qué tan bien evaluada está esa clase.",
        "",
        "| Clase | train | val | test |",
        "| --- | ---: | ---: | ---: |",
    ]
    por_clase = resumen.get("por_clase", {})
    for clase, conteo in sorted(por_clase.items()):
        celdas = " | ".join(
            f"{conteo[split]['imagenes']} img / {conteo[split]['observadores']} obs"
            for split in ("train", "val", "test")
        )
        lineas.append(f"| {clase} | {celdas} |")

    clases_riesgo = sorted(
        clase for clase, conteo in por_clase.items() if conteo["test"]["observadores"] == 1
    )
    lineas += [
        "",
        "## Alerta: clases cuyo test depende de un solo fotógrafo",
        "",
    ]
    if clases_riesgo:
        lineas.append(
            "Estas clases superan el número mínimo de imágenes de prueba exigido, pero "
            "**todas esas imágenes de test vienen de una sola persona**. Eso significa que "
            "el resultado que el reporte de evaluación muestre para esa clase no mide qué "
            "tan bien el modelo reconoce la familia en el campo: mide qué tan bien memorizó "
            "la cámara, el encuadre, la iluminación o el fondo de esa única persona. Conviene "
            "tratar estos resultados con cautela en la reunión de decisión, hasta conseguir "
            "fotos de test de más observadores:"
        )
        lineas.append("")
        for clase in clases_riesgo:
            n_img = por_clase[clase]["test"]["imagenes"]
            lineas.append(f"- `{clase}`: {n_img} imágenes de test, todas del mismo observador.")
    else:
        lineas.append("Ninguna clase depende de un único fotógrafo en su conjunto de test.")

    anonimos = resumen.get("anonimos_por_split") or {"train": 0, "val": 0, "test": 0}
    total_anonimos = sum(anonimos.values())
    lineas += [
        "",
        "## Observaciones sin fotógrafo identificado",
        "",
    ]
    if total_anonimos:
        detalle = ", ".join(f"{split}: {cantidad}" for split, cantidad in anonimos.items())
        lineas.append(
            f"**{total_anonimos} imágenes** quedaron agrupadas bajo el identificador "
            f"`{OBSERVADOR_DESCONOCIDO}` porque la observación de iNaturalist no traía "
            "usuario registrado. Ese identificador **no es una sola persona**: es un cajón "
            "donde caen observaciones anónimas de gente distinta, agrupadas juntas a "
            "propósito (separarlas sin saber quién las tomó podría, en realidad, causar la "
            "fuga que este particionado evita, si dos de ellas compartieran fotógrafo). Se "
            f"repartieron así entre los splits: {detalle}. Si la cifra es una porción grande "
            "del total, conviene saberlo antes de confiar en la partición."
        )
    else:
        lineas.append("No hubo observaciones sin fotógrafo identificado.")

    return "\n".join(lineas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Particionado del dataset curado")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--curado", default="datos/curado")
    parser.add_argument("--destino", default="datos/splits")
    args = parser.parse_args()

    onto = cargar_ontologia(Path(args.ontologia))
    with (Path(args.curado) / "manifiesto_curado.csv").open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))

    particiones, resumen = particionar(filas, onto)
    escribir_particiones(particiones, Path(args.destino))
    Path("docs/reporte_splits.md").write_text(reporte_markdown(resumen), encoding="utf-8")
    print({k: len(v) for k, v in particiones.items()})


if __name__ == "__main__":
    main()
