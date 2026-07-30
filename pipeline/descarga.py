"""Descarga masiva de imágenes con manifiesto de trazabilidad.

El manifiesto es la pieza central del pipeline: arrastra observación,
observador y licencia hasta los splits. Sin él no se puede agrupar por
observador (Tarea 7) ni atribuir las fotos.
"""
from __future__ import annotations

import argparse
import csv
import logging
import time
from pathlib import Path

from pipeline import imagenes, inat
from pipeline.inat import iterar_observaciones
from pipeline.ontologia import Ontologia, cargar_ontologia

_log = logging.getLogger(__name__)

COLUMNAS_MANIFIESTO = (
    "archivo",
    "obs_id",
    "observador",
    "orden",
    "familia",
    "taxon_nombre",
    "rango",
    "licencia",
    "atribucion",
    "latitud",
    "longitud",
    "fecha",
    "url",
    "fuente",
)

# Códigos de licencia de iNaturalist que permiten uso y redistribución con
# atribución. Una licencia vacía significa "todos los derechos reservados".
LICENCIAS_PERMITIDAS = frozenset(
    {"cc0", "cc-by", "cc-by-nc", "cc-by-sa", "cc-by-nc-sa", "cc-by-nd", "cc-by-nc-nd"}
)

# Carpeta donde caen las imágenes de la cuota de orden, cuya familia se
# desconoce (o cuyo taxón identificado no llega a nivel de familia).
SIN_FAMILIA = "_sin_familia"


def leer_manifiesto(ruta: Path) -> list[dict]:
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def escribir_manifiesto(filas: list[dict], ruta: Path) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_MANIFIESTO))
        escritor.writeheader()
        escritor.writerows(filas)


def descargar_clase(
    orden: str,
    familia: str,
    taxon_id: int,
    *,
    cupo: int,
    raiz: Path,
    ya_descargados: set[int],
    sesion_api,
    sesion_img,
    pausa: float = inat.PAUSA_SEGUNDOS,
) -> list[dict]:
    """Descarga hasta `cupo` imágenes nuevas para una clase.

    Se pide un margen de `cupo * 3` observaciones al iterador porque se
    descartan las ya vistas, las de licencia no permitida y las de imagen
    inservible. Si aun con ese margen no se alcanza el cupo, no se falla en
    silencio: se deja constancia en el log de cuánto faltó y por qué se
    descartó cada observación, junto con una pista de si el margen se agotó
    (la fuente tenía observaciones de sobra pero se descartaron demasiadas)
    o si la fuente simplemente no tenía más observaciones que ofrecer. Sin
    ese aviso, una corrida de horas podría dejar una clase corta sin que
    nadie lo note hasta que la regla de admisión posterior la descarte.
    """
    carpeta = familia or SIN_FAMILIA
    filas: list[dict] = []
    vistas = 0
    descartes_repetida = 0
    descartes_licencia = 0
    descartes_imagen = 0

    for observacion in iterar_observaciones(
        taxon_id, limite=cupo * 3, sesion=sesion_api, pausa=pausa
    ):
        if len(filas) >= cupo:
            break
        vistas += 1
        if observacion.id in ya_descargados:
            descartes_repetida += 1
            continue
        if observacion.licencia not in LICENCIAS_PERMITIDAS:
            descartes_licencia += 1
            continue

        img = imagenes.descargar_imagen(observacion.foto_url, sesion=sesion_img)
        if img is None:
            descartes_imagen += 1
            continue

        relativo = f"{orden}/{carpeta}/{observacion.id}.jpg"
        imagenes.guardar_jpeg(imagenes.normalizar(img), Path(raiz) / relativo)
        ya_descargados.add(observacion.id)
        filas.append(
            {
                "archivo": relativo,
                "obs_id": observacion.id,
                "observador": observacion.observador,
                "orden": orden,
                "familia": familia,
                "taxon_nombre": observacion.taxon_nombre,
                "rango": observacion.rango,
                "licencia": observacion.licencia,
                "atribucion": observacion.atribucion,
                "latitud": observacion.latitud if observacion.latitud is not None else "",
                "longitud": observacion.longitud if observacion.longitud is not None else "",
                "fecha": observacion.fecha,
                "url": observacion.foto_url,
                "fuente": "iNaturalist",
            }
        )
        if pausa:
            time.sleep(pausa * 0.15)

    if len(filas) < cupo:
        # `vistas` llega a cupo * 3 solo si el iterador tenía tanto material
        # como se le pidió; si se quedó corto, la causa es la propia fuente,
        # no el margen de 3x.
        margen_insuficiente = vistas >= cupo * 3
        motivo = (
            "el margen de 3x no alcanzó (demasiados descartes)"
            if margen_insuficiente
            else "la fuente no tenía más observaciones que ofrecer"
        )
        _log.warning(
            "%s/%s: cupo no alcanzado (%d de %d). %s. "
            "observaciones vistas=%d, descartadas por ya_descargada=%d, "
            "licencia_no_permitida=%d, imagen_inservible=%d",
            orden, carpeta, len(filas), cupo, motivo,
            vistas, descartes_repetida, descartes_licencia, descartes_imagen,
        )
    return filas


def descargar_todo(
    onto: Ontologia,
    *,
    raiz: Path,
    cupo_orden: int,
    cupo_familia: int,
    sesion_api=None,
    sesion_img=None,
) -> list[dict]:
    """Descarga la cuota de cada orden y de cada familia declarada.

    La reanudación es por `obs_id`: si el manifiesto ya existente en `raiz`
    lo tiene, se salta. Así una corrida interrumpida se retoma sin volver a
    bajar nada. El manifiesto se reescribe después de cada clase, para no
    perder lo ya bajado si la corrida se corta a mitad de camino.
    """
    sesion_api = sesion_api or inat.nueva_sesion()
    sesion_img = sesion_img or inat.nueva_sesion()
    raiz = Path(raiz)

    manifiesto = leer_manifiesto(raiz / "manifiesto.csv")
    ya = {int(f["obs_id"]) for f in manifiesto if f.get("obs_id")}

    for orden in sorted(onto.ordenes, key=lambda o: o.nombre):
        print(f"[{orden.nombre}] cuota de orden (cupo {cupo_orden})...")
        nuevas = descargar_clase(
            orden.nombre, "", orden.inat_taxon_id,
            cupo=cupo_orden, raiz=raiz, ya_descargados=ya,
            sesion_api=sesion_api, sesion_img=sesion_img,
        )
        manifiesto += nuevas
        escribir_manifiesto(manifiesto, raiz / "manifiesto.csv")
        print(f"  +{len(nuevas)} imágenes")

        for fam in sorted(orden.familias, key=lambda f: f.nombre):
            print(f"[{orden.nombre}/{fam.nombre}] (cupo {cupo_familia})...")
            nuevas = descargar_clase(
                orden.nombre, fam.nombre, fam.inat_taxon_id,
                cupo=cupo_familia, raiz=raiz, ya_descargados=ya,
                sesion_api=sesion_api, sesion_img=sesion_img,
            )
            manifiesto += nuevas
            escribir_manifiesto(manifiesto, raiz / "manifiesto.csv")
            print(f"  +{len(nuevas)} imágenes")

    return manifiesto


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga de imágenes por clase")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--raiz", default="datos/crudo")
    parser.add_argument("--cupo-orden", type=int, default=1200)
    parser.add_argument("--cupo-familia", type=int, default=600)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    onto = cargar_ontologia(Path(args.ontologia))
    manifiesto = descargar_todo(
        onto,
        raiz=Path(args.raiz),
        cupo_orden=args.cupo_orden,
        cupo_familia=args.cupo_familia,
    )
    print(f"Manifiesto con {len(manifiesto)} imágenes en {args.raiz}/manifiesto.csv")


if __name__ == "__main__":
    main()
