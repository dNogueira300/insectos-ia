from pathlib import Path

import pytest

from pipeline.curacion import COLUMNAS_CURADO
from pipeline.ontologia import cargar_ontologia
from pipeline.splits import (
    PROPORCIONES,
    aplicar_regla_admision,
    asignar_grupos,
    particionar,
    reporte_markdown,
)


def fila(obs_id, observador, orden="Coleoptera", familia="Curculionidae"):
    base = {c: "" for c in COLUMNAS_CURADO}
    base.update(
        archivo=f"{orden}/{familia or '_sin_familia'}/{obs_id}.jpg",
        obs_id=str(obs_id),
        observador=observador,
        orden=orden,
        familia=familia,
        hash=f"{obs_id:016x}",
    )
    return base


def muchas(n, orden="Coleoptera", familia="Curculionidae", desde=0, por_observador=1):
    return [
        fila(desde + i, f"obs{orden}{familia}{(desde + i) // por_observador}", orden, familia)
        for i in range(n)
    ]


def test_cada_observador_cae_en_un_solo_split():
    filas = muchas(300, por_observador=5)
    asignacion = asignar_grupos(filas)
    for f in filas:
        assert f["observador"] in asignacion
    assert len(set(asignacion.values())) <= 3


def test_ningun_observador_cruza_splits():
    filas = muchas(300, por_observador=5)
    particiones, _ = particionar(filas, cargar_ontologia(Path("ontologia/clases.yaml")))
    de_train = {f["observador"] for f in particiones["train"]}
    de_val = {f["observador"] for f in particiones["val"]}
    de_test = {f["observador"] for f in particiones["test"]}
    assert not (de_train & de_val)
    assert not (de_train & de_test)
    assert not (de_val & de_test)


def test_proporciones_aproximadas():
    filas = muchas(1000, por_observador=2)
    asignacion = asignar_grupos(filas)
    conteo = {"train": 0, "val": 0, "test": 0}
    for f in filas:
        conteo[asignacion[f["observador"]]] += 1
    assert conteo["train"] / len(filas) == pytest.approx(PROPORCIONES["train"], abs=0.10)


def test_asignacion_es_determinista():
    filas = muchas(200, por_observador=3)
    assert asignar_grupos(filas) == asignar_grupos(list(reversed(filas)))


def test_familia_bajo_el_umbral_pasa_a_otros(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)  # minimos: 150 train / 30 test
    filas = muchas(40, orden="Coleoptera", familia="Curculionidae", por_observador=1)
    asignacion = asignar_grupos(filas)
    resultado, decisiones = aplicar_regla_admision(filas, asignacion, onto)
    assert {f["familia"] for f in resultado} == {"Otros_Coleoptera"}
    assert decisiones["Curculionidae"] == "agrupada"


def test_familia_sobre_el_umbral_se_conserva(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = muchas(900, orden="Coleoptera", familia="Curculionidae", por_observador=1)
    asignacion = asignar_grupos(filas)
    resultado, decisiones = aplicar_regla_admision(filas, asignacion, onto)
    assert {f["familia"] for f in resultado} == {"Curculionidae"}
    assert decisiones["Curculionidae"] == "admitida"


def test_filas_sin_familia_no_se_tocan(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = muchas(50, orden="Coleoptera", familia="", por_observador=1)
    asignacion = asignar_grupos(filas)
    resultado, _ = aplicar_regla_admision(filas, asignacion, onto)
    assert {f["familia"] for f in resultado} == {""}


def test_particionar_devuelve_los_tres_splits(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    particiones, resumen = particionar(muchas(600, por_observador=2), onto)
    assert set(particiones) == {"train", "val", "test"}
    assert resumen["total"] == 600


def test_reporte_lista_las_familias_agrupadas():
    resumen = {
        "total": 100,
        "por_split": {"train": 70, "val": 15, "test": 15},
        "decisiones": {"FamA": "admitida", "FamB": "agrupada"},
        "por_clase": {},
    }
    texto = reporte_markdown(resumen)
    assert "FamB" in texto and "agrupada" in texto
