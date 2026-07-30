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
#
# La marca solo cuenta si es un ARCHIVO REGULAR: en todo el módulo se
# comprueba con `.is_file()`, nunca con `.exists()`. Un directorio que por
# accidente (o por un descomprimido raro) se llame igual que la marca no
# debe confundirse con ella -si `.exists()` bastara, cualquier carpeta con
# ese nombre haría que `curar()` asumiera la propiedad total del directorio
# y reconciliara -es decir, borrara- contenido ajeno sin que hubiera existido
# ninguna corrida previa.
MARCA_DESTINO = ".curacion_destino"


class ErrorDestinoNoReconocido(Exception):
    """`raiz_curado` existe, tiene contenido y no es un destino de curación."""


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


def _verificar_destino(raiz_curado: Path) -> None:
    """Rechaza `raiz_curado` si existe, tiene contenido y no es propio.

    Se llama antes de marcar y antes de copiar nada. Sin esta comprobación,
    una primera corrida contra una carpeta ajena (p. ej. `--curado` escrito
    por error) no borraba nada -correcto-, pero SÍ la marcaba y copiaba
    imágenes ahí, dejándola lista para que una segunda corrida con la misma
    ruta equivocada la reconociera como propia y borrara el contenido del
    usuario. Basta con equivocarse dos veces con la misma ruta, algo
    plausible en una herramienta de línea de comandos. Rechazar de entrada,
    sin tocar nada, cierra esa ventana: un directorio ajeno con contenido
    nunca llega a marcarse.

    No aplica a los tres casos legítimos: destino inexistente, existente y
    vacío, o ya marcado por una corrida anterior. La marca solo cuenta si es
    un archivo regular (`.is_file()`, no `.exists()`): un directorio que por
    accidente se llame igual no es una marca válida, así que cae en la
    comprobación de contenido de más abajo y el destino se rechaza -es
    justamente el caso que se quiere atrapar-.
    """
    if not raiz_curado.exists():
        return
    if (raiz_curado / MARCA_DESTINO).is_file():
        return
    if any(raiz_curado.iterdir()):
        raise ErrorDestinoNoReconocido(
            f"'{raiz_curado}' ya existe, tiene contenido, y no parece un "
            f"destino de curación (no tiene la marca '{MARCA_DESTINO}' de una "
            "corrida anterior de curar()). Para no arriesgarse a borrar "
            "archivos ajenos por una ruta --curado mal escrita, curar() se "
            "detiene sin tocar nada. Usa una carpeta vacía o inexistente "
            "para --curado, o verifica que esta sea realmente la carpeta de "
            "una corrida de curación anterior."
        )


def _marcar_destino(raiz_curado: Path) -> None:
    """Crea la marca de propiedad de `raiz_curado` si todavía no existe.

    Se llama al principio de `curar`, antes de copiar nada, para que incluso
    una corrida que se interrumpe a mitad de camino deje el directorio
    identificado como propio: la siguiente corrida completa podrá
    reconciliar lo que esta alcanzó a copiar.

    En el flujo normal de `curar`, `_verificar_destino` ya descartó antes
    cualquier directorio-disfraz con ese nombre (cuenta como "contenido" y
    el destino se rechaza). Pero si algo distinto a un archivo regular
    ocupara esta ruta -por ejemplo, si se llamara a esta función fuera de
    ese flujo-, escribir ahí fallaría con una excepción cruda del sistema
    de archivos (`IsADirectoryError` en algunos sistemas, `PermissionError`
    en otros). Se comprueba explícitamente para fallar con un mensaje
    legible en su lugar.
    """
    marca = raiz_curado / MARCA_DESTINO
    if marca.is_file():
        return
    if marca.exists():
        raise ErrorDestinoNoReconocido(
            f"'{marca}' ya existe pero no es un archivo regular, así que no "
            f"puede usarse como marca de propiedad de '{raiz_curado}'. "
            "Elimina manualmente esa ruta -revisando antes que no sea nada "
            "importante- y vuelve a correr curar()."
        )
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

    ADVERTENCIA sobre el alcance del borrado: una vez que `raiz_curado` está
    legítimamente marcado, esta función borra TODO lo que no esté en
    `conservadas` (salvo el manifiesto y la marca) -incluido cualquier
    contenido ajeno que hubiera quedado ahí de antes, aunque no lo haya
    puesto `curar()`-. Esto es intencional, no un descuido: la marca
    significa "este directorio me pertenece por completo", no "reconcilia
    solo lo que yo mismo copié". `_verificar_destino` es la única barrera
    contra perder contenido ajeno, y actúa antes de marcar; una vez marcado,
    el directorio es del todo de `curar()`.
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
    """Cura el dataset completo y devuelve el resumen de lo ocurrido.

    Lanza `ErrorDestinoNoReconocido` si `raiz_curado` existe, tiene
    contenido y no lleva la marca de una corrida anterior -ver
    `_verificar_destino`-, sin escribir absolutamente nada en ese caso.
    """
    raiz_crudo, raiz_curado = Path(raiz_crudo), Path(raiz_curado)
    _verificar_destino(raiz_curado)

    # Se determina ANTES de tocar nada: si la marca ya estaba puesta, este
    # directorio es propio desde una corrida anterior -completa o
    # interrumpida- y es seguro reconciliarlo. Si no estaba, gracias a
    # `_verificar_destino` sabemos que el directorio no existía o estaba
    # vacío -nunca contenido ajeno-, así que esta primera corrida no tiene
    # nada que reconciliar; solo deja la marca puesta para que la siguiente
    # sí pueda.
    directorio_ya_propio = (raiz_curado / MARCA_DESTINO).is_file()
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
