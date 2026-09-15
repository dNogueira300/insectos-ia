"""Filtro de contenido: descarta fotos en las que no se ve el insecto.

La curación solo quita duplicados y archivos rotos. No mira qué hay en la
foto, y en iNaturalist una observación de insecto puede ser un nido, un
montículo, madera dañada o un paisaje: en una muestra de 30 fotos de una
familia de termitas, la mitad no mostraba ninguna. Entrenar con eso enseña al
modelo que "montículo de tierra" es una familia, y la precisión con fotos de
catálogo deja de decir nada sobre la foto de celular en campo.

Se usa un modelo de visión preentrenado en modo zero-shot: cada foto se
compara con descripciones de "insecto visible" y de "sin insecto", y el
puntaje es la probabilidad acumulada del primer grupo. Las descripciones son
genéricas a propósito: no nombran ninguna clase (ver
`test_ningun_modulo_escribe_nombres_de_clase_literales`), así que el filtro no
necesita cambiar si cambia la ontología.

No borra ni mueve imágenes, ni reescribe el manifiesto curado: escribe un
manifiesto filtrado aparte (que es el que consume `pipeline.splits`), el
detalle de lo descartado con su puntaje, y una caché de puntajes para poder
reajustar el umbral sin volver a pasar el modelo por todo el dataset.
"""
from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from PIL import Image

from pipeline.curacion import COLUMNAS_CURADO, NOMBRE_MANIFIESTO_CURADO

NOMBRE_MANIFIESTO_FILTRADO = "manifiesto_filtrado.csv"
NOMBRE_DESCARTES = "descartes_contenido.csv"
NOMBRE_PUNTAJES = "puntajes_contenido.csv"

MOTIVO_SIN_INSECTO = "sin_insecto"
MOTIVO_ILEGIBLE = "ilegible"

# Calibrado el 2026-09-14 con 360 fotos del dataset real, etiquetadas a mano
# como "se ve un insecto" o no. La muestra se cargó hacia las clases de riesgo:
# 49 no mostraban insecto, casi todas nidos y montículos de termitas.
#
#   umbral 0.10: atrapa el 73% de las malas y pierde el 2.3% de las buenas
#   umbral 0.30: atrapa el 78% de las malas y pierde el 4.2% de las buenas
#   umbral 0.50: atrapa el 88% de las malas y pierde el 5.5% de las buenas
#   umbral 0.70: atrapa el 94% de las malas y pierde el 7.4% de las buenas
#
# Se elige 0.5. Las buenas que se pierden son sobre todo colonias, insectos
# dentro de galerías de madera o sobre tallos cubiertos; el modelo final
# tampoco aprende bien de ellas. El descarte fue una decisión del proyecto
# sin revisión humana: preferir perder algunas fotos buenas a entrenar con
# nidos etiquetados como familias.
UMBRAL = 0.5

DESCRIPCIONES_INSECTO = (
    "a photo of an insect",
    "a close-up photo of a small insect",
    "a macro photo of an insect on a leaf",
    "a photo of insects on the ground",
    "a photo of an insect on a person's hand",
)
DESCRIPCIONES_SIN_INSECTO = (
    "a photo of an insect nest or a mound of soil",
    "a photo of a landscape",
    "a photo of damaged wood",
    "a photo of a damaged leaf",
    "a photo of bare soil",
    "a photo of a tree trunk",
    "a photo of a plant",
)

# Recibe imágenes RGB y devuelve, para cada una, la probabilidad de que se vea
# un insecto (0 a 1).
Clasificador = Callable[[list[Image.Image]], list[float]]


def puntuar(
    filas: list[dict],
    raiz: Path,
    clasificador: Clasificador,
    *,
    lote: int = 64,
    previos: dict[str, float | None] | None = None,
    al_avanzar: Callable[[dict[str, float | None]], None] | None = None,
) -> dict[str, float | None]:
    """Puntaje por archivo. `None` marca una imagen que no se pudo abrir.

    Los archivos presentes en `previos` no se vuelven a clasificar.
    `al_avanzar` recibe los puntajes acumulados después de cada lote, para
    persistir el progreso de una pasada que dura decenas de minutos.
    """
    raiz = Path(raiz)
    puntajes: dict[str, float | None] = dict(previos or {})
    pendientes = [f["archivo"] for f in filas if f["archivo"] not in puntajes]

    for inicio in range(0, len(pendientes), lote):
        legibles: list[tuple[str, Image.Image]] = []
        for archivo in pendientes[inicio : inicio + lote]:
            try:
                with Image.open(raiz / archivo) as img:
                    legibles.append((archivo, img.convert("RGB")))
            except Exception:
                puntajes[archivo] = None
        if legibles:
            valores = clasificador([img for _, img in legibles])
            for (archivo, _), valor in zip(legibles, valores, strict=True):
                puntajes[archivo] = float(valor)
        if al_avanzar is not None:
            al_avanzar(puntajes)
    return puntajes


def filtrar(
    filas: list[dict], puntajes: dict[str, float | None], *, umbral: float
) -> tuple[list[dict], list[dict]]:
    """Conserva las filas con puntaje >= umbral; el resto sale con su motivo."""
    conservadas: list[dict] = []
    descartadas: list[dict] = []
    for fila in filas:
        puntaje = puntajes.get(fila["archivo"])
        if puntaje is None:
            descartadas.append(dict(fila, motivo=MOTIVO_ILEGIBLE, puntaje=""))
        elif puntaje >= umbral:
            conservadas.append(fila)
        else:
            descartadas.append(dict(fila, motivo=MOTIVO_SIN_INSECTO, puntaje=puntaje))
    return conservadas, descartadas


def _escribir_csv(ruta: Path, filas: list[dict], columnas: list[str]) -> None:
    """Escritura atómica, mismo patrón que el resto del pipeline."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(f".{ruta.name}.tmp-{os.getpid()}")
    try:
        with temporal.open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
            escritor.writeheader()
            escritor.writerows(filas)
        os.replace(temporal, ruta)
    except Exception:
        temporal.unlink(missing_ok=True)
        raise


def _leer_puntajes(ruta: Path) -> dict[str, float | None]:
    if not ruta.is_file():
        return {}
    with ruta.open(encoding="utf-8", newline="") as f:
        return {
            fila["archivo"]: (float(fila["puntaje"]) if fila["puntaje"] else None)
            for fila in csv.DictReader(f)
        }


def _escribir_puntajes(ruta: Path, puntajes: dict[str, float | None]) -> None:
    filas = [
        {"archivo": archivo, "puntaje": "" if valor is None else f"{valor:.4f}"}
        for archivo, valor in sorted(puntajes.items())
    ]
    _escribir_csv(ruta, filas, ["archivo", "puntaje"])


def ejecutar(
    raiz_curado: Path,
    clasificador: Clasificador,
    *,
    umbral: float = UMBRAL,
    lote: int = 64,
    informar: Callable[[int, int], None] | None = None,
) -> dict:
    """Filtra el manifiesto curado de `raiz_curado`.

    `informar(hechas, total)` se llama tras cada lote clasificado, contando
    también lo que ya estaba en la caché: una pasada de decenas de minutos sin
    ninguna salida parece colgada.
    """
    raiz_curado = Path(raiz_curado)
    with (raiz_curado / NOMBRE_MANIFIESTO_CURADO).open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))

    ruta_puntajes = raiz_curado / NOMBRE_PUNTAJES
    archivos = [f["archivo"] for f in filas]

    def _al_avanzar(parciales: dict[str, float | None]) -> None:
        _escribir_puntajes(ruta_puntajes, parciales)
        if informar is not None:
            informar(sum(1 for a in archivos if a in parciales), len(archivos))

    puntajes = puntuar(
        filas, raiz_curado, clasificador, lote=lote,
        previos=_leer_puntajes(ruta_puntajes),
        al_avanzar=_al_avanzar,
    )
    _escribir_puntajes(ruta_puntajes, puntajes)

    conservadas, descartadas = filtrar(filas, puntajes, umbral=umbral)
    _escribir_csv(raiz_curado / NOMBRE_MANIFIESTO_FILTRADO, conservadas, list(COLUMNAS_CURADO))
    _escribir_csv(
        raiz_curado / NOMBRE_DESCARTES, descartadas, [*COLUMNAS_CURADO, "motivo", "puntaje"]
    )

    por_clase: dict[str, dict[str, int]] = defaultdict(lambda: {"entrada": 0, "descartadas": 0})
    for fila in filas:
        por_clase[_clase(fila)]["entrada"] += 1
    for fila in descartadas:
        por_clase[_clase(fila)]["descartadas"] += 1
    return {
        "entrada": len(filas),
        "conservadas": len(conservadas),
        "umbral": umbral,
        "por_clase": dict(por_clase),
    }


def _clase(fila: dict) -> str:
    return f"{fila['orden']}/{fila['familia'] or '_sin_familia'}"


def reporte_markdown(resumen: dict) -> str:
    lineas = [
        "# Reporte del filtro de contenido",
        "",
        f"- Imágenes de entrada: **{resumen['entrada']}**",
        f"- Conservadas: **{resumen['conservadas']}**",
        f"- Umbral de puntaje: **{resumen['umbral']}**",
        "",
        "El puntaje es la probabilidad, según un modelo de visión zero-shot, de que "
        "la foto muestre un insecto visible. Lo descartado queda listado con su "
        f"puntaje en `{NOMBRE_DESCARTES}`; las imágenes no se borran.",
        "",
        "| Clase | Entrada | Descartadas | % |",
        "| --- | ---: | ---: | ---: |",
    ]
    for clase, datos in sorted(resumen["por_clase"].items()):
        porcentaje = round(100 * datos["descartadas"] / datos["entrada"]) if datos["entrada"] else 0
        lineas.append(f"| {clase} | {datos['entrada']} | {datos['descartadas']} | {porcentaje}% |")
    return "\n".join(lineas) + "\n"


def clasificador_clip(modelo: str = "ViT-B-32", pesos: str = "laion2b_s34b_b79k") -> Clasificador:
    """Clasificador zero-shot con open_clip, en CPU.

    Se importa aquí dentro para que el resto del pipeline (y sus pruebas) no
    dependa de torch.
    """
    import open_clip
    import torch

    torch.set_grad_enabled(False)
    red, _, preprocesar = open_clip.create_model_and_transforms(modelo, pretrained=pesos)
    red.eval()
    tokens = open_clip.get_tokenizer(modelo)(
        [*DESCRIPCIONES_INSECTO, *DESCRIPCIONES_SIN_INSECTO]
    )
    textos = red.encode_text(tokens)
    textos = textos / textos.norm(dim=-1, keepdim=True)
    n_insecto = len(DESCRIPCIONES_INSECTO)

    def clasificar(imagenes: list[Image.Image]) -> list[float]:
        lote = torch.stack([preprocesar(img) for img in imagenes])
        vistas = red.encode_image(lote)
        vistas = vistas / vistas.norm(dim=-1, keepdim=True)
        probs = (100.0 * vistas @ textos.T).softmax(dim=-1)
        return probs[:, :n_insecto].sum(dim=-1).tolist()

    return clasificar


def main() -> None:
    parser = argparse.ArgumentParser(description="Filtro de fotos sin insecto visible")
    parser.add_argument("--curado", default="datos/curado")
    parser.add_argument("--umbral", type=float, default=UMBRAL)
    parser.add_argument("--reporte", default="docs/reporte_filtro_contenido.md")
    args = parser.parse_args()

    print("Cargando el modelo de visión...", flush=True)
    clasificador = clasificador_clip()

    def _informar(hechas: int, total: int) -> None:
        print(f"  {hechas}/{total} imágenes puntuadas ({100 * hechas // total}%)", end="\r", flush=True)

    resumen = ejecutar(Path(args.curado), clasificador, umbral=args.umbral, informar=_informar)
    print()
    Path(args.reporte).write_text(reporte_markdown(resumen), encoding="utf-8")
    print(f"Filtro de contenido: {resumen['conservadas']}/{resumen['entrada']} conservadas")


if __name__ == "__main__":
    main()
