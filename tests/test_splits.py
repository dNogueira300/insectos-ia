import random
from collections import defaultdict
from pathlib import Path

import pytest

from pipeline.curacion import COLUMNAS_CURADO
from pipeline.ontologia import cargar_ontologia
from pipeline.splits import (
    ARCHIVO_ASIGNACION,
    DECISION_ADMITIDA,
    DECISION_MATERIAL_ESCASO,
    DECISION_SIN_REPARTO,
    OBSERVADOR_DESCONOCIDO,
    PROPORCIONES,
    SALIDA_ASIGNACION_INVALIDA,
    ErrorAsignacion,
    aplicar_regla_admision,
    asignar_grupos,
    escribir_asignacion,
    leer_asignacion,
    main,
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


# --- Estratificación por clase (B1a) ----------------------------------------


def escenario_especializado(
    *, n_familias=8, por_familia=600, obs_por_familia=6, semilla=0
) -> list[dict]:
    """Observadores especializados: cada uno fotografía una sola familia.

    Es el caso real en taxonomía y el garantizado en las familias amazónicas
    raras, que dependen de un puñado de naturalistas locales. Las 8 familias
    tienen 600 imágenes curadas cada una, muy por encima del umbral de
    150 train + 30 test: ninguna debería quedar plegada a `Otros_`.
    """
    rng = random.Random(semilla)
    filas: list[dict] = []
    oid = 0
    for f in range(n_familias):
        familia = f"Fam{f:02d}"
        for _ in range(obs_por_familia):
            nombre = f"nat_{rng.randrange(10**9):09d}"
            for _ in range(por_familia // obs_por_familia):
                oid += 1
                filas.append(fila(oid, nombre, "OrdenZ", familia))
    rng.shuffle(filas)  # el orden de llegada no debe influir
    return filas


@pytest.mark.parametrize("semilla", [0, 1, 2, 3, 4])
def test_ninguna_familia_se_pliega_con_observadores_especializados(
    ruta_ontologia: Path, semilla: int
):
    """El reparto debe estratificar por clase, no solo por total global.

    Sin conciencia de clase, todos los observadores de una familia pueden
    caer del mismo lado y la familia queda plegada a `Otros_` pese a tener
    600 fotografías. El documento con el que la Facultad decide qué clases
    entran reportaría entonces como carentes de datos a familias que sobran
    de material.
    """
    onto = cargar_ontologia(ruta_ontologia)  # minimos: 150 train / 30 test
    filas = escenario_especializado(semilla=semilla)
    asignacion = asignar_grupos(filas)
    _, decisiones = aplicar_regla_admision(filas, asignacion, onto)

    plegadas = sorted(f for f, d in decisiones.items() if d != DECISION_ADMITIDA)
    assert plegadas == [], f"familias con 600 imágenes plegadas a Otros_: {plegadas}"


@pytest.mark.parametrize("semilla", [0, 1, 2, 3, 4])
def test_ninguna_familia_se_queda_sin_imagenes_en_el_examen(
    ruta_ontologia: Path, semilla: int
):
    """Contraparte del anterior: cero imágenes en test es peor que quedar
    plegada, porque la clase existe en el modelo y nadie la evalúa."""
    filas = escenario_especializado(semilla=semilla)
    asignacion = asignar_grupos(filas)
    en_test: dict[str, int] = defaultdict(int)
    for f in filas:
        if asignacion[f["observador"]] == "test":
            en_test[f["familia"]] += 1
    sin_examen = sorted({f["familia"] for f in filas} - set(en_test))
    assert sin_examen == [], f"familias sin ninguna imagen de examen: {sin_examen}"


def test_la_estratificacion_no_parte_a_ningun_observador(ruta_ontologia: Path):
    """Propiedad que ya se cumplía y no puede perderse con el criterio nuevo."""
    filas = escenario_especializado(semilla=7)
    particiones, _ = particionar(filas, cargar_ontologia(ruta_ontologia))
    de_train = {f["observador"] for f in particiones["train"]}
    de_val = {f["observador"] for f in particiones["val"]}
    de_test = {f["observador"] for f in particiones["test"]}
    assert not (de_train & de_val)
    assert not (de_train & de_test)
    assert not (de_val & de_test)


def test_la_estratificacion_es_independiente_del_orden_de_llegada():
    """Determinismo con varias clases en juego, no solo con una."""
    filas = escenario_especializado(semilla=3)
    assert asignar_grupos(filas) == asignar_grupos(list(reversed(filas)))
    revuelto = list(filas)
    random.Random(99).shuffle(revuelto)
    assert asignar_grupos(filas) == asignar_grupos(revuelto)


# --- Las dos causas de "insuficiente" (B1b) ---------------------------------


def test_distingue_poco_material_de_material_no_repartible(ruta_ontologia: Path):
    """Una familia con 600 fotos de un solo fotógrafo no tiene el mismo
    problema que una con 40 fotos de 40 fotógrafos, y el consejo tampoco es
    el mismo: conseguir más fotos sirve para la segunda; para la primera hace
    falta material de más fotógrafos, que es un problema distinto."""
    onto = cargar_ontologia(ruta_ontologia)
    de_un_fotografo = [fila(i, "unico", "OrdenZ", "FamUnica") for i in range(600)]
    escasa = [fila(1000 + i, f"nat{i}", "OrdenZ", "FamPobre") for i in range(40)]
    filas = de_un_fotografo + escasa

    asignacion = asignar_grupos(filas)
    _, decisiones = aplicar_regla_admision(filas, asignacion, onto)

    assert decisiones["FamUnica"] == DECISION_SIN_REPARTO
    assert decisiones["FamPobre"] == DECISION_MATERIAL_ESCASO
    assert DECISION_SIN_REPARTO != DECISION_MATERIAL_ESCASO


def test_el_resumen_expone_el_diagnostico_de_cada_familia(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = [fila(i, "unico", "OrdenZ", "FamUnica") for i in range(600)]
    _, resumen = particionar(filas, onto)

    diagnostico = resumen["diagnostico_familias"]["FamUnica"]
    assert diagnostico["decision"] == DECISION_SIN_REPARTO
    assert diagnostico["imagenes"] == 600
    assert diagnostico["observadores"] == 1


def test_el_reporte_da_el_consejo_correcto_a_cada_causa():
    """El consejo actual —"o se consiguen más imágenes para ellas, o se
    sustituyen por otras"— es lo contrario de lo que hace falta para una
    familia que ya tiene 600 fotografías."""
    resumen = {
        "total": 640,
        "por_split": {"train": 448, "val": 96, "test": 96},
        "decisiones": {
            "FamUnica": DECISION_SIN_REPARTO,
            "FamPobre": DECISION_MATERIAL_ESCASO,
        },
        "diagnostico_familias": {
            "FamUnica": {
                "decision": DECISION_SIN_REPARTO,
                "imagenes": 600,
                "observadores": 1,
            },
            "FamPobre": {
                "decision": DECISION_MATERIAL_ESCASO,
                "imagenes": 40,
                "observadores": 40,
            },
        },
        "por_clase": {},
        "anonimos_por_split": {"train": 0, "val": 0, "test": 0},
    }
    texto = reporte_markdown(resumen)

    # Cada familia debe caer DENTRO del bloque de su causa: no basta con que
    # ambos consejos aparezcan sueltos en algún lugar del documento.
    encabezado_reparto = "### No se pudieron repartir: hacen falta **más fotógrafos**"
    encabezado_escaso = "### Material insuficiente: hacen falta **más imágenes**"
    assert encabezado_reparto in texto and encabezado_escaso in texto

    bloque_reparto, bloque_escaso = texto.split(encabezado_reparto)[1].split(
        encabezado_escaso
    )

    assert "FamUnica" in bloque_reparto and "FamUnica" not in bloque_escaso
    assert "600" in bloque_reparto  # el material que sí tiene
    assert "1 fotógrafo" in bloque_reparto  # la causa real

    assert "FamPobre" in bloque_escaso and "FamPobre" not in bloque_reparto
    assert "40" in bloque_escaso

    # El consejo engañoso desaparece: sustituir una familia con 600 fotos por
    # otra es exactamente lo contrario de lo que hace falta.
    assert "se sustituyen por otras" not in texto


def test_el_umbral_de_escasez_no_es_la_suma_de_los_minimos(ruta_ontologia: Path):
    """Contraejemplo del revisor: 190 imágenes de 19 fotógrafos distintos.

    Con la suma de los mínimos (150 + 30 = 180) como umbral, 190 imágenes
    parecen "de sobra" y la familia se diagnostica como mal repartida. Pero
    con un reparto proporcional 70/15/15, a train le tocan ~133 imágenes,
    por debajo de su mínimo de 150: el problema es que no hay bastante
    material, no que esté mal distribuido. Y con 19 fotógrafos distintos,
    "hacen falta más fotógrafos" es exactamente el consejo falso: lo que
    falta son más FOTOS, no más personas.
    """
    onto = cargar_ontologia(ruta_ontologia)  # minimos: 150 train / 30 test
    filas = muchas(190, orden="OrdenZ", familia="FamMedia", por_observador=10)
    asignacion = asignar_grupos(filas)
    _, decisiones = aplicar_regla_admision(filas, asignacion, onto)

    assert decisiones["FamMedia"] == DECISION_MATERIAL_ESCASO, (
        "190 imágenes de 19 fotógrafos no llegan al mínimo de train con un "
        "reparto proporcional: es escasez de material, no mal reparto"
    )


def test_material_concentrado_en_uno_o_dos_fotografos_sigue_siendo_sin_reparto(
    ruta_ontologia: Path,
):
    """Contraparte del caso anterior: con material de sobra concentrado en muy
    pocas personas, el diagnóstico correcto sigue siendo SIN_REPARTO."""
    onto = cargar_ontologia(ruta_ontologia)
    filas = [fila(i, "prolifico", "OrdenZ", "FamConcentrada") for i in range(590)] + [
        fila(590 + i, "ocasional", "OrdenZ", "FamConcentrada") for i in range(10)
    ]
    asignacion = asignar_grupos(filas)
    _, decisiones = aplicar_regla_admision(filas, asignacion, onto)

    assert decisiones["FamConcentrada"] == DECISION_SIN_REPARTO


def test_el_reporte_no_inventa_secciones_si_todas_las_familias_entran():
    resumen = {
        "total": 100,
        "por_split": {"train": 70, "val": 15, "test": 15},
        "decisiones": {"FamA": DECISION_ADMITIDA},
        "diagnostico_familias": {
            "FamA": {"decision": DECISION_ADMITIDA, "imagenes": 100, "observadores": 9}
        },
        "por_clase": {},
        "anonimos_por_split": {"train": 0, "val": 0, "test": 0},
    }
    texto = reporte_markdown(resumen)
    assert "Todas las familias alcanzaron el umbral" in texto


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


# --- Persistencia de la partición entre corridas (B3) ------------------------


def escenario_corrida(n_obs=60, semilla=0, desde=0, prefijo="nat"):
    """Observadores de tamanos dispares, cada uno aportando a varias familias.

    Los tamanos irregulares importan: el algoritmo recorre los observadores de
    mayor a menor, asi que anadir imagenes reordena esa cola y, sin memoria,
    arrastra a media poblacion a otro split.
    """
    rng = random.Random(semilla)
    observadores = [f"{prefijo}_{rng.randrange(10**9):09d}" for _ in range(n_obs)]
    familias = [f"Fam{i:02d}" for i in range(4)]
    filas: list[dict] = []
    oid = desde
    for j, observador in enumerate(observadores):
        for k in range(rng.randint(10, 60)):
            filas.append(fila(oid, observador, "OrdenZ", familias[(j + k) % 4]))
            oid += 1
    return filas, observadores


def ampliar(filas, observadores, *, semilla=500, n_extra=800):
    """Segunda corrida: mas imagenes de los mismos, repartidas de otra forma."""
    rng = random.Random(semilla)
    return filas + [
        fila(90_000 + i, observadores[rng.randrange(len(observadores))],
             "OrdenZ", f"Fam{i % 4:02d}")
        for i in range(n_extra)
    ]


def test_los_observadores_ya_asignados_conservan_su_split():
    filas, observadores = escenario_corrida()
    previa = {observadores[0]: "test", observadores[1]: "test", observadores[2]: "val"}
    asignacion = asignar_grupos(filas, asignacion_previa=previa)
    for observador, split in previa.items():
        assert asignacion[observador] == split


@pytest.mark.parametrize("semilla", [0, 1, 2, 3, 4])
def test_una_segunda_corrida_con_datos_nuevos_no_mueve_a_nadie(semilla: int):
    """El defecto que esto previene no lo detectaria ninguna otra prueba.

    `asignar_grupos` es determinista dentro de una corrida pero no era estable
    entre corridas: al anadir imagenes y observadores, la mitad de los
    fotografos cambiaba de split y algunos pasaban de examen a aprendizaje. Un
    modelo entrenado entre las dos corridas quedaria evaluado contra un examen
    que ya vio, y nada lo delataria: cada corrida es internamente consistente
    y las pruebas siguen en verde.
    """
    filas1, observadores = escenario_corrida(semilla=semilla)
    primera = asignar_grupos(filas1)

    nuevas, nuevos = escenario_corrida(
        n_obs=10, semilla=900 + semilla, desde=200_000, prefijo="nuevo"
    )
    ampliadas = ampliar(filas1, observadores, semilla=500 + semilla) + nuevas

    segunda = asignar_grupos(ampliadas, asignacion_previa=primera)

    movidos = [o for o in observadores if primera[o] != segunda[o]]
    assert movidos == [], f"{len(movidos)} de {len(observadores)} cambiaron de split"
    assert set(nuevos) <= set(segunda), "los observadores nuevos si deben repartirse"


@pytest.mark.parametrize("semilla", [0, 1, 2, 3, 4])
def test_sin_asignacion_previa_la_segunda_corrida_si_mueve_gente(semilla: int):
    """Contraprueba: sin el artefacto persistido, el problema sigue ahi.

    Confirma que la prueba anterior mide la persistencia y no una estabilidad
    que el algoritmo tuviera por casualidad.
    """
    filas1, observadores = escenario_corrida(semilla=semilla)
    primera = asignar_grupos(filas1)
    ampliadas = ampliar(filas1, observadores, semilla=500 + semilla)

    sin_memoria = asignar_grupos(ampliadas)

    movidos = [o for o in observadores if primera[o] != sin_memoria[o]]
    assert len(movidos) > len(observadores) // 4, (
        "sin memoria se esperaba inestabilidad notable; si esta prueba empieza a "
        "fallar, la contraprueba dejo de demostrar nada"
    )
    de_examen_a_aprendizaje = [
        o for o in observadores if primera[o] == "test" and sin_memoria[o] == "train"
    ]
    assert de_examen_a_aprendizaje, "el caso grave: fotografos del examen pasan a train"


def test_la_asignacion_va_y_vuelve_del_disco(tmp_path: Path):
    ruta = tmp_path / ARCHIVO_ASIGNACION
    asignacion = {"ana": "train", "beto": "val", "caro": "test"}
    escribir_asignacion(asignacion, ruta)
    assert leer_asignacion(ruta) == asignacion


def test_el_archivo_de_asignacion_es_legible_y_explica_por_que_existe(tmp_path: Path):
    """Es el tipo de artefacto que alguien borra creyéndolo caché."""
    ruta = tmp_path / ARCHIVO_ASIGNACION
    escribir_asignacion({"ana": "train"}, ruta)
    texto = ruta.read_text(encoding="utf-8")
    assert "NO BORRAR" in texto
    assert "caché" in texto.lower()
    assert "ana: train" in texto


def test_leer_una_asignacion_inexistente_da_un_mapa_vacio(tmp_path: Path):
    assert leer_asignacion(tmp_path / "no_existe.yaml") == {}


def test_una_asignacion_con_valor_no_textual_es_un_error_legible(tmp_path: Path):
    """Un desliz de indentación en YAML convierte fácilmente el valor en una
    lista o un mapa. Antes eso producía `TypeError: unhashable type` crudo, en
    vez del mensaje legible que ya daba un YAML sintácticamente roto."""
    ruta = tmp_path / ARCHIVO_ASIGNACION
    ruta.write_text("ana:\n  - train\n  - test\n", encoding="utf-8")
    with pytest.raises(ErrorAsignacion):
        leer_asignacion(ruta)


def test_una_asignacion_con_clave_no_textual_es_un_error_legible(tmp_path: Path):
    """Una clave numérica (`123: train`, típico de un YAML sin comillas) debe
    fallar igual de ruidosamente que un valor inválido, no colarse convertida
    a texto en silencio."""
    ruta = tmp_path / ARCHIVO_ASIGNACION
    ruta.write_text("123: train\nana: test\n", encoding="utf-8")
    with pytest.raises(ErrorAsignacion):
        leer_asignacion(ruta)


def test_una_asignacion_corrupta_es_un_error_y_no_un_silencio(tmp_path: Path):
    """Ignorar en silencio un archivo ilegible reintroduciría el defecto:
    la corrida repartiría todo de nuevo creyendo que no había nada guardado."""
    ruta = tmp_path / ARCHIVO_ASIGNACION
    ruta.write_text("ana: entrenamiento\n", encoding="utf-8")
    with pytest.raises(ErrorAsignacion):
        leer_asignacion(ruta)


def test_la_escritura_de_la_asignacion_es_atomica(tmp_path: Path, monkeypatch):
    """Este proyecto ya arrastró dos defectos críticos por truncar archivos
    antes de tener el contenido nuevo. Aquí lo truncado sería la partición."""
    import pipeline.splits as mod

    ruta = tmp_path / ARCHIVO_ASIGNACION
    escribir_asignacion({f"obs{i}": "train" for i in range(50)}, ruta)
    contenido_previo = ruta.read_text(encoding="utf-8")

    def _revienta(*args, **kwargs):
        raise OSError("fallo de disco simulado a mitad de la reescritura")

    monkeypatch.setattr(mod.yaml, "safe_dump", _revienta)

    with pytest.raises(OSError):
        escribir_asignacion({"obs0": "test"}, ruta)

    assert ruta.read_text(encoding="utf-8") == contenido_previo
    assert len(leer_asignacion(ruta)) == 50
    assert sorted(p.name for p in tmp_path.iterdir()) == [ARCHIVO_ASIGNACION]


# --- Línea de comandos -------------------------------------------------------


def preparar_corrida(tmp_path: Path, ruta_ontologia: Path, filas: list[dict]):
    curado = tmp_path / "curado"
    curado.mkdir(parents=True, exist_ok=True)
    with (curado / "manifiesto_curado.csv").open("w", encoding="utf-8", newline="") as f:
        import csv

        escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
        escritor.writeheader()
        for f_ in filas:
            escritor.writerow({c: f_.get(c, "") for c in COLUMNAS_CURADO})
    destino = tmp_path / "splits"
    return [
        "--ontologia", str(ruta_ontologia),
        "--curado", str(curado),
        "--destino", str(destino),
        "--reporte", str(tmp_path / "reporte.md"),
    ], destino


def test_main_persiste_la_asignacion_y_la_reutiliza(tmp_path: Path, ruta_ontologia: Path):
    filas, observadores = escenario_corrida(n_obs=30)
    argv, destino = preparar_corrida(tmp_path, ruta_ontologia, filas)

    assert main(argv) == 0
    primera = leer_asignacion(destino / ARCHIVO_ASIGNACION)
    assert set(primera) == set(observadores)

    # Segunda corrida con más material: nadie se mueve.
    ampliadas = ampliar(filas, observadores, n_extra=300)
    argv2, destino2 = preparar_corrida(tmp_path / "b", ruta_ontologia, ampliadas)
    # Se reutiliza el mismo directorio de destino, que es donde vive el artefacto.
    argv2[argv2.index("--destino") + 1] = str(destino)
    assert main(argv2) == 0
    segunda = leer_asignacion(destino / ARCHIVO_ASIGNACION)
    assert segunda == primera


def test_main_solo_regenera_la_asignacion_con_la_opcion_explicita(
    tmp_path: Path, ruta_ontologia: Path
):
    """Regenerar desde cero tiene que ser una decisión, nunca un accidente."""
    filas, observadores = escenario_corrida(n_obs=30)
    argv, destino = preparar_corrida(tmp_path, ruta_ontologia, filas)
    main(argv)

    # Se falsea la asignación guardada: si la corrida la respeta, la reutilizó.
    falsa = {o: "test" for o in observadores}
    escribir_asignacion(falsa, destino / ARCHIVO_ASIGNACION)

    assert main(argv) == 0
    assert leer_asignacion(destino / ARCHIVO_ASIGNACION) == falsa

    assert main(argv + ["--regenerar-asignacion"]) == 0
    regenerada = leer_asignacion(destino / ARCHIVO_ASIGNACION)
    assert regenerada != falsa
    assert set(regenerada.values()) == {"train", "val", "test"}


def test_main_no_toca_el_reporte_del_repositorio(tmp_path: Path, ruta_ontologia: Path):
    """El destino del reporte es configurable: las pruebas no pueden escribir
    en docs/ del repositorio real."""
    filas, _ = escenario_corrida(n_obs=10)
    argv, _ = preparar_corrida(tmp_path, ruta_ontologia, filas)
    main(argv)
    assert (tmp_path / "reporte.md").exists()


def test_main_para_si_la_asignacion_guardada_es_ilegible(
    tmp_path: Path, ruta_ontologia: Path, capsys
):
    """Ante un artefacto corrupto no puede repartir de cero por su cuenta: eso
    movería observadores de examen a aprendizaje sin que nadie lo pidiera."""
    filas, _ = escenario_corrida(n_obs=10)
    argv, destino = preparar_corrida(tmp_path, ruta_ontologia, filas)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / ARCHIVO_ASIGNACION).write_text("ana: entrenamiento\n", encoding="utf-8")

    codigo = main(argv)

    assert codigo == SALIDA_ASIGNACION_INVALIDA
    assert codigo != 0
    assert not (destino / "train.csv").exists()
    assert "--regenerar-asignacion" in capsys.readouterr().out


# --- Límite conocido del reparto estratificado (ver PESO_CLASE en pipeline/splits.py) ---
#
# Estas pruebas no arreglan nada: documentan un límite ya aceptado como deuda.
# El reparto estratificado llega a cero familias mal plegadas cuando los
# fotógrafos de una familia aportan cantidades PARECIDAS de fotos. Cuando
# aportan cantidades muy dispares -un fotógrafo prolífico y varios
# ocasionales, lo habitual fuera de un escenario sintético- una fracción de
# familias sigue plegándose aunque casi siempre eran repartibles.


def _bloques_parecidos(rng: random.Random, total: int, n: int) -> list[int]:
    """Reparto equitativo entre los `n` fotógrafos: el régimen que sí funciona."""
    del rng  # sin aleatoriedad: es justamente el caso "cantidades parecidas"
    base = total // n
    return [base] * n


def _bloques_desiguales(rng: random.Random, total: int, n: int) -> list[int]:
    """Un fotógrafo prolífico y varios ocasionales, no partes iguales."""
    pesos = [rng.random() ** 3 for _ in range(n)]
    suma = sum(pesos)
    return [max(1, int(total * peso / suma)) for peso in pesos]


def escenario_mixto(
    *,
    seed: int,
    generador_bloques,
    n_familias_raras: int = 30,
    obs_por_familia: int = 3,
    total_familia: int = 600,
    n_familias_comunes: int = 6,
    obs_comunes: int = 25,
) -> tuple[list[dict], dict[str, list[int]]]:
    """Mezcla realista: familias comunes con fotógrafos compartidos (que no se
    pliegan, y generan la contención de cupo que sí ocurre con datos reales) y
    familias raras con fotógrafos dedicados, en cantidades iguales o dispares
    según `generador_bloques`."""
    rng = random.Random(seed)
    filas: list[dict] = []
    oid = 0
    bloques_por_familia: dict[str, list[int]] = {}
    for i in range(n_familias_raras):
        familia = f"Rara{i:02d}"
        bloques = generador_bloques(rng, total_familia, obs_por_familia)
        bloques_por_familia[familia] = bloques
        for j, tamano in enumerate(bloques):
            observador = f"{familia}_obs{j}"
            for _ in range(tamano):
                filas.append(fila(oid, observador, "OrdenZ", familia))
                oid += 1

    observadores_comunes = [f"comun_{k}" for k in range(obs_comunes)]
    for fam_i in range(n_familias_comunes):
        familia = f"Comun{fam_i}"
        for observador in observadores_comunes:
            n = rng.randint(20, 80)
            for _ in range(n):
                filas.append(fila(oid, observador, "OrdenZ", familia))
                oid += 1
    return filas, bloques_por_familia


def _tasa_de_plegado(
    filas: list[dict], bloques_por_familia: dict[str, list[int]], onto
) -> float:
    """Fracción de las familias "raras" que no llegan al umbral de admisión."""
    asignacion = asignar_grupos(filas)
    conteo: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for f in filas:
        conteo[f["familia"]][asignacion[f["observador"]]] += 1

    plegadas = 0
    for familia in bloques_por_familia:
        por_split = conteo[familia]
        suficiente = (
            por_split["train"] >= onto.minimo_familia_train
            and por_split["test"] >= onto.minimo_familia_test
        )
        if not suficiente:
            plegadas += 1
    return plegadas / len(bloques_por_familia)


@pytest.mark.parametrize("obs_por_familia", [3, 4])
def test_bloques_parecidos_no_pliega_ninguna_familia(ruta_ontologia: Path, obs_por_familia: int):
    """Fija el régimen que SÍ funciona, para que una regresión futura se note.

    Con fotógrafos que aportan cantidades parecidas -incluso con solo 3 o 4
    por familia-, el reparto estratificado no debería plegar ninguna."""
    onto = cargar_ontologia(ruta_ontologia)
    filas, bloques_por_familia = escenario_mixto(
        seed=0, generador_bloques=_bloques_parecidos, obs_por_familia=obs_por_familia
    )
    tasa = _tasa_de_plegado(filas, bloques_por_familia, onto)
    assert tasa == 0.0, (
        f"con bloques parecidos no debería plegarse ninguna familia (tasa={tasa:.1%})"
    )


@pytest.mark.parametrize(
    "obs_por_familia, minimo, maximo",
    [(3, 0.10, 0.60), (4, 0.05, 0.40)],
)
def test_bloques_desiguales_documentan_el_limite_conocido(
    ruta_ontologia: Path, obs_por_familia: int, minimo: float, maximo: float
):
    """Documenta el límite conocido: no es el comportamiento deseado, es la
    realidad actual del algoritmo con contribuciones desiguales por fotógrafo.

    No se marca como fallo esperado (no hay `xfail`): esta prueba debe pasar y
    seguir describiendo la realidad. Si el rango deja de contener la tasa
    medida, o bien el algoritmo mejoró (buena noticia, hay que angostar el
    rango) o bien empeoró (regresión, hay que investigar) -pero de cualquier
    forma el comentario de PESO_CLASE en pipeline/splits.py quedó desactualizado
    y hay que revisarlo junto con esta prueba.
    """
    onto = cargar_ontologia(ruta_ontologia)
    filas, bloques_por_familia = escenario_mixto(
        seed=0, generador_bloques=_bloques_desiguales, obs_por_familia=obs_por_familia
    )
    tasa = _tasa_de_plegado(filas, bloques_por_familia, onto)
    assert minimo < tasa <= maximo, (
        f"tasa de plegado observada {tasa:.1%} fuera del rango documentado "
        f"({minimo:.0%}, {maximo:.0%}] para {obs_por_familia} fotógrafos por familia"
    )
