import sqlite3
from pathlib import Path

import pytest

from backend.fichas import RepositorioFichas
from pipeline.bd import COLUMNAS_BD


@pytest.fixture
def base(tmp_path: Path) -> Path:
    ruta = tmp_path / "bd.sqlite"
    conexion = sqlite3.connect(ruta)
    columnas = ", ".join(f"{c} TEXT" for c in COLUMNAS_BD)
    conexion.execute(f"CREATE TABLE insectos ({columnas})")
    registros = [
        ("INS-0001", "Coleoptera", "Curculionidae", "gorgojo del plátano", "plátano", "plaga"),
        ("INS-0002", "Coleoptera", "Curculionidae", "otro gorgojo", "yuca", "plaga"),
        ("INS-0003", "Odonata", "Libellulidae", "libélula", "", "benéfico"),
    ]
    for identificador, orden, familia, comun, cultivo, importancia in registros:
        fila = {c: "" for c in COLUMNAS_BD}
        fila.update(
            ID=identificador,
            Orden=orden,
            Familia=familia,
            Nombre_comun=comun,
            Cultivo_asociado=cultivo,
            Importancia_economica=importancia,
        )
        conexion.execute(
            f"INSERT INTO insectos ({', '.join(COLUMNAS_BD)}) "
            f"VALUES ({', '.join('?' * len(COLUMNAS_BD))})",
            tuple(fila[c] for c in COLUMNAS_BD),
        )
    conexion.commit()
    conexion.close()
    return ruta


def test_busca_por_orden_y_familia(base: Path):
    fichas = RepositorioFichas(base).por_taxon("Coleoptera", "Curculionidae")
    assert len(fichas) == 2
    assert {f["Nombre_comun"] for f in fichas} == {"gorgojo del plátano", "otro gorgojo"}


def test_busca_solo_por_orden_cuando_no_hay_familia(base: Path):
    fichas = RepositorioFichas(base).por_taxon("Coleoptera")
    assert len(fichas) == 2


def test_taxon_sin_registros_devuelve_lista_vacia(base: Path):
    assert RepositorioFichas(base).por_taxon("Odonata", "Inexistente") == []


def test_las_fichas_traen_todas_las_columnas(base: Path):
    ficha = RepositorioFichas(base).por_taxon("Odonata")[0]
    assert set(ficha) == set(COLUMNAS_BD)


def test_buscar_por_id(base: Path):
    ficha = RepositorioFichas(base).por_id("INS-0002")
    assert ficha is not None and ficha["Cultivo_asociado"] == "yuca"


def test_id_inexistente_devuelve_none(base: Path):
    assert RepositorioFichas(base).por_id("INS-9999") is None


def test_resumen_cuenta_registros_por_orden(base: Path):
    resumen = {r["orden"]: r["registros"] for r in RepositorioFichas(base).resumen_por_orden()}
    assert resumen == {"Coleoptera": 2, "Odonata": 1}


def test_disponible_es_verdadero_con_base_existente(base: Path):
    assert RepositorioFichas(base).disponible() is True


def test_sin_archivo_el_repositorio_no_falla(tmp_path: Path):
    repositorio = RepositorioFichas(tmp_path / "no_existe.sqlite")
    assert repositorio.disponible() is False
    assert repositorio.por_taxon("Coleoptera") == []
    assert repositorio.por_id("INS-0001") is None
    assert repositorio.resumen_por_orden() == []


def test_no_es_vulnerable_a_inyeccion(base: Path):
    """El parámetro llega como valor, no como SQL."""
    repositorio = RepositorioFichas(base)
    assert repositorio.por_taxon("Coleoptera'; DROP TABLE insectos; --") == []
    assert len(repositorio.por_taxon("Coleoptera")) == 2  # la tabla sigue viva
