from collections import defaultdict
from pathlib import Path

import pytest

from pipeline.curacion import COLUMNAS_CURADO
from pipeline.ontologia import cargar_ontologia
from pipeline.splits import (
    OBSERVADOR_DESCONOCIDO,
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


def test_resumen_reporta_observadores_unicos_por_clase_y_split(ruta_ontologia: Path):
    """El conteo de observadores únicos debe salir de recomponer la asignación real
    (asignar_grupos + aplicar_regla_admision), no de una estimación por proporciones."""
    onto = cargar_ontologia(ruta_ontologia)
    filas = (
        [fila(i, "obsGrande") for i in range(200)]
        + [fila(200 + i, "obsMediano") for i in range(60)]
        + [fila(260 + i, f"obsChico{i}") for i in range(5)]
    )
    _, resumen = particionar(filas, onto)

    asignacion = asignar_grupos(filas)
    reetiquetadas, _ = aplicar_regla_admision(filas, asignacion, onto)
    esperado_imagenes: dict[tuple[str, str], int] = defaultdict(int)
    esperado_observadores: dict[tuple[str, str], set] = defaultdict(set)
    for f in reetiquetadas:
        clase = f"{f['orden']}/{f['familia'] or '_sin_familia'}"
        split = asignacion[f["observador"]]
        esperado_imagenes[(clase, split)] += 1
        esperado_observadores[(clase, split)].add(f["observador"])

    for (clase, split), cantidad in esperado_imagenes.items():
        assert resumen["por_clase"][clase][split]["imagenes"] == cantidad
        assert resumen["por_clase"][clase][split]["observadores"] == len(
            esperado_observadores[(clase, split)]
        )


def test_clase_con_test_de_un_solo_observador_queda_senalada_en_el_reporte():
    """Una familia puede superar el mínimo de imágenes de test y, aun así, provenir
    de un solo fotógrafo: el reporte debe señalarlo en prosa, no solo en la tabla."""
    resumen = {
        "total": 100,
        "por_split": {"train": 70, "val": 15, "test": 15},
        "decisiones": {"Curculionidae": "admitida"},
        "por_clase": {
            "Coleoptera/Curculionidae": {
                "train": {"imagenes": 70, "observadores": 5},
                "val": {"imagenes": 15, "observadores": 2},
                "test": {"imagenes": 31, "observadores": 1},
            }
        },
        "anonimos_por_split": {"train": 0, "val": 0, "test": 0},
    }
    texto = reporte_markdown(resumen)
    assert "`Coleoptera/Curculionidae`" in texto
    assert "un solo fotógrafo" in texto.lower() or "un único fotógrafo" in texto.lower()


def test_clase_con_test_de_varios_observadores_no_queda_senalada():
    """Contraprueba: si el test de la clase viene de varias personas, no debe
    aparecer en la lista de clases en riesgo."""
    resumen = {
        "total": 100,
        "por_split": {"train": 70, "val": 15, "test": 15},
        "decisiones": {"Curculionidae": "admitida"},
        "por_clase": {
            "Coleoptera/Curculionidae": {
                "train": {"imagenes": 70, "observadores": 5},
                "val": {"imagenes": 15, "observadores": 2},
                "test": {"imagenes": 31, "observadores": 2},
            }
        },
        "anonimos_por_split": {"train": 0, "val": 0, "test": 0},
    }
    texto = reporte_markdown(resumen)
    assert "`Coleoptera/Curculionidae`" not in texto
    assert "Ninguna clase depende de un único fotógrafo" in texto


def test_reporte_informa_la_masa_de_observaciones_anonimas():
    """El reporte debe decir cuántas imágenes cayeron bajo el identificador de
    anónimos y en qué split, para que se note si es una porción grande del total."""
    resumen = {
        "total": 500,
        "por_split": {"train": 350, "val": 75, "test": 75},
        "decisiones": {},
        "por_clase": {},
        "anonimos_por_split": {"train": 120, "val": 0, "test": 0},
    }
    texto = reporte_markdown(resumen)
    assert OBSERVADOR_DESCONOCIDO in texto
    assert "120" in texto
    assert "train: 120" in texto
