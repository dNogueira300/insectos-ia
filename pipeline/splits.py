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

    por_clase: dict[str, dict[str, int]] = defaultdict(lambda: {"train": 0, "val": 0, "test": 0})
    for split, filas_split in particiones.items():
        for fila in filas_split:
            por_clase[f"{fila['orden']}/{fila['familia'] or '_sin_familia'}"][split] += 1

    resumen = {
        "total": len(filas),
        "por_split": {split: len(v) for split, v in particiones.items()},
        "decisiones": decisiones,
        "por_clase": {k: dict(v) for k, v in por_clase.items()},
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
        "| Clase | train | val | test |",
        "| --- | ---: | ---: | ---: |",
    ]
    for clase, conteo in sorted(resumen["por_clase"].items()):
        lineas.append(f"| {clase} | {conteo['train']} | {conteo['val']} | {conteo['test']} |")
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
