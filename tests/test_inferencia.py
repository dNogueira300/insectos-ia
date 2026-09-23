import numpy as np
import pytest

from pipeline.etiquetas import EspacioEtiquetas
from pipeline.inferencia import Prediccion, enmascarar, predecir, softmax

ESPACIO = EspacioEtiquetas(
    ordenes=("OrdenA", "OrdenB"),
    familias=("FamA1", "FamA2", "FamB1"),
    matriz=((True, False), (True, False), (False, True)),
)
MATRIZ = np.array(ESPACIO.matriz, dtype=bool)


def test_softmax_suma_uno():
    assert softmax(np.array([1.0, 2.0, 3.0])).sum() == pytest.approx(1.0)


def test_softmax_es_estable_con_valores_grandes():
    salida = softmax(np.array([1000.0, 1001.0]))
    assert np.isfinite(salida).all()
    assert salida.sum() == pytest.approx(1.0)


def test_enmascarar_anula_las_familias_de_otro_orden():
    probs = np.array([0.2, 0.3, 0.5])
    salida = enmascarar(probs, 0, MATRIZ)  # orden A
    assert salida[2] == 0.0
    assert salida[:2].sum() == pytest.approx(1.0)


def test_enmascarar_renormaliza():
    probs = np.array([0.1, 0.1, 0.8])
    salida = enmascarar(probs, 0, MATRIZ)
    assert salida.sum() == pytest.approx(1.0)
    assert salida[0] == pytest.approx(0.5)


def test_enmascarar_con_todo_en_cero_no_divide_por_cero():
    probs = np.array([0.0, 0.0, 1.0])
    salida = enmascarar(probs, 0, MATRIZ)
    assert np.isfinite(salida).all()
    assert salida.sum() == pytest.approx(0.0)


def test_predecir_elige_el_orden_de_mayor_logit():
    prediccion = predecir(np.array([5.0, 0.0]), np.array([0.0, 0.0, 9.0]), ESPACIO)
    assert prediccion.orden == "OrdenA"


def test_la_familia_predicha_pertenece_al_orden_predicho():
    """El logit más alto de familia es de OrdenB, pero el orden ganó A."""
    prediccion = predecir(np.array([5.0, 0.0]), np.array([1.0, 2.0, 9.0]), ESPACIO)
    assert prediccion.orden == "OrdenA"
    assert prediccion.familia == "FamA2"


def test_familia_incierta_cuando_no_supera_el_umbral():
    prediccion = predecir(
        np.array([5.0, 0.0]), np.array([1.0, 1.0, 0.0]), ESPACIO, umbral=0.9
    )
    assert prediccion.familia_incierta is True
    assert prediccion.confianza_familia < 0.9


def test_familia_certera_cuando_supera_el_umbral():
    prediccion = predecir(
        np.array([5.0, 0.0]), np.array([9.0, 0.0, 0.0]), ESPACIO, umbral=0.5
    )
    assert prediccion.familia_incierta is False
    assert prediccion.familia == "FamA1"


def test_por_omision_una_familia_al_60_por_ciento_es_incierta():
    """Con la v3, exigir 0.7 responde en el 89 % de las fotos y acierta el 93.6 %.

    A 0.6 el acierto cae al 92 %: esa respuesta debe mostrarse como duda.
    """
    prediccion = predecir(
        np.array([5.0, 0.0]), np.array([np.log(1.5), 0.0, 0.0]), ESPACIO
    )
    assert prediccion.confianza_familia == pytest.approx(0.6)
    assert prediccion.familia_incierta is True


def test_por_omision_una_familia_al_75_por_ciento_se_afirma():
    prediccion = predecir(
        np.array([5.0, 0.0]), np.array([np.log(3.0), 0.0, 0.0]), ESPACIO
    )
    assert prediccion.confianza_familia == pytest.approx(0.75)
    assert prediccion.familia_incierta is False


def test_top_familias_solo_incluye_las_del_orden():
    prediccion = predecir(np.array([5.0, 0.0]), np.array([1.0, 2.0, 9.0]), ESPACIO)
    nombres = [n for n, _ in prediccion.top_familias]
    assert "FamB1" not in nombres


def test_top_familias_viene_ordenado_de_mayor_a_menor():
    prediccion = predecir(np.array([5.0, 0.0]), np.array([1.0, 2.0, 0.0]), ESPACIO)
    valores = [p for _, p in prediccion.top_familias]
    assert valores == sorted(valores, reverse=True)


def test_orden_sin_familias_devuelve_familia_vacia():
    espacio = EspacioEtiquetas(
        ordenes=("OrdenA", "OrdenB"), familias=("FamA1",), matriz=((True, False),)
    )
    prediccion = predecir(np.array([0.0, 5.0]), np.array([9.0]), espacio)
    assert prediccion.orden == "OrdenB"
    assert prediccion.familia == ""
    assert prediccion.familia_incierta is True


def test_devuelve_una_prediccion():
    assert isinstance(predecir(np.array([1.0, 0.0]), np.array([1.0, 0.0, 0.0]), ESPACIO), Prediccion)
