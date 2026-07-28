"""Censo de disponibilidad de imágenes por clase.

Produce la tabla con la que la Facultad decide qué órdenes y familias entran
al sistema, antes de descargar un solo archivo.
"""
from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from pipeline import gbif, inat
from pipeline.ontologia import Ontologia, cargar_ontologia

# El censo cuenta observaciones crudas; el umbral de admisión se aplica sobre
# imágenes curadas. Se estima que sobrevive ~67% (duplicados, fotos chicas,
# fotos de hábitat). Recalibrar tras la primera corrida de curación.
FACTOR_CURACION = 1.5

# Marca un conteo que no se obtuvo: por un fallo de red al consultarlo, o
# porque la fuente no aplica para esa clase (p. ej. GBIF en una familia, que
# no tiene `gbif_key` propio en la ontología). No debe confundirse con un 0
# real (0 significa "se consultó y no hay registros").
SIN_DATO = -1

# Veredicto de una clase en la que falló la consulta de red (iNaturalist o
# GBIF). No es "insuficiente" -esa palabra implica que sí se consultó y no
# alcanza el objetivo-, sino "no se sabe todavía": hay que reintentarla.
VEREDICTO_ERROR = "error_consulta"


@dataclass(frozen=True)
class FilaCenso:
    nivel: str          # "orden" o "familia"
    orden: str
    nombre: str
    inat_global: int
    inat_lugar: int
    gbif_global: int
    gbif_pais: int
    objetivo: int
    veredicto: str      # "suficiente", "insuficiente" o VEREDICTO_ERROR


def _objetivo(onto: Ontologia) -> int:
    return round((onto.minimo_familia_train + onto.minimo_familia_test) * FACTOR_CURACION)


def censar(
    onto: Ontologia,
    *,
    lugar_id: int | None,
    pais_gbif: str | None,
    sesion_inat=None,
    sesion_gbif=None,
    pausa_segundos: float = inat.PAUSA_SEGUNDOS,
    al_avanzar: Callable[[list[FilaCenso]], None] | None = None,
) -> list[FilaCenso]:
    """Consulta iNaturalist y GBIF para cada clase de la ontología.

    Un fallo de red al consultar una clase no aborta el censo completo: se
    captura, la fila queda con sus conteos en `SIN_DATO` y veredicto
    `VEREDICTO_ERROR`, y el recorrido sigue con la siguiente clase. Distinguir
    ese caso de "insuficiente" importa porque "insuficiente" implica que sí
    se consultó y no alcanza el objetivo; "error_consulta" significa que no
    se sabe todavía y hay que reintentar. Se captura `Exception` en general
    (no solo `requests.RequestException`) porque un fallo de red real puede
    aparecer como error de conexión, tiempo de espera, código HTTP, o incluso
    una respuesta sin el campo JSON esperado -no vale la pena enumerar cada
    subtipo cuando el tratamiento es el mismo: no perder el resto del censo.

    `pausa_segundos` throttlea las llamadas a iNaturalist entre una clase y
    la siguiente, reutilizando por defecto `pipeline.inat.PAUSA_SEGUNDOS` (la
    misma constante que ya usa `iterar_observaciones` entre páginas). Las
    pruebas pasan 0 para no dormir de verdad.

    Si se pasa `al_avanzar`, se invoca con una copia de las filas censadas
    hasta el momento después de cada clase, para que quien llama pueda
    persistir el progreso incrementalmente y no perder el trabajo hecho si
    el proceso se interrumpe a mitad de camino.
    """
    sesion_inat = sesion_inat or inat.nueva_sesion()
    sesion_gbif = sesion_gbif or gbif.nueva_sesion()
    objetivo = _objetivo(onto)
    filas: list[FilaCenso] = []

    for orden in sorted(onto.ordenes, key=lambda o: o.nombre):
        candidatos = [("orden", orden.nombre, orden.inat_taxon_id, orden.gbif_key)]
        candidatos += [
            ("familia", fam.nombre, fam.inat_taxon_id, None)
            for fam in sorted(orden.familias, key=lambda f: f.nombre)
        ]

        for nivel, nombre, taxon_id, gbif_key in candidatos:
            try:
                global_ = inat.contar_observaciones(taxon_id, sesion=sesion_inat)
                en_lugar = (
                    inat.contar_observaciones(taxon_id, lugar_id=lugar_id, sesion=sesion_inat)
                    if lugar_id
                    else 0
                )
                if pausa_segundos:
                    time.sleep(pausa_segundos)
                g_global = (
                    gbif.contar_ocurrencias(gbif_key, sesion=sesion_gbif)
                    if gbif_key
                    else SIN_DATO
                )
                g_pais = (
                    gbif.contar_ocurrencias(gbif_key, pais=pais_gbif, sesion=sesion_gbif)
                    if gbif_key and pais_gbif
                    else SIN_DATO
                )
                veredicto = "suficiente" if global_ >= objetivo else "insuficiente"
            except Exception:
                global_ = en_lugar = g_global = g_pais = SIN_DATO
                veredicto = VEREDICTO_ERROR

            filas.append(
                FilaCenso(
                    nivel=nivel,
                    orden=orden.nombre,
                    nombre=nombre,
                    inat_global=global_,
                    inat_lugar=en_lugar,
                    gbif_global=g_global,
                    gbif_pais=g_pais,
                    objetivo=objetivo,
                    veredicto=veredicto,
                )
            )
            if al_avanzar is not None:
                al_avanzar(list(filas))
    return filas


def _celda(valor: int) -> str:
    """Renderiza un conteo; `SIN_DATO` se ve como `N/D`, nunca como `-1`."""
    return "N/D" if valor == SIN_DATO else str(valor)


def a_markdown(filas: list[FilaCenso], onto: Ontologia) -> str:
    """Reporte legible para llevar a la reunión con la Facultad."""
    objetivo = _objetivo(onto)
    lineas = [
        "# Censo de disponibilidad de imágenes por clase",
        "",
        f"Umbral de admisión de una familia: **{onto.minimo_familia_train} imágenes curadas "
        f"en train y {onto.minimo_familia_test} en test**.",
        "",
        f"Factor de curación estimado: **{FACTOR_CURACION}** (se asume que sobrevive ~"
        f"{round(100 / FACTOR_CURACION)}% de lo descargado tras deduplicar y filtrar). "
        f"Por eso el objetivo de observaciones crudas es **{objetivo}** por familia.",
        "",
        "La columna *en lugar* filtra por la región configurada; sirve para ver cuánto "
        "del material disponible es realmente amazónico.",
        "",
        "**Los conteos incluyen solo ejemplares adultos** (`solo_adultos=True` excluye "
        "larvas, orugas y ninfas por defecto en la consulta a iNaturalist). Quien compare "
        "estas cifras contra la web pública de iNaturalist verá números menores por esa razón; "
        "no es un error del censo.",
        "",
        "**El veredicto se calcula solo con la columna *iNat global* (conteo mundial)**, no "
        "con *iNat en lugar*. Una clase abundante en el mundo pero casi ausente en la región "
        "configurada puede salir marcada como \"suficiente\" igual: no se debe leer "
        "\"suficiente\" como \"suficiente material amazónico\". Si el veredicto debe ponderar "
        "la columna regional es una decisión pendiente, todavía sin tomar.",
        "",
        "**`N/D`** marca una celda que no se consultó, para no confundirla con un 0 real "
        "(0 significa \"se consultó y no hay registros\"). Las columnas GBIF de las familias "
        "siempre muestran `N/D`: la ontología solo asigna `gbif_key` a nivel de orden, así "
        "que GBIF nunca se consulta para una familia por sí sola. También aparece `N/D` en "
        "cualquier columna de una fila con veredicto `error_consulta`.",
        "",
        f"**`{VEREDICTO_ERROR}`** marca una clase en la que la consulta a iNaturalist o a "
        "GBIF falló (red, límite de tasa, etc.). No equivale a \"insuficiente\": significa "
        "que no se sabe todavía y hay que reintentar esa clase.",
        "",
        "| Nivel | Orden | Clase | iNat global | iNat en lugar | GBIF global | GBIF país | Objetivo | Veredicto |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for f in filas:
        lineas.append(
            f"| {f.nivel} | {f.orden} | {f.nombre} | {_celda(f.inat_global)} | "
            f"{_celda(f.inat_lugar)} | {_celda(f.gbif_global)} | {_celda(f.gbif_pais)} | "
            f"{f.objetivo} | {f.veredicto} |"
        )

    insuficientes = [f.nombre for f in filas if f.nivel == "familia" and f.veredicto == "insuficiente"]
    con_error = [f"{f.orden}/{f.nombre}" for f in filas if f.veredicto == VEREDICTO_ERROR]
    lineas += [
        "",
        "## Familias que no alcanzan el umbral",
        "",
        (
            ", ".join(insuficientes)
            if insuficientes
            else "Ninguna: todas las familias censadas alcanzan el objetivo."
        ),
        "",
        "Estas familias no entran como clase propia. Se agrupan en `Otros_<Orden>` "
        "dentro de su orden, o se reemplazan por otras que la Facultad considere "
        "igual de relevantes y con más material disponible.",
    ]
    if con_error:
        lineas += [
            "",
            "## Clases que no se pudieron consultar (reintentar antes de decidir)",
            "",
            ", ".join(con_error),
        ]
    return "\n".join(lineas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Censo de disponibilidad por clase")
    parser.add_argument("--ontologia", default="ontologia/candidatas.yaml")
    parser.add_argument("--lugar", default="Peru", help="nombre del lugar en iNaturalist")
    parser.add_argument("--pais-gbif", default="PE", help="código ISO-2 para GBIF")
    parser.add_argument("--salida", default="docs/censo_disponibilidad.md")
    args = parser.parse_args()

    onto = cargar_ontologia(Path(args.ontologia))
    sesion = inat.nueva_sesion()
    lugar_id = inat.buscar_lugar(args.lugar, sesion=sesion) if args.lugar else None
    print(f"Lugar '{args.lugar}' resuelto a place_id={lugar_id}")

    ruta_salida = Path(args.salida)
    ruta_json = Path("datos/censo.json")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    ruta_json.parent.mkdir(exist_ok=True)

    def _guardar_avance(filas_hasta_ahora: list[FilaCenso]) -> None:
        # Guardado incremental (Hallazgo 1): si el proceso se interrumpe a
        # mitad de camino -límite de tasa, corte de red, cierre manual-, lo
        # censado hasta ese punto ya quedó en disco y no hay que reiniciar
        # el censo completo.
        ruta_json.write_text(
            json.dumps([asdict(f) for f in filas_hasta_ahora], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        ruta_salida.write_text(a_markdown(filas_hasta_ahora, onto), encoding="utf-8")

    filas = censar(
        onto,
        lugar_id=lugar_id,
        pais_gbif=args.pais_gbif,
        sesion_inat=sesion,
        al_avanzar=_guardar_avance,
    )

    _guardar_avance(filas)
    print(f"Censo escrito en {args.salida} ({len(filas)} clases)")


if __name__ == "__main__":
    main()
