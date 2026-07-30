"""Ingesta del conjunto de prueba de campo.

Estas fotos son la única medición honesta del sistema: nunca entran a
entrenamiento ni a validación. Se colocan a mano en
`datos/campo_crudo/<Orden>/<Familia>/` y este módulo las valida contra la
ontología y verifica que ninguna coincida con una imagen de entrenamiento.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

from pipeline import imagenes
from pipeline.curacion import COLUMNAS_CURADO
from pipeline.ontologia import Ontologia, cargar_ontologia

SIN_FAMILIA = "_sin_familia"

# Los tres splits contra los que hay que comprobar toda foto de campo. El
# diseño (§7) dice que estas fotos "nunca entran a entrenamiento ni a
# validación"; comprobar solo contra `train` dejaba pasar dos tercios del
# riesgo, y una foto de campo que ya está en validación invalida por igual la
# comparación entre la métrica de validación y la de campo, que es
# precisamente el resultado que el informe debe explicar.
SPLITS_DE_REFERENCIA = ("train", "val", "test")

# Códigos de salida del módulo, pensados para encadenar `campo.py` en un
# script: cualquier valor distinto de cero significa que el conjunto de campo
# resultante no es de fiar, o directamente no se produjo.
SALIDA_OK = 0
SALIDA_COLISIONES = 1  # hay fotos de campo que también están en los splits
SALIDA_RECHAZOS = 2  # se entregaron archivos que no pudieron ingerirse
SALIDA_FALTA_REFERENCIA = 3  # no se pudo verificar la fuga: no se escribe nada


class ErrorReferencias(Exception):
    """Faltan los splits contra los que verificar la fuga."""
# WEBP se acepta porque Pillow lo decodifica de forma nativa, sin depender de
# ningún complemento adicional. HEIC (el formato por defecto de iPhone desde
# iOS 11) queda deliberadamente fuera: Pillow no lo lee sin un plugin externo,
# y no se añaden dependencias nuevas en esta ronda. Una foto en ese formato
# debe convertirse antes de entregarse, y por eso produce un error explícito
# más abajo en vez de desaparecer en silencio.
EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp"}

# Archivos que el propio sistema operativo siembra en las carpetas (miniaturas
# de Windows, metadatos de macOS) sin que nadie los haya "entregado": no son
# fotos y se ignoran sin generar error. Los ocultos (que empiezan por punto,
# como .DS_Store o un .gitkeep de control de versiones) quedan cubiertos por
# la segunda condición de `_es_metadato_de_sistema`.
NOMBRES_IGNORADOS = {"thumbs.db", ".ds_store"}


def _es_metadato_de_sistema(ruta: Path) -> bool:
    """True si el archivo es basura del sistema operativo, no una entrega."""
    return ruta.name.lower() in NOMBRES_IGNORADOS or ruta.name.startswith(".")


def ingerir(raiz_campo: Path, onto: Ontologia) -> tuple[list[dict], list[str]]:
    """Recorre las carpetas y produce filas de manifiesto, o errores.

    Ningún archivo entregado desaparece sin dejar constancia: una extensión
    no reconocida (p. ej. .heic de iPhone o .webp mal escrito) se reporta
    como error explícito en vez de omitirse en silencio, porque el conjunto
    de campo es la única medición honesta del sistema y perder fotos sin
    que nadie se entere invalidaría esa medición sin avisar.
    """
    raiz_campo = Path(raiz_campo)
    ordenes = set(onto.nombres_ordenes())
    familias = set(onto.nombres_familias())
    filas: list[dict] = []
    errores: list[str] = []

    for ruta in sorted(raiz_campo.rglob("*")):
        if not ruta.is_file() or _es_metadato_de_sistema(ruta):
            continue
        relativo = ruta.relative_to(raiz_campo)
        if len(relativo.parts) != 3:
            errores.append(
                f"{relativo}: se esperaba la estructura <Orden>/<Familia>/<archivo>"
            )
            continue

        if ruta.suffix.lower() not in EXTENSIONES:
            formatos = ", ".join(sorted(EXTENSIONES))
            errores.append(
                f"{relativo}: extensión '{ruta.suffix}' no reconocida; "
                f"convertir a uno de estos formatos antes de ingerir: {formatos}"
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


def cargar_referencias(directorio_splits: Path) -> dict[str, list[dict]]:
    """Lee los tres splits contra los que se verifica la fuga.

    Si falta alguno lanza `ErrorReferencias` en vez de devolver lo que haya.
    La verificación anti-fuga es el único guardián del conjunto de campo -"la
    única medición honesta del sistema", según el diseño-, así que no puede
    fallar en abierto: un `--splits` con un typo, o correr este módulo antes
    que `splits.py`, tiene que ser un error ruidoso y no una corrida que
    informa éxito sin haber comprobado nada.
    """
    directorio_splits = Path(directorio_splits)
    faltantes = [
        split
        for split in SPLITS_DE_REFERENCIA
        if not (directorio_splits / f"{split}.csv").is_file()
    ]
    if faltantes:
        nombres = ", ".join(f"{s}.csv" for s in faltantes)
        raise ErrorReferencias(
            f"no se puede verificar la fuga: falta(n) {nombres} en {directorio_splits}. "
            "Ejecutar primero pipeline/splits.py, o corregir --splits."
        )

    referencias: dict[str, list[dict]] = {}
    for split in SPLITS_DE_REFERENCIA:
        with (directorio_splits / f"{split}.csv").open(encoding="utf-8", newline="") as f:
            referencias[split] = list(csv.DictReader(f))
    return referencias


def detectar_colisiones(
    filas_campo: list[dict],
    filas_referencia: list[dict],
    *,
    umbral: int = 3,
    etiqueta: str = "entrenamiento",
) -> list[str]:
    """Avisa si una foto de campo coincide con una del split de referencia."""
    indice: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for fila in filas_referencia:
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
                    f"{fila['archivo']} coincide con la imagen de {etiqueta} {archivo}"
                )
                break
    return colisiones


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada. Devuelve el código de salida (ver constantes `SALIDA_*`)."""
    parser = argparse.ArgumentParser(description="Ingesta del conjunto de prueba de campo")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--campo", default="datos/campo_crudo")
    parser.add_argument(
        "--splits",
        default="datos/splits",
        help="directorio con train.csv, val.csv y test.csv; los tres son obligatorios",
    )
    parser.add_argument("--salida", default=None, help="por defecto <splits>/campo.csv")
    args = parser.parse_args(argv)

    onto = cargar_ontologia(Path(args.ontologia))
    filas, errores = ingerir(Path(args.campo), onto)
    for error in errores:
        print(f"  ! {error}")

    # La verificación va ANTES de escribir nada: si no se puede comprobar la
    # fuga, no se produce un conjunto de campo que alguien pueda usar creyendo
    # que fue verificado.
    try:
        referencias = cargar_referencias(Path(args.splits))
    except ErrorReferencias as error:
        print(f"  !! ERROR: {error}")
        print("No se escribió campo.csv.")
        return SALIDA_FALTA_REFERENCIA

    colisiones: list[str] = []
    for split, filas_split in referencias.items():
        colisiones += detectar_colisiones(filas, filas_split, etiqueta=split)
    for colision in colisiones:
        print(f"  !! COLISIÓN: {colision}")
    if colisiones:
        print(
            f"{len(colisiones)} coincidencias entre fotos de campo y los splits "
            f"({', '.join(SPLITS_DE_REFERENCIA)}). Quitarlas antes de evaluar: "
            "invalidan la medición."
        )

    salida = Path(args.salida) if args.salida else Path(args.splits) / "campo.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"{len(filas)} fotos de campo en {salida} ({len(errores)} descartadas)")

    # Las colisiones pesan más que los rechazos: un rechazo deja fotos fuera,
    # una colisión contamina las que sí entraron.
    if colisiones:
        return SALIDA_COLISIONES
    if errores:
        return SALIDA_RECHAZOS
    return SALIDA_OK


if __name__ == "__main__":
    sys.exit(main())
