from pathlib import Path

import numpy as np
import pytest

from pipeline.metricas import (
    cobertura_y_exactitud,
    exactitud,
    exactitud_jerarquica,
    f1_por_clase,
    guardar_matriz_png,
    macro_f1,
    matriz_confusion,
    tabla_por_clase,
    top_k,
)


def test_matriz_confusion_cuenta_bien():
    matriz = matriz_confusion([0, 0, 1, 1], [0, 1, 1, 1], 2)
    assert matriz.tolist() == [[1, 1], [0, 2]]


def test_prediccion_perfecta_da_f1_uno():
    matriz = matriz_confusion([0, 1, 2], [0, 1, 2], 3)
    assert f1_por_clase(matriz).tolist() == [1.0, 1.0, 1.0]


def test_clase_nunca_predicha_da_f1_cero():
    # La clase 2 existe en la verdad pero el modelo nunca la predice.
    matriz = matriz_confusion([0, 1, 2], [0, 1, 1], 3)
    assert f1_por_clase(matriz)[2] == 0.0


def test_clase_ausente_de_verdad_y_prediccion_da_f1_cero_sin_nan():
    matriz = matriz_confusion([0, 0], [0, 0], 3)
    valores = f1_por_clase(matriz)
    assert np.isfinite(valores).all()
    assert valores[1] == 0.0


def test_macro_f1_promedia_por_clase():
    # Clase 0 perfecta (F1=1), clase 1 nunca acertada (F1=0).
    assert macro_f1([0, 0, 1], [0, 0, 0], 2) == pytest.approx(0.4, abs=0.05)


def test_macro_f1_castiga_ignorar_la_clase_rara():
    y_true = [0] * 95 + [1] * 5
    y_pred = [0] * 100  # el modelo ignora por completo la clase rara
    assert exactitud(y_true, y_pred) == pytest.approx(0.95)
    assert macro_f1(y_true, y_pred, 2) < 0.5  # el macro-F1 sí lo detecta


def test_exactitud_jerarquica_exige_ambos_niveles():
    valor = exactitud_jerarquica([0, 0], [0, 0], [1, 1], [1, 2])
    assert valor == pytest.approx(0.5)


def test_exactitud_jerarquica_falla_si_el_orden_falla():
    assert exactitud_jerarquica([0], [1], [1], [1]) == 0.0


def test_top_k_acepta_el_acierto_en_segunda_posicion():
    probs = np.array([[0.2, 0.5, 0.3]])
    assert top_k(probs, [2], k=2) == 1.0   # clase 2 (0.3) es la segunda más probable
    assert top_k(probs, [2], k=1) == 0.0
    assert top_k(probs, [0], k=2) == 0.0   # clase 0 (0.2) es la tercera: fuera del top-2


def test_cobertura_y_exactitud_filtran_por_umbral():
    confianzas = [0.9, 0.8, 0.2, 0.1]
    aciertos = [True, False, True, True]
    cobertura, exacta = cobertura_y_exactitud(confianzas, aciertos, 0.5)
    assert cobertura == pytest.approx(0.5)
    assert exacta == pytest.approx(0.5)


def test_cobertura_cero_no_rompe():
    cobertura, exacta = cobertura_y_exactitud([0.1, 0.2], [True, True], 0.9)
    assert cobertura == 0.0
    assert exacta == 0.0


def test_tabla_por_clase_incluye_los_nombres():
    matriz = matriz_confusion([0, 1], [0, 1], 2)
    texto = tabla_por_clase(matriz, ["FamA", "FamB"])
    assert "FamA" in texto and "FamB" in texto


def test_guardar_matriz_png_crea_el_archivo(tmp_path: Path):
    matriz = matriz_confusion([0, 1, 1], [0, 1, 0], 2)
    destino = tmp_path / "m.png"
    guardar_matriz_png(matriz, ["A", "B"], destino)
    assert destino.exists() and destino.stat().st_size > 0
