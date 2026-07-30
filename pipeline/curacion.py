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

# Nombre del manifiesto que `curar` escribe en `raiz_curado`.
NOMBRE_MANIFIESTO_CURADO = "manifiesto_curado.csv"

# Archivo centinela que marca `raiz_curado` como un directorio administrado
# por `curar()`. A diferencia del manifiesto, se escribe al INICIO de la
# corrida, antes de copiar nada: una descarga y curación real dura horas y
# es justo el tipo de proceso que se interrumpe a mitad de camino, o al que
# alguien le borra el manifiesto a mano entre corridas. Si la marca dependiera
# del manifiesto (que se escribe al final), cualquiera de esos dos casos
# dejaría el directorio sin identificar y la siguiente corrida no
# reconciliaría los archivos huérfanos. Ver `_marcar_destino` y `curar`.
# No es basura: no borrar.
MARCA_DESTINO = ".curacion_destino"


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


def _marcar_destino(raiz_curado: Path) -> None:
    """Crea la marca de propiedad de `raiz_curado` si todavía no existe.

    Se llama al principio de `curar`, antes de copiar nada, para que incluso
    una corrida que se interrumpe a mitad de camino deje el directorio
    identificado como propio: la siguiente corrida completa podrá
    reconciliar lo que esta alcanzó a copiar.
    """
    marca = raiz_curado / MARCA_DESTINO
    if marca.exists():
        return
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(
        "Este directorio es administrado por pipeline.curacion.curar().\n"
        "No borrar este archivo: sin él, curar() no puede distinguir este\n"
        "directorio de una carpeta ajena y deja de reconciliar archivos\n"
        "huerfanos entre corridas, para no arriesgarse a borrar algo que no\n"
        "puso.\n",
        encoding="utf-8",
    )


def _reconciliar_destino(raiz_curado: Path, conservadas: list[dict]) -> None:
    """Deja en `raiz_curado` solo los archivos listados en `conservadas`.

    Una corrida anterior pudo haber copiado imágenes que esta corrida ya no
    conserva -por ejemplo, si el manifiesto de origen cambió entre medio, o
    si una corrida previa murió a mitad de la copia-. Sin esto esos archivos
    quedarían huérfanos: sin fila que los respalde en el CSV, pero visibles
    para cualquier cargador que liste carpetas directamente en vez de leer
    el manifiesto (así funcionan los `ImageFolder` típicos), coleándose al
    entrenamiento sin trazabilidad, sin licencia y sin haber pasado por el
    particionado por observador de la Tarea 7.

    Quien llama (`curar`) decide cuándo invocar esta función: solo cuando
    `raiz_curado` ya era, antes de esta corrida, un directorio propio (ver
    `MARCA_DESTINO` y `_marcar_destino`). No se repite esa comprobación aquí
    porque para este punto `_marcar_destino` ya escribió la marca de esta
    misma corrida, y comprobar su existencia ahora siempre daría verdadero.
    """
    protegidos = {
        (raiz_curado / NOMBRE_MANIFIESTO_CURADO).resolve(),
        (raiz_curado / MARCA_DESTINO).resolve(),
    }
    esperados = {(raiz_curado / fila["archivo"]).resolve() for fila in conservadas}
    for existente in raiz_curado.rglob("*"):
        if existente.is_file():
            resuelta = existente.resolve()
            if resuelta not in protegidos and resuelta not in esperados:
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

    # Se determina ANTES de tocar nada: si la marca ya estaba puesta, este
    # directorio es propio desde una corrida anterior -completa o
    # interrumpida- y es seguro reconciliarlo. Si no estaba, no hay forma de
    # saber si el contenido preexistente es ajeno, así que esta corrida no
    # borra nada -aunque sí deja la marca puesta para que la siguiente sí
    # pueda-.
    directorio_ya_propio = (raiz_curado / MARCA_DESTINO).exists()
    _marcar_destino(raiz_curado)

    filas = leer_manifiesto(raiz_crudo / "manifiesto.csv")
    con_hash = hashes_de(filas, raiz_crudo)
    conservadas, descartadas = deduplicar(
        con_hash, umbral=umbral, hashes_externos=hashes_externos
    )

    for fila in conservadas:
        destino = raiz_curado / fila["archivo"]
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raiz_crudo / fila["archivo"], destino)

    if directorio_ya_propio:
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
