"""Acceso de solo lectura a la base de datos biológica.

Tolera que la base no exista: en las primeras semanas Agronomía puede no
haber llenado el Excel todavía, y el prototipo debe poder demostrarse igual.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from pipeline.bd import COLUMNAS_BD


class RepositorioFichas:
    def __init__(self, ruta_sqlite: Path) -> None:
        self.ruta = Path(ruta_sqlite)

    def disponible(self) -> bool:
        return self.ruta.exists()

    def _consultar(self, sql: str, parametros: tuple) -> list[dict]:
        if not self.disponible():
            return []
        conexion = sqlite3.connect(self.ruta)
        conexion.row_factory = sqlite3.Row
        try:
            return [dict(f) for f in conexion.execute(sql, parametros).fetchall()]
        except sqlite3.DatabaseError:
            return []
        finally:
            conexion.close()

    def por_taxon(self, orden: str, familia: str = "") -> list[dict]:
        columnas = ", ".join(COLUMNAS_BD)
        if familia:
            return self._consultar(
                f"SELECT {columnas} FROM insectos WHERE Orden = ? AND Familia = ? "
                "ORDER BY ID",
                (orden, familia),
            )
        return self._consultar(
            f"SELECT {columnas} FROM insectos WHERE Orden = ? ORDER BY ID", (orden,)
        )

    def por_id(self, identificador: str) -> dict | None:
        columnas = ", ".join(COLUMNAS_BD)
        filas = self._consultar(
            f"SELECT {columnas} FROM insectos WHERE ID = ?", (identificador,)
        )
        return filas[0] if filas else None

    def resumen_por_orden(self) -> list[dict]:
        return self._consultar(
            "SELECT Orden AS orden, COUNT(*) AS registros FROM insectos "
            "GROUP BY Orden ORDER BY Orden",
            (),
        )
