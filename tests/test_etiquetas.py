from pathlib import Path

import pytest

from pipeline.etiquetas import (
    SIN_FAMILIA_IDX,
    cargar_espacio,
    construir_espacio,
)
from pipeline.ontologia import cargar_ontologia


def fila(orden, familia):
    return {"orden": orden, "familia": familia}


def test_ordenes_salen_de_la_ontologia(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    espacio = construir_espacio([fila("Coleoptera", "Curculionidae")], onto)
    assert espacio.ordenes == ("Coleoptera", "Odonata")


def test_familias_salen_de_los_datos_no_de_la_ontologia(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = [fila("Coleoptera", "Curculionidae"), fila("Coleoptera", "Otros_Coleoptera")]
    espacio = construir_espacio(filas, onto)
    assert espacio.familias == ("Curculionidae", "Otros_Coleoptera")
    assert "Chrysomelidae" not in espacio.familias  # declarada, pero sin datos


def test_familia_vacia_no_genera_clase(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    espacio = construir_espacio([fila("Coleoptera", ""), fila("Coleoptera", "Curculionidae")], onto)
    assert espacio.familias == ("Curculionidae",)


def test_indice_de_familia_vacia_es_el_de_ignorar(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    espacio = construir_espacio([fila("Coleoptera", "Curculionidae")], onto)
    assert espacio.indice_familia("") == SIN_FAMILIA_IDX
    assert SIN_FAMILIA_IDX == -1


def test_matriz_asocia_otros_con_su_orden(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = [
        fila("Coleoptera", "Curculionidae"),
        fila("Coleoptera", "Otros_Coleoptera"),
        fila("Odonata", "Libellulidae"),
    ]
    espacio = construir_espacio(filas, onto)
    i_otros = espacio.indice_familia("Otros_Coleoptera")
    i_coleoptera = espacio.indice_orden("Coleoptera")
    i_odonata = espacio.indice_orden("Odonata")
    assert espacio.matriz[i_otros][i_coleoptera] is True
    assert espacio.matriz[i_otros][i_odonata] is False


def test_cada_familia_pertenece_a_exactamente_un_orden(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = [
        fila("Coleoptera", "Curculionidae"),
        fila("Coleoptera", "Otros_Coleoptera"),
        fila("Odonata", "Libellulidae"),
    ]
    espacio = construir_espacio(filas, onto)
    for renglon in espacio.matriz:
        assert sum(renglon) == 1


def test_familia_desconocida_falla(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    with pytest.raises(KeyError):
        construir_espacio([fila("Coleoptera", "Inventadidae")], onto)


def test_orden_desconocido_falla(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    with pytest.raises(KeyError):
        construir_espacio([fila("Inventado", "")], onto)


def test_guardar_y_cargar_conserva_todo(tmp_path: Path, ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = [fila("Coleoptera", "Curculionidae"), fila("Odonata", "Libellulidae")]
    espacio = construir_espacio(filas, onto)
    ruta = tmp_path / "etiquetas.json"
    espacio.guardar(ruta)
    recuperado = cargar_espacio(ruta)
    assert recuperado == espacio


def test_indices_son_estables_ante_el_orden_de_las_filas(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = [fila("Odonata", "Libellulidae"), fila("Coleoptera", "Curculionidae")]
    a = construir_espacio(filas, onto)
    b = construir_espacio(list(reversed(filas)), onto)
    assert a == b
