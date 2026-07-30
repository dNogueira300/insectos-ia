"""Curación del dataset: deduplicado perceptual y descarte de archivos malos.

El deduplicado usa indexado por bandas: dos huellas a distancia <= 3
comparten al menos una banda de 16 bits, así que basta comparar dentro de
cada cubeta en vez de todos los pares.
"""
from __future__ import annotations

import argparse
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image

from pipeline import imagenes
from pipeline.descarga import COLUMNAS_MANIFIESTO, leer_manifiesto

COLUMNAS_CURADO = COLUMNAS_MANIFIESTO + ("hash",)

# Nombre del manifiesto que `curar` escribe en `raiz_curado`. También sirve de
# marca: si ya existe, `raiz_curado` es un directorio de curación de una
# corrida anterior y es seguro reconciliarlo (ver `_reconciliar_destino`).
NOMBRE_MANIFIESTO_CURADO = "manifiesto_curado.csv"


def hashes_de(filas: list[dict], raiz: Path) -> list[dict]:
    """Añade la columna `hash` a cada fila. Vacía si el archivo es ilegible."""
    raiz = Path(raiz)
    salida = []
    for fila in filas:
        copia = dict(fila)
        try:
            with Image.open(raiz / fila["archivo"]) as img:
                copia["hash"] = imagenes.hash_perceptual(img.convert("RGB"))
        except Exception:
            copia["hash"] = ""
        salida.append(copia)
    return salida


def _prioridad(fila: dict) -> tuple[int, int]:
    """Ordena para que, entre duplicadas, gane la fila con familia declarada."""
    return (0 if fila.get("familia") else 1, int(fila.get("obs_id") or 0))


def deduplicar(
    filas: list[dict], *, umbral: int = 3, hashes_externos: set[str] | None = None
) -> tuple[list[dict], list[dict]]:
    """Separa las filas en conservadas y descartadas."""
    externos = hashes_externos or set()
    conservadas: list[dict] = []
    descartadas: list[dict] = []
    indice: dict[str, list[str]] = defaultdict(list)  # banda -> huellas conservadas

    for fila in sorted(filas, key=_prioridad):
        huella = fila.get("hash", "")
        if not huella:
            descartadas.append(dict(fila, motivo="ilegible"))
            continue

        if any(imagenes.distancia(huella, ext) <= umbral for ext in externos):
            descartadas.append(dict(fila, motivo="duplicado_externo"))
            continue

        candidatas = {c for banda in imagenes.bandas(huella) for c in indice[banda]}
        if any(imagenes.distancia(huella, c) <= umbral for c in candidatas):
            descartadas.append(dict(fila, motivo="duplicado"))
            continue

        conservadas.append(fila)
        for banda in imagenes.bandas(huella):
            indice[banda].append(huella)

    return conservadas, descartadas


def _escribir_curado(filas: list[dict], ruta: Path) -> None:
    import csv

    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({c: fila.get(c, "") for c in COLUMNAS_CURADO})


def _reconciliar_destino(raiz_curado: Path, conservadas: list[dict]) -> None:
    """Deja en `raiz_curado` solo los archivos listados en `conservadas`.

    Una corrida anterior pudo haber copiado imágenes que esta corrida ya no
    conserva -por ejemplo, si el manifiesto de origen cambió entre medio-.
    Sin esto esos archivos quedarían huérfanos: sin fila que los respalde en
    el CSV, pero visibles para cualquier cargador que liste carpetas
    directamente en vez de leer el manifiesto (así funcionan los `ImageFolder`
    típicos), coleándose al entrenamiento sin trazabilidad, sin licencia y
    sin haber pasado por el particionado por observador de la Tarea 7.

    Solo actúa si `raiz_curado` ya tiene su propio `manifiesto_curado.csv` de
    una corrida previa: esa es la marca de que este módulo es dueño del
    directorio. Si no está, no se borra nada -así un `--curado` mal escrito
    que apunte a una carpeta ajena no pierde contenido que no puso `curar`-.
    """
    marca = raiz_curado / NOMBRE_MANIFIESTO_CURADO
    if not marca.exists():
        return

    esperados = {(raiz_curado / fila["archivo"]).resolve() for fila in conservadas}
    marca_resuelta = marca.resolve()
    for existente in raiz_curado.rglob("*"):
        if existente.is_file():
            resuelta = existente.resolve()
            if resuelta != marca_resuelta and resuelta not in esperados:
                existente.unlink()

    # Elimina las carpetas de clase que quedaron vacías tras el borrado,
    # de las más profundas a las más superficiales.
    carpetas = sorted(
        (p for p in raiz_curado.rglob("*") if p.is_dir()),
        key=lambda p: len(p.parts),
        reverse=True,
    )
    for carpeta in carpetas:
        if not any(carpeta.iterdir()):
            carpeta.rmdir()


def curar(
    raiz_crudo: Path,
    raiz_curado: Path,
    *,
    umbral: int = 3,
    hashes_externos: set[str] | None = None,
) -> dict:
    """Cura el dataset completo y devuelve el resumen de lo ocurrido."""
    raiz_crudo, raiz_curado = Path(raiz_crudo), Path(raiz_curado)
    filas = leer_manifiesto(raiz_crudo / "manifiesto.csv")
    con_hash = hashes_de(filas, raiz_crudo)
    conservadas, descartadas = deduplicar(
        con_hash, umbral=umbral, hashes_externos=hashes_externos
    )

    for fila in conservadas:
        destino = raiz_curado / fila["archivo"]
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raiz_crudo / fila["archivo"], destino)

    if raiz_curado.exists():
        _reconciliar_destino(raiz_curado, conservadas)

    _escribir_curado(conservadas, raiz_curado / NOMBRE_MANIFIESTO_CURADO)

    por_motivo: dict[str, int] = defaultdict(int)
    for fila in descartadas:
        por_motivo[fila["motivo"]] += 1
    por_clase: dict[str, int] = defaultdict(int)
    for fila in conservadas:
        por_clase[f"{fila['orden']}/{fila['familia'] or '_sin_familia'}"] += 1

    return {
        "entrada": len(filas),
        "conservadas": len(conservadas),
        "por_motivo": dict(por_motivo),
        "por_clase": dict(por_clase),
    }


def reporte_markdown(resumen: dict) -> str:
    entrada = resumen["entrada"]
    conservadas = resumen["conservadas"]
    factor = round(entrada / conservadas, 2) if conservadas else 0.0
    lineas = [
        "# Reporte de curación",
        "",
        f"- Imágenes de entrada: **{entrada}**",
        f"- Conservadas: **{conservadas}**",
        f"- Factor de curación real: **{factor}** "
        "(comparar con el 1.5 estimado en el censo y corregirlo si difiere).",
        "",
        "## Descartes por motivo",
        "",
        "| Motivo | Cantidad |",
        "| --- | ---: |",
    ]
    for motivo, cantidad in sorted(resumen["por_motivo"].items()):
        lineas.append(f"| {motivo} | {cantidad} |")

    lineas += ["", "## Imágenes conservadas por clase", "", "| Clase | Cantidad |", "| --- | ---: |"]
    for clase, cantidad in sorted(resumen["por_clase"].items()):
        lineas.append(f"| {clase} | {cantidad} |")
    return "\n".join(lineas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Curación del dataset descargado")
    parser.add_argument("--crudo", default="datos/crudo")
    parser.add_argument("--curado", default="datos/curado")
    parser.add_argument("--umbral", type=int, default=3)
    parser.add_argument(
        "--demo",
        default="",
        help="carpeta de imágenes de la demo, para no reutilizar sus fotos",
    )
    args = parser.parse_args()

    externos: set[str] = set()
    if args.demo:
        for ruta in Path(args.demo).rglob("*.jpg"):
            try:
                with Image.open(ruta) as img:
                    externos.add(imagenes.hash_perceptual(img.convert("RGB")))
            except Exception:
                continue
        print(f"{len(externos)} huellas externas cargadas de {args.demo}")

    resumen = curar(Path(args.crudo), Path(args.curado), umbral=args.umbral, hashes_externos=externos)
    Path("docs/reporte_curacion.md").write_text(reporte_markdown(resumen), encoding="utf-8")
    print(f"Curación: {resumen['conservadas']}/{resumen['entrada']} conservadas")


if __name__ == "__main__":
    main()
