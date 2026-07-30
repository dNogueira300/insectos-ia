import sqlite3
from pathlib import Path

import pandas as pd

from pipeline.bd import COLUMNAS_BD, importar, validar
from pipeline.ontologia import cargar_ontologia


def marco(filas):
    return pd.DataFrame(filas, columns=list(COLUMNAS_BD))


def registro(**cambios):
    base = {c: "" for c in COLUMNAS_BD}
    base.update(
        ID="INS-0001",
        Archivo_imagen="Coleoptera/Curculionidae/1.jpg",
        Orden="Coleoptera",
        Familia="Curculionidae",
        Nombre_cientifico="Ejemplo sp.",
        Fecha="2026-01-15",
        Coordenadas="-3.75,-73.25",
    )
    base.update(cambios)
    return base


def test_registro_valido_no_da_errores(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    assert validar(marco([registro()]), onto) == []


def test_orden_fuera_de_la_ontologia_da_error(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    errores = validar(marco([registro(Orden="Inventado", Familia="")]), onto)
    assert any("Inventado" in e for e in errores)


def test_familia_que_no_pertenece_al_orden_da_error(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    errores = validar(marco([registro(Orden="Odonata", Familia="Curculionidae")]), onto)
    assert any("Curculionidae" in e for e in errores)


def test_id_duplicado_da_error(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    errores = validar(marco([registro(), registro()]), onto)
    assert any("INS-0001" in e for e in errores)


def test_fecha_mal_formada_da_error(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    errores = validar(marco([registro(Fecha="15/01/2026")]), onto)
    assert any("Fecha" in e for e in errores)


def test_coordenadas_mal_formadas_dan_error(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    errores = validar(marco([registro(Coordenadas="por ahi cerca")]), onto)
    assert any("Coordenadas" in e for e in errores)


def test_coordenadas_vacias_son_validas(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    assert validar(marco([registro(Coordenadas="")]), onto) == []


def test_falta_una_columna_da_error(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    df = marco([registro()]).drop(columns=["Hospedero"])
    errores = validar(df, onto)
    assert any("Hospedero" in e for e in errores)


def test_importar_escribe_sqlite(tmp_path: Path, ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    excel = tmp_path / "bd.xlsx"
    marco([registro(), registro(ID="INS-0002")]).to_excel(excel, index=False, sheet_name="BD_Insectos")

    cantidad, errores = importar(excel, tmp_path / "bd.sqlite", onto)

    assert errores == []
    assert cantidad == 2
    con = sqlite3.connect(tmp_path / "bd.sqlite")
    filas = con.execute("SELECT ID, Orden, Familia FROM insectos ORDER BY ID").fetchall()
    con.close()
    assert filas == [
        ("INS-0001", "Coleoptera", "Curculionidae"),
        ("INS-0002", "Coleoptera", "Curculionidae"),
    ]


def test_importar_con_errores_no_escribe_nada(tmp_path: Path, ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    excel = tmp_path / "bd.xlsx"
    marco([registro(Orden="Inventado", Familia="")]).to_excel(
        excel, index=False, sheet_name="BD_Insectos"
    )
    destino = tmp_path / "bd.sqlite"

    cantidad, errores = importar(excel, destino, onto)

    assert cantidad == 0
    assert errores
    assert not destino.exists()
