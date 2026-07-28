"""Censo de disponibilidad de imágenes por clase.

Produce la tabla con la que la Facultad decide qué órdenes y familias entran
al sistema, antes de descargar un solo archivo.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pipeline import gbif, inat
from pipeline.ontologia import Ontologia, cargar_ontologia

# El censo cuenta observaciones crudas; el umbral de admisión se aplica sobre
# imágenes curadas. Se estima que sobrevive ~67% (duplicados, fotos chicas,
# fotos de hábitat). Recalibrar tras la primera corrida de curación.
FACTOR_CURACION = 1.5


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
    veredicto: str      # "suficiente" o "insuficiente"


def _objetivo(onto: Ontologia) -> int:
    return round((onto.minimo_familia_train + onto.minimo_familia_test) * FACTOR_CURACION)


def censar(
    onto: Ontologia,
    *,
    lugar_id: int | None,
    pais_gbif: str | None,
    sesion_inat=None,
    sesion_gbif=None,
) -> list[FilaCenso]:
    """Consulta iNaturalist y GBIF para cada clase de la ontología."""
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
            global_ = inat.contar_observaciones(taxon_id, sesion=sesion_inat)
            en_lugar = (
                inat.contar_observaciones(taxon_id, lugar_id=lugar_id, sesion=sesion_inat)
                if lugar_id
                else 0
            )
            g_global = gbif.contar_ocurrencias(gbif_key, sesion=sesion_gbif) if gbif_key else 0
            g_pais = (
                gbif.contar_ocurrencias(gbif_key, pais=pais_gbif, sesion=sesion_gbif)
                if gbif_key and pais_gbif
                else 0
            )
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
                    veredicto="suficiente" if global_ >= objetivo else "insuficiente",
                )
            )
    return filas


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
        "| Nivel | Orden | Clase | iNat global | iNat en lugar | GBIF global | GBIF país | Objetivo | Veredicto |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for f in filas:
        lineas.append(
            f"| {f.nivel} | {f.orden} | {f.nombre} | {f.inat_global} | {f.inat_lugar} | "
            f"{f.gbif_global} | {f.gbif_pais} | {f.objetivo} | {f.veredicto} |"
        )

    insuficientes = [f.nombre for f in filas if f.nivel == "familia" and f.veredicto == "insuficiente"]
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

    filas = censar(onto, lugar_id=lugar_id, pais_gbif=args.pais_gbif, sesion_inat=sesion)

    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(a_markdown(filas, onto), encoding="utf-8")
    Path("datos").mkdir(exist_ok=True)
    Path("datos/censo.json").write_text(
        json.dumps([asdict(f) for f in filas], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Censo escrito en {args.salida} ({len(filas)} clases)")


if __name__ == "__main__":
    main()
