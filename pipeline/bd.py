"""Importación validada de la base de datos biológica: Excel a SQLite.

La valida contra la ontología para que Agronomía no pueda registrar un orden
o una familia que el sistema desconoce. Si hay un solo error, no se escribe
nada: es preferible una BD ausente a una BD silenciosamente inconsistente.

Ese mismo principio rige la escritura: `importar()` nunca toca el archivo de
destino directamente. Arma la base completa en un archivo temporal y solo
reemplaza el destino cuando la escritura terminó sin fallos, así que un
error a mitad de camino (disco lleno, E/S, lo que sea) deja el destino
exactamente como estaba, sin propagar una excepción cruda.
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sqlite3
from datetime import date
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
PATRON_COORDENADAS = re.compile(r"^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$")
LATITUD_MINIMA, LATITUD_MAXIMA = -90.0, 90.0
LONGITUD_MINIMA, LONGITUD_MAXIMA = -180.0, 180.0


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
        if fecha:
            if not PATRON_FECHA.match(fecha):
                errores.append(f"{etiqueta}: Fecha '{fecha}' no tiene formato AAAA-MM-DD")
            else:
                anio, mes, dia = (int(parte) for parte in fecha.split("-"))
                try:
                    date(anio, mes, dia)
                except ValueError:
                    errores.append(
                        f"{etiqueta}: Fecha '{fecha}' no es una fecha real de colecta"
                    )

        coordenadas = _texto(registro["Coordenadas"])
        if coordenadas:
            coincidencia = PATRON_COORDENADAS.match(coordenadas)
            if not coincidencia:
                errores.append(
                    f"{etiqueta}: Coordenadas '{coordenadas}' no tienen formato 'lat, lon' decimal"
                )
            else:
                latitud, longitud = (float(g) for g in coincidencia.groups())
                if not (LATITUD_MINIMA <= latitud <= LATITUD_MAXIMA) or not (
                    LONGITUD_MINIMA <= longitud <= LONGITUD_MAXIMA
                ):
                    errores.append(
                        f"{etiqueta}: Coordenadas '{coordenadas}' fuera de rango "
                        f"(latitud entre {LATITUD_MINIMA:.0f} y {LATITUD_MAXIMA:.0f}, "
                        f"longitud entre {LONGITUD_MINIMA:.0f} y {LONGITUD_MAXIMA:.0f})"
                    )

    return errores


def _construir_sqlite(df, ruta_temporal: Path) -> None:
    """Crea el esquema y vuelca las filas de `df` en un archivo nuevo.

    `ruta_temporal` no es el destino final: `importar()` solo lo promueve a
    destino si esta función termina sin lanzar ninguna excepción. `DROP TABLE
    IF EXISTS` del esquema corre aquí, sobre el archivo temporal, así que
    nunca toca datos previos del destino.
    """
    esquema = (Path(__file__).resolve().parent.parent / "bd" / "esquema.sql").read_text(
        encoding="utf-8"
    )
    conexion = sqlite3.connect(ruta_temporal)
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


def importar(ruta_excel: Path, ruta_sqlite: Path, onto: Ontologia) -> tuple[int, list[str]]:
    """Valida el Excel y, si está limpio, lo vuelca a SQLite de forma atómica.

    Nunca escribe directamente sobre `ruta_sqlite`: construye la base en un
    archivo temporal junto a él (`_construir_sqlite`) y solo lo reemplaza,
    con `os.replace`, cuando esa escritura terminó sin errores. La conexión
    ya está cerrada para ese momento, así que el reemplazo funciona también
    en Windows. Si algo falla en cualquier punto, se borra el temporal y el
    destino queda exactamente como estaba (con los datos previos intactos si
    existían, o inexistente si no existía); el fallo se devuelve como error,
    nunca como excepción sin capturar.
    """
    import pandas as pd  # local: mantiene el módulo importable sin pandas

    df = pd.read_excel(ruta_excel, sheet_name=HOJA, dtype=str).fillna("")
    errores = validar(df, onto)
    if errores:
        return 0, errores

    ruta_sqlite = Path(ruta_sqlite)
    ruta_sqlite.parent.mkdir(parents=True, exist_ok=True)
    ruta_temporal = ruta_sqlite.with_name(f".{ruta_sqlite.name}.tmp-{os.getpid()}")
    ruta_temporal.unlink(missing_ok=True)  # restos de una corrida anterior interrumpida

    try:
        _construir_sqlite(df, ruta_temporal)
        os.replace(ruta_temporal, ruta_sqlite)
    except Exception as error:
        ruta_temporal.unlink(missing_ok=True)
        return 0, [f"no se pudo escribir la base de datos: {error}"]

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
