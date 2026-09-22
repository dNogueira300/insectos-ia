from pipeline.desempeno import tabla_cobertura, tabla_por_clase


def test_la_tabla_ordena_de_la_clase_mas_debil_a_la_mas_fuerte():
    nombres = ("A", "B", "C")
    real = [0, 0, 1, 1, 2, 2]
    pred = [0, 0, 1, 2, 1, 2]  # A perfecta, B y C se confunden entre sí
    texto = tabla_por_clase(real, pred, nombres)
    filas = [linea for linea in texto.splitlines() if linea.startswith("| ") and "---" not in linea][1:]
    assert filas[-1].startswith("| A | 1.00 |")


def test_la_tabla_nombra_la_confusion_principal_de_cada_clase():
    nombres = ("A", "B", "C")
    real = [1, 1, 1, 1]
    pred = [2, 2, 0, 1]
    texto = tabla_por_clase(real, pred, nombres)
    assert "| B | " in texto and "C (2)" in texto


def test_una_clase_sin_confusiones_lo_dice():
    texto = tabla_por_clase([0, 1], [0, 1], ("A", "B"))
    assert "| A | 1.00 | 1 | — |" in texto


def test_la_cobertura_sube_la_exactitud_al_exigir_mas_confianza():
    confianzas = [0.95, 0.9, 0.4, 0.3]
    aciertos = [True, True, False, True]
    texto = tabla_cobertura(confianzas, aciertos, umbrales=(0.0, 0.5))
    assert "| 0.0 | 100% | 75.0% |" in texto
    assert "| 0.5 | 50% | 100.0% |" in texto
