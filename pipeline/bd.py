"""Importación validada de la base de datos biológica: Excel a SQLite.

La valida contra la ontología para que Agronomía no pueda registrar un orden
o una familia que el sistema desconoce. Si hay un solo error, no se escribe
nada: es preferible una BD ausente a una BD silenciosamente inconsistente.
"""
from __future__ import annotations

import argparse
import math
import re
import sqlite3
from pathlib import Path

from pipeline.ontologia import Ontologia, cargar_ontologia

# pandas se importa dentro de `importar()`, no aquí: el backend del Plan 03
# necesita COLUMNAS_BD y no debe arrastrar pandas al despliegue.

COLUMNAS_BD = (
    "ID",
    "Archivo_imagen",
    "Vistas_fotograficas",
    "Orden",
    "Familia",
    "Nombre_cientifico",
    "Nombre_comun",
    "Cultivo_asociado",
    "Tipo_de_dano",
    "Hospedero",
    "Localidad",
    "Coordenadas",
    "Fecha",
    "Colector",
    "Importancia_economica",
    "Estado_biologico",
    "Fuente",
    "Verificado_por",
    "Observaciones",
)

HOJA = "BD_Insectos"
PATRON_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PATRON_COORDENADAS = re.compile(r"^-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?$")


def _texto(valor) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return ""
    return str(valor).strip()


def validar(df, onto: Ontologia) -> list[str]:
    """Devuelve la lista de errores legibles. Vacía si el marco es válido."""
    errores: list[str] = []

    faltantes = [c for c in COLUMNAS_BD if c not in df.columns]
    if faltantes:
        return [f"faltan columnas obligatorias: {', '.join(faltantes)}"]

    ordenes = set(onto.nombres_ordenes())
    familias = set(onto.nombres_familias())
    vistos: set[str] = set()

    for posicion, registro in df.iterrows():
        etiqueta = f"fila {posicion + 2}"  # +2: encabezado y base 1 de Excel

        identificador = _texto(registro["ID"])
        if not identificador:
            errores.append(f"{etiqueta}: ID vacío")
        elif identificador in vistos:
            errores.append(f"{etiqueta}: ID duplicado {identificador}")
        else:
            vistos.add(identificador)

        orden = _texto(registro["Orden"])
        if not orden:
            errores.append(f"{etiqueta}: Orden vacío")
        elif orden not in ordenes:
            errores.append(f"{etiqueta}: Orden '{orden}' no existe en la ontología")

        familia = _texto(registro["Familia"])
        if familia:
            if familia not in familias:
                errores.append(f"{etiqueta}: Familia '{familia}' no existe en la ontología")
            elif orden in ordenes and onto.orden_de_familia(familia) != orden:
                errores.append(
                    f"{etiqueta}: Familia '{familia}' no pertenece al orden '{orden}'"
                )

        fecha = _texto(registro["Fecha"])
        if fecha and not PATRON_FECHA.match(fecha):
            errores.append(f"{etiqueta}: Fecha '{fecha}' no tiene formato AAAA-MM-DD")

        coordenadas = _texto(registro["Coordenadas"])
        if coordenadas and not PATRON_COORDENADAS.match(coordenadas):
            errores.append(
                f"{etiqueta}: Coordenadas '{coordenadas}' no tienen formato 'lat, lon' decimal"
            )

    return errores


def importar(ruta_excel: Path, ruta_sqlite: Path, onto: Ontologia) -> tuple[int, list[str]]:
    """Valida el Excel y, si está limpio, lo vuelca a SQLite."""
    import pandas as pd  # local: mantiene el módulo importable sin pandas

    df = pd.read_excel(ruta_excel, sheet_name=HOJA, dtype=str).fillna("")
    errores = validar(df, onto)
    if errores:
        return 0, errores

    ruta_sqlite = Path(ruta_sqlite)
    ruta_sqlite.parent.mkdir(parents=True, exist_ok=True)
    esquema = (Path(__file__).resolve().parent.parent / "bd" / "esquema.sql").read_text(
        encoding="utf-8"
    )

    conexion = sqlite3.connect(ruta_sqlite)
    try:
        conexion.executescript(esquema)
        conexion.executemany(
            f"INSERT INTO insectos ({', '.join(COLUMNAS_BD)}) "
            f"VALUES ({', '.join('?' * len(COLUMNAS_BD))})",
            [tuple(_texto(fila[c]) for c in COLUMNAS_BD) for _, fila in df.iterrows()],
        )
        conexion.commit()
    finally:
        conexion.close()
    return len(df), []


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa la BD biológica de Excel a SQLite")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--excel", default="bd/bd_insectos.xlsx")
    parser.add_argument("--sqlite", default="bd/bd_insectos.sqlite")
    args = parser.parse_args()

    onto = cargar_ontologia(Path(args.ontologia))
    cantidad, errores = importar(Path(args.excel), Path(args.sqlite), onto)
    if errores:
        print(f"NO se importó nada. {len(errores)} errores:")
        for error in errores:
            print(f"  - {error}")
        raise SystemExit(1)
    print(f"{cantidad} registros importados en {args.sqlite}")


if __name__ == "__main__":
    main()
