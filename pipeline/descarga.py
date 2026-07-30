"""Descarga masiva de imágenes con manifiesto de trazabilidad.

El manifiesto es la pieza central del pipeline: arrastra observación,
observador y licencia hasta los splits. Sin él no se puede agrupar por
observador (Tarea 7) ni atribuir las fotos.

NOTA: este módulo aún no está completo. La Tarea 6 (curación) depende de
`COLUMNAS_MANIFIESTO`, `leer_manifiesto` y `escribir_manifiesto`, así que se
adelantan aquí tal como las especifica el brief de la Tarea 5. El resto de
la Tarea 5 (`descargar_clase`, `descargar_todo`, `LICENCIAS_PERMITIDAS`,
`main`) queda pendiente de implementar en su propia tarea.
"""
from __future__ import annotations

import csv
from pathlib import Path

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
