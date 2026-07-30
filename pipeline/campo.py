"""Ingesta del conjunto de prueba de campo.

Estas fotos son la única medición honesta del sistema: nunca entran a
entrenamiento ni a validación. Se colocan a mano en
`datos/campo_crudo/<Orden>/<Familia>/` y este módulo las valida contra la
ontología y verifica que ninguna coincida con una imagen de entrenamiento.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from PIL import Image

from pipeline import imagenes
from pipeline.curacion import COLUMNAS_CURADO
from pipeline.ontologia import Ontologia, cargar_ontologia

SIN_FAMILIA = "_sin_familia"
EXTENSIONES = {".jpg", ".jpeg", ".png"}


def ingerir(raiz_campo: Path, onto: Ontologia) -> tuple[list[dict], list[str]]:
    """Recorre las carpetas y produce filas de manifiesto, o errores."""
    raiz_campo = Path(raiz_campo)
    ordenes = set(onto.nombres_ordenes())
    familias = set(onto.nombres_familias())
    filas: list[dict] = []
    errores: list[str] = []

    for ruta in sorted(raiz_campo.rglob("*")):
        if not ruta.is_file() or ruta.suffix.lower() not in EXTENSIONES:
            continue
        relativo = ruta.relative_to(raiz_campo)
        if len(relativo.parts) != 3:
            errores.append(
                f"{relativo}: se esperaba la estructura <Orden>/<Familia>/<archivo>"
            )
            continue

        orden, carpeta_familia, _ = relativo.parts
        if orden not in ordenes:
            errores.append(f"{relativo}: orden '{orden}' no existe en la ontología")
            continue

        familia = "" if carpeta_familia == SIN_FAMILIA else carpeta_familia
        if familia:
            if familia not in familias:
                errores.append(f"{relativo}: familia '{familia}' no existe en la ontología")
                continue
            if onto.orden_de_familia(familia) != orden:
                errores.append(f"{relativo}: familia '{familia}' no pertenece a '{orden}'")
                continue

        try:
            with Image.open(ruta) as img:
                huella = imagenes.hash_perceptual(img.convert("RGB"))
        except Exception:
            errores.append(f"{relativo}: archivo ilegible")
            continue

        fila = {c: "" for c in COLUMNAS_CURADO}
        fila.update(
            archivo=str(relativo).replace("\\", "/"),
            obs_id="",
            observador="campo",
            orden=orden,
            familia=familia,
            fuente="campo",
            hash=huella,
        )
        filas.append(fila)

    return filas, errores


def detectar_colisiones(
    filas_campo: list[dict], filas_train: list[dict], *, umbral: int = 3
) -> list[str]:
    """Avisa si una foto de campo coincide con una de entrenamiento."""
    indice: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for fila in filas_train:
        huella = fila.get("hash", "")
        if huella:
            for banda in imagenes.bandas(huella):
                indice[banda].append((huella, fila["archivo"]))

    colisiones: list[str] = []
    for fila in filas_campo:
        huella = fila.get("hash", "")
        if not huella:
            continue
        candidatas = {c for banda in imagenes.bandas(huella) for c in indice[banda]}
        for otra, archivo in candidatas:
            if imagenes.distancia(huella, otra) <= umbral:
                colisiones.append(
                    f"{fila['archivo']} coincide con la imagen de entrenamiento {archivo}"
                )
                break
    return colisiones


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta del conjunto de prueba de campo")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--campo", default="datos/campo_crudo")
    parser.add_argument("--train", default="datos/splits/train.csv")
    parser.add_argument("--salida", default="datos/splits/campo.csv")
    args = parser.parse_args()

    onto = cargar_ontologia(Path(args.ontologia))
    filas, errores = ingerir(Path(args.campo), onto)
    for error in errores:
        print(f"  ! {error}")

    ruta_train = Path(args.train)
    if ruta_train.exists():
        with ruta_train.open(encoding="utf-8", newline="") as f:
            colisiones = detectar_colisiones(filas, list(csv.DictReader(f)))
        for colision in colisiones:
            print(f"  !! COLISIÓN: {colision}")
        if colisiones:
            print(
                f"{len(colisiones)} fotos de campo también están en entrenamiento. "
                "Quitarlas antes de evaluar: invalidan la medición."
            )

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"{len(filas)} fotos de campo en {salida} ({len(errores)} descartadas)")


if __name__ == "__main__":
    main()
