import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from pipeline import bd
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


def test_falla_en_la_escritura_no_toca_datos_previos(
    tmp_path: Path, ruta_ontologia: Path, monkeypatch: pytest.MonkeyPatch
):
    """Una escritura nueva que falla a mitad de camino no debe destruir la BD previa."""
    onto = cargar_ontologia(ruta_ontologia)
    excel = tmp_path / "bd.xlsx"
    marco([registro()]).to_excel(excel, index=False, sheet_name="BD_Insectos")
    destino = tmp_path / "bd.sqlite"

    cantidad, errores = importar(excel, destino, onto)
    assert errores == []
    assert cantidad == 1

    con = sqlite3.connect(destino)
    previos = con.execute("SELECT ID FROM insectos").fetchall()
    con.close()
    assert previos == [("INS-0001",)]

    def _falla(_df, _ruta_temporal):
        raise RuntimeError("fallo simulado de E/S")

    monkeypatch.setattr(bd, "_construir_sqlite", _falla)
    cantidad2, errores2 = importar(excel, destino, onto)

    assert cantidad2 == 0
    assert errores2
    assert any("fallo simulado" in e for e in errores2)

    con = sqlite3.connect(destino)
    actuales = con.execute("SELECT ID FROM insectos").fetchall()
    con.close()
    assert actuales == previos


def test_falla_en_la_escritura_no_deja_archivos_temporales(
    tmp_path: Path, ruta_ontologia: Path, monkeypatch: pytest.MonkeyPatch
):
    """Un fallo a mitad de la escritura no debe dejar basura junto al destino."""
    onto = cargar_ontologia(ruta_ontologia)
    excel = tmp_path / "bd.xlsx"
    marco([registro()]).to_excel(excel, index=False, sheet_name="BD_Insectos")
    destino = tmp_path / "bd.sqlite"

    def _falla(_df, _ruta_temporal):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(bd, "_construir_sqlite", _falla)
    cantidad, errores = importar(excel, destino, onto)

    assert cantidad == 0
    assert errores
    assert not destino.exists()
    sospechosos = [p.name for p in tmp_path.iterdir() if "sqlite" in p.name or "tmp" in p.name]
    assert sospechosos == []


def test_reimportar_reemplaza_contenido_existente(tmp_path: Path, ruta_ontologia: Path):
    """Una reimportación exitosa sobre un destino existente debe reemplazar su contenido."""
    onto = cargar_ontologia(ruta_ontologia)
    excel1 = tmp_path / "bd1.xlsx"
    marco([registro()]).to_excel(excel1, index=False, sheet_name="BD_Insectos")
    destino = tmp_path / "bd.sqlite"
    importar(excel1, destino, onto)

    excel2 = tmp_path / "bd2.xlsx"
    marco([registro(ID="INS-0099")]).to_excel(excel2, index=False, sheet_name="BD_Insectos")
    cantidad, errores = importar(excel2, destino, onto)

    assert errores == []
    assert cantidad == 1
    con = sqlite3.connect(destino)
    filas = con.execute("SELECT ID FROM insectos").fetchall()
    con.close()
    assert filas == [("INS-0099",)]


@pytest.mark.parametrize("fecha", ["2026-13-45", "2026-02-30"])
def test_fecha_imposible_da_error(ruta_ontologia: Path, fecha: str):
    onto = cargar_ontologia(ruta_ontologia)
    errores = validar(marco([registro(Fecha=fecha)]), onto)
    assert any("Fecha" in e for e in errores)


@pytest.mark.parametrize("coordenadas", ["999,999", "-95.5,-200.3", "91,0", "0,181"])
def test_coordenadas_fuera_de_rango_dan_error(ruta_ontologia: Path, coordenadas: str):
    onto = cargar_ontologia(ruta_ontologia)
    errores = validar(marco([registro(Coordenadas=coordenadas)]), onto)
    assert any("Coordenadas" in e for e in errores)


def test_coordenadas_en_el_borde_del_rango_son_validas(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    assert validar(marco([registro(Coordenadas="-90,-180")]), onto) == []
    assert validar(marco([registro(Coordenadas="90,180")]), onto) == []
