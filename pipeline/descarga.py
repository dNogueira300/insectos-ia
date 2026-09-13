"""Descarga masiva de imágenes con manifiesto de trazabilidad.

El manifiesto es la pieza central del pipeline: arrastra observación,
observador y licencia hasta los splits. Sin él no se puede agrupar por
observador (Tarea 7) ni atribuir las fotos.
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
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

# Cada cuántas imágenes NUEVAS, dentro de una misma clase, se vuelca el
# manifiesto completo a disco (además del volcado al terminar la clase).
# 25 acota lo que se repetiría al reanudar tras un corte a menos del 4% de
# la cuota más chica (600, la de familia) sin multiplicar en exceso las
# reescrituras completas del archivo, que crecen con el tamaño total del
# manifiesto: un valor mucho más chico paga esa reescritura completa muchas
# más veces de las necesarias; uno mucho más grande deja de proteger nada.
INTERVALO_PERSISTENCIA_MANIFIESTO = 25


def leer_manifiesto(ruta: Path) -> list[dict]:
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def escribir_manifiesto(filas: list[dict], ruta: Path) -> None:
    """Escribe el manifiesto de forma atómica.

    Nunca trunca `ruta` directamente: arma el CSV completo en un archivo
    temporal junto al destino y lo reemplaza con `os.replace` solo cuando la
    escritura terminó sin fallos (mismo patrón que `importar()` en
    `pipeline/bd.py`). `descargar_todo` llama a esta función una y otra vez
    sobre el manifiesto completo y creciente, así que sin esta protección
    una interrupción a mitad de una reescritura no solo perdería las filas
    nuevas: truncaría también las que ya estaban a salvo en disco.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta_temporal = ruta.with_name(f".{ruta.name}.tmp-{os.getpid()}")
    ruta_temporal.unlink(missing_ok=True)  # restos de una corrida anterior interrumpida

    try:
        with ruta_temporal.open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_MANIFIESTO))
            escritor.writeheader()
            escritor.writerows(filas)
        os.replace(ruta_temporal, ruta)
    except Exception:
        ruta_temporal.unlink(missing_ok=True)
        raise


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
    manifiesto_previo: list[dict] = (),
    intervalo_persistencia: int = INTERVALO_PERSISTENCIA_MANIFIESTO,
    solo_adultos: bool = True,
    excluir_taxon_ids: tuple[int, ...] = (),
) -> list[dict]:
    """Descarga hasta `cupo` imágenes nuevas para una clase.

    Se admite un margen de `cupo * 3` observaciones NUEVAS porque se
    descartan las de licencia no permitida y las de imagen inservible. Las ya
    descargadas no cuentan contra ese margen: la cuota de orden corre después
    de sus familias y pagina desde las mismas observaciones antiguas que ellas
    ya se llevaron, así que contarlas dejaba al orden corto con la fuente
    llena (medido en un simulacro: 1099 de 1200 en un orden con seis familias). Si aun con ese margen no se alcanza el cupo, no se falla en
    silencio: se deja constancia en el log de cuánto faltó y por qué se
    descartó cada observación, junto con una pista de si el margen se agotó
    (la fuente tenía observaciones de sobra pero se descartaron demasiadas)
    o si la fuente simplemente no tenía más observaciones que ofrecer. Sin
    ese aviso, una corrida de horas podría dejar una clase corta sin que
    nadie lo note hasta que la regla de admisión posterior la descarte.

    La unidad de confirmación en el manifiesto no es la clase completa: cada
    `intervalo_persistencia` imágenes nuevas se vuelca a disco el manifiesto
    acumulado (`manifiesto_previo` más lo bajado hasta ese punto). Sin esto,
    un corte a mitad de una clase con cupo alto (hasta 1200) dejaría en disco
    archivos `.jpg` sin fila correspondiente: no contaminan el dataset -la
    curación solo copia lo que figura en el manifiesto-, pero al reanudar
    `ya_descargados` no los reconoce y la corrida los vuelve a bajar de la
    red, tirando ese trabajo.
    """
    carpeta = familia or SIN_FAMILIA
    ruta_manifiesto = Path(raiz) / "manifiesto.csv"
    margen = cupo * 3
    filas: list[dict] = []
    vistas = 0
    vistas_nuevas = 0
    descartes_repetida = 0
    descartes_licencia = 0
    descartes_imagen = 0

    # El límite del iterador solo acota la paginación: el corte real lo deciden
    # el cupo y el margen de observaciones nuevas, dentro del bucle.
    for observacion in iterar_observaciones(
        taxon_id, limite=margen + len(ya_descargados), sesion=sesion_api, pausa=pausa,
        solo_adultos=solo_adultos, excluir_taxon_ids=excluir_taxon_ids,
    ):
        if len(filas) >= cupo or vistas_nuevas >= margen:
            break
        vistas += 1
        if observacion.id in ya_descargados:
            descartes_repetida += 1
            continue
        vistas_nuevas += 1
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
        if intervalo_persistencia and len(filas) % intervalo_persistencia == 0:
            escribir_manifiesto(list(manifiesto_previo) + filas, ruta_manifiesto)
        if pausa:
            time.sleep(pausa * 0.15)

    if len(filas) < cupo:
        # Las nuevas llegan al margen solo si la fuente tenía tanto material
        # como se le pidió; si se quedó corta, la causa es la propia fuente,
        # no el margen de 3x.
        margen_insuficiente = vistas_nuevas >= margen
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
    """Descarga la cuota de cada familia declarada y, después, la de cada orden.

    Las familias van primero a propósito: ver el comentario extenso dentro
    del bucle. Invertirlo hace que la cuota de orden se coma las etiquetas
    de familia.

    La reanudación es por `obs_id`: si el manifiesto ya existente en `raiz`
    lo tiene, se salta. Además, los cupos son el TOTAL por clase, no lo nuevo
    de cada corrida: se descuenta lo que el manifiesto ya tiene de esa clase,
    y una clase completa ni siquiera se consulta. Sin ese descuento, cada
    relanzamiento de una descarga hecha por partes volvía a pedir el cupo
    entero y la clase crecía por encima de él. Así una corrida interrumpida se retoma sin volver a
    bajar nada. El manifiesto se reescribe después de cada clase, para no
    perder lo ya bajado si la corrida se corta a mitad de camino.
    """
    sesion_api = sesion_api or inat.nueva_sesion()
    sesion_img = sesion_img or inat.nueva_sesion()
    raiz = Path(raiz)

    manifiesto = leer_manifiesto(raiz / "manifiesto.csv")
    ya = {int(f["obs_id"]) for f in manifiesto if f.get("obs_id")}
    existentes: dict[tuple[str, str], int] = {}
    for fila in manifiesto:
        clave = (fila["orden"], fila["familia"])
        existentes[clave] = existentes.get(clave, 0) + 1

    def _clase(orden, familia: str, taxon_id: int, cupo: int) -> None:
        nonlocal manifiesto
        etiqueta = f"{orden.nombre}/{familia}" if familia else f"{orden.nombre} (cuota de orden)"
        tenidas = existentes.get((orden.nombre, familia), 0)
        faltan = max(0, cupo - tenidas)
        if not faltan:
            print(f"[{etiqueta}] completa ({tenidas} de {cupo})")
            return
        print(f"[{etiqueta}] {tenidas} de {cupo}, faltan {faltan}...")
        nuevas = descargar_clase(
            orden.nombre, familia, taxon_id,
            cupo=faltan, raiz=raiz, ya_descargados=ya,
            sesion_api=sesion_api, sesion_img=sesion_img,
            manifiesto_previo=manifiesto,
            solo_adultos=orden.solo_adultos,
            excluir_taxon_ids=orden.excluir_taxon_ids,
        )
        manifiesto += nuevas
        escribir_manifiesto(manifiesto, raiz / "manifiesto.csv")
        print(f"  +{len(nuevas)} imágenes")

    for orden in sorted(onto.ordenes, key=lambda o: o.nombre):
        # EL ORDEN DE ESTOS DOS BUCLES IMPORTA: PRIMERO LAS FAMILIAS.
        #
        # Una familia es un subconjunto taxonómico de su orden, y
        # `iterar_observaciones` pagina siempre desde la observación más
        # antigua. Las dos cuotas se disputan, por tanto, exactamente las
        # mismas observaciones, y `ya_descargados` se comparte entre ambas:
        # la que corra primero se las lleva y la otra ya no puede
        # recuperarlas.
        #
        # Si el orden fuese primero, cada observación que en realidad
        # pertenece a una familia declarada quedaría archivada bajo
        # `_sin_familia` con la etiqueta de familia vacía, de forma
        # permanente: la familia pierde ese ejemplar y nadie se entera. En
        # una familia escasa —justo las que la regla de admisión de
        # `splits.py` está para adjudicar— eso basta para empujarla bajo el
        # umbral y plegarla a `Otros_<Orden>`.
        #
        # Con las familias primero no se pierde nada, porque la relación es
        # de dominancia estricta: toda fila descargada como familia sirve
        # además como muestra de orden, ya que lleva el campo `orden`
        # poblado. La cuota de orden se queda con lo que ninguna familia
        # declarada reclamó, que es exactamente su propósito.
        #
        # No revertir este orden por estética ni por simetría con el resto
        # del módulo.
        for fam in sorted(orden.familias, key=lambda f: f.nombre):
            _clase(orden, fam.nombre, fam.inat_taxon_id, cupo_familia)
        _clase(orden, "", orden.inat_taxon_id, cupo_orden)

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
