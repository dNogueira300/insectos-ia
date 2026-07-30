"""Particionado train/val/test agrupado por observador y regla de admisión.

Agrupar por observador es la defensa contra la fuga de datos: las fotos de una
misma persona comparten cámara, fondo y a menudo el mismo individuo. Si se
reparten entre train y test, la métrica sube y el sistema falla en campo.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from pipeline.curacion import COLUMNAS_CURADO
from pipeline.ontologia import PREFIJO_OTROS, Ontologia, cargar_ontologia

PROPORCIONES = {"train": 0.70, "val": 0.15, "test": 0.15}

# Nombre del artefacto que guarda la asignación observador -> split. Vive
# junto a los CSV de los splits, en el mismo directorio de destino.
ARCHIVO_ASIGNACION = "asignacion_observadores.yaml"


class ErrorAsignacion(Exception):
    """El archivo de asignación existe pero no se puede interpretar."""


# Códigos de salida de la línea de comandos.
SALIDA_OK = 0
SALIDA_ASIGNACION_INVALIDA = 1


# Encabezado del artefacto. Se escribe siempre, y dice para qué sirve, porque
# es exactamente el tipo de archivo que alguien borra creyéndolo caché.
ENCABEZADO_ASIGNACION = """\
# ============================================================================
# NO BORRAR. ESTE ARCHIVO NO ES CACHÉ.
# ============================================================================
#
# Es la partición del dataset: qué fotógrafo quedó en aprendizaje (train), en
# validación (val) y en examen (test). Se guarda porque el reparto tiene que
# ser el mismo en todas las corridas del pipeline, y esta rama garantiza que
# habrá más de una: la lista de clases todavía no está cerrada, así que el
# dataset se volverá a descargar y a particionar al menos una vez.
#
# Sin este archivo, el algoritmo reparte de nuevo desde cero cada vez. Al
# añadir imágenes u observadores nuevos, buena parte de los fotógrafos cambia
# de lado, y algunos pasan de examen a aprendizaje. Un modelo entrenado antes
# de ese cambio quedaría evaluado contra un examen que ya vio: la métrica
# subiría y sería mentira. Nada lo detectaría, porque cada corrida es
# internamente consistente por separado y las pruebas siguen en verde.
#
# Si lo borras, esa garantía desaparece en silencio. Para rehacer el reparto a
# propósito -por ejemplo, si el dataset cambió tanto que la partición vieja ya
# no tiene sentido- usa la opción explícita:
#
#     python -m pipeline.splits --regenerar-asignacion
#
# y ten en cuenta que a partir de ahí cualquier modelo entrenado antes queda
# invalidado para efectos de evaluación.
#
# Formato: un mapa <observador>: <split>. Se puede leer y editar a mano.
# ============================================================================
"""


def leer_asignacion(ruta: Path) -> dict[str, str]:
    """Lee la asignación persistida. Devuelve `{}` si el archivo no existe.

    Un archivo ilegible o con splits desconocidos es un error, no un `{}`:
    tragárselo en silencio haría que la corrida repartiera todo de nuevo
    creyendo que no había nada guardado, que es justo el defecto que este
    artefacto existe para evitar.
    """
    ruta = Path(ruta)
    if not ruta.is_file():
        return {}

    try:
        datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ErrorAsignacion(f"{ruta}: no es un YAML válido ({error})") from error

    if datos is None:
        return {}
    if not isinstance(datos, dict):
        raise ErrorAsignacion(f"{ruta}: se esperaba un mapa <observador>: <split>")

    asignacion: dict[str, str] = {}
    for observador, split in datos.items():
        # Un YAML con una sangría o un guion de más convierte fácilmente una
        # línea `<observador>: <split>` en una lista o en otro mapa, y una
        # clave sin comillas que parezca número se lee como int. Ambos casos
        # deben fallar aquí, con un mensaje que diga qué se esperaba, en vez
        # de llegar a `split not in PROPORCIONES` y reventar con
        # `TypeError: unhashable type` cuando el valor no es hasheable.
        if not isinstance(observador, str):
            raise ErrorAsignacion(
                f"{ruta}: la clave {observador!r} no es texto; se esperaba el nombre "
                "de un observador (una cadena). Revisar la línea en el YAML: una "
                "clave sin comillas que parezca número o una lista se leen como otra "
                "cosa, no como texto."
            )
        if not isinstance(split, str) or split not in PROPORCIONES:
            raise ErrorAsignacion(
                f"{ruta}: el observador '{observador}' tiene el valor {split!r}, que "
                f"no es uno de los splits válidos ({', '.join(PROPORCIONES)}). Si el "
                "valor es una lista o un mapa en vez de una palabra, suele ser una "
                "sangría de más: la línea debe quedar `<observador>: <split>`, sin "
                "guiones debajo."
            )
        asignacion[observador] = split
    return asignacion


def escribir_asignacion(asignacion: dict[str, str], ruta: Path) -> None:
    """Persiste la asignación de forma atómica.

    Nunca trunca `ruta` directamente: arma el contenido completo en un archivo
    temporal junto al destino y lo promueve con `os.replace` solo cuando la
    escritura terminó sin fallos (mismo patrón que `escribir_manifiesto` en
    `pipeline/descarga.py` y que `importar` en `pipeline/bd.py`). Lo que se
    perdería aquí al truncar no son unas filas: es la partición entera, y con
    ella la única garantía de que el conjunto de examen sigue siendo el mismo
    entre corridas.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta_temporal = ruta.with_name(f".{ruta.name}.tmp-{os.getpid()}")
    ruta_temporal.unlink(missing_ok=True)  # restos de una corrida interrumpida

    try:
        cuerpo = yaml.safe_dump(
            dict(sorted(asignacion.items())),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=True,
        )
        ruta_temporal.write_text(ENCABEZADO_ASIGNACION + cuerpo, encoding="utf-8")
        os.replace(ruta_temporal, ruta)
    except Exception:
        ruta_temporal.unlink(missing_ok=True)
        raise

# Placeholder que pipeline.inat asigna al campo `observador` cuando la
# observación de iNaturalist no trae usuario registrado (ver
# `Observacion.observador` en pipeline/inat.py). No representa a una persona:
# es un cajón donde caen observaciones anónimas de gente distinta. Se
# mantiene como un observador más para el agrupamiento (separarlas sin saber
# quién las tomó arriesgaría fuga si en realidad compartieran fotógrafo),
# pero su peso debe quedar visible en el reporte.
OBSERVADOR_DESCONOCIDO = "desconocido"

# Etiqueta de las imágenes que no tienen familia declarada (la cuota de orden).
# A efectos de estratificación son una clase más: también alimentan la cabeza
# de orden del modelo y también conviene repartirlas bien.
SIN_FAMILIA = "_sin_familia"

# Vocabulario de la regla de admisión. Hay DOS maneras distintas de no llegar
# al umbral, y confundirlas produce el consejo equivocado en el documento con
# el que la Facultad decide qué clases entran:
#
#   - MATERIAL_ESCASO: la familia no tiene imágenes suficientes ni sumando
#     todos los splits. Ninguna asignación podría salvarla. Lo que hace falta
#     son más fotografías.
#   - SIN_REPARTO: la familia tiene material de sobra, pero viene de tan pocos
#     fotógrafos que el particionado agrupado por observador no pudo dejar lo
#     mínimo en aprendizaje y en examen a la vez. Conseguir más fotos de las
#     mismas personas no arregla nada: hacen falta fotos de MÁS FOTÓGRAFOS.
#
# El valor de MATERIAL_ESCASO se mantiene en "agrupada" a propósito: es el caso
# base y es el que ya consumían el reporte y las pruebas anteriores.
DECISION_ADMITIDA = "admitida"
DECISION_MATERIAL_ESCASO = "agrupada"
DECISION_SIN_REPARTO = "agrupada_sin_reparto"

# Cuánto pesa el déficit POR CLASE frente al déficit global al elegir el split
# de un observador. Con una sola clase ambos términos coinciden y el valor es
# irrelevante; con observadores especializados por familia -el caso real en
# taxonomía- es lo único que impide que todos los fotógrafos de una familia
# caigan del mismo lado. Se eligió empíricamente: ver `asignar_grupos`.
#
# LÍMITE CONOCIDO (deuda documentada, no un arreglo pendiente): el régimen
# donde este valor se midió, y donde el reparto estratificado llega a CERO
# familias mal plegadas, es aquel en que los fotógrafos de una misma familia
# aportan cantidades PARECIDAS de fotos (ver
# `test_bloques_parecidos_no_pliega_ninguna_familia` en tests/test_splits.py).
#
# Cuando aportan cantidades muy dispares -un fotógrafo prolífico y varios
# ocasionales, que es lo habitual fuera de un escenario sintético- el reparto
# sigue plegando una fracción de familias pese a que casi siempre son
# repartibles: en un caso medido, bloques de 311, 145 y 144 imágenes admitían
# un reparto válido (uno por split) que el algoritmo no encontró. Con datos
# sintéticos de contraste se midió una tasa de plegado del 26,6% con 3
# fotógrafos por familia y del 9,6% con 4 (ver
# `test_bloques_desiguales_documentan_el_limite_conocido`). Además, 0.8 no es
# el valor óptimo fuera del régimen donde se ajustó: con 3 fotógrafos por
# familia, 0.7 da mejor resultado, y con 4, 1.0 da un resultado hasta tres
# veces mejor. En el escenario mixto realista -familias comunes con
# fotógrafos compartidos, más algunas raras con fotógrafos dedicados- el
# reparto sí funciona limpio, que es el caso que más importa en la práctica.
#
# Este parámetro debe re-medirse cuando exista la lista real de clases del
# entomólogo: los números de arriba son de escenarios sintéticos, y la
# distribución real de fotógrafos por familia amazónica puede diferir.
PESO_CLASE = 0.8


def _clave_clase(fila: dict) -> str:
    """Clase a efectos de estratificación: la familia dentro de su orden."""
    return f"{fila['orden']}/{fila['familia'] or SIN_FAMILIA}"


def asignar_grupos(
    filas: list[dict],
    *,
    proporciones: dict[str, float] = PROPORCIONES,
    asignacion_previa: dict[str, str] | None = None,
    peso_clase: float = PESO_CLASE,
) -> dict[str, str]:
    """Asigna cada observador a un split, estratificando por clase.

    Balancear solo el total global no basta. Cuando los observadores se
    especializan por familia -lo normal en taxonomía, y lo seguro en las
    familias amazónicas raras, que dependen de un puñado de naturalistas
    locales- un criterio ciego a la clase puede mandar a todos los fotógrafos
    de una familia al mismo split. La familia queda entonces sin material en
    examen (o sin material en aprendizaje) y la regla de admisión la pliega a
    `Otros_`, aunque tenga cientos de fotografías.

    El criterio es un déficit relativo ponderado. Para cada split se mide qué
    fracción de su cupo sigue vacía, en dos escalas:

    - el déficit global: cuánto le falta al split respecto de su cupo total;
    - el déficit por clase: cuánto le falta respecto del cupo de cada clase,
      promediado según cuánto aporta el observador a cada una.

    Se elige el split con mayor déficit combinado, con `peso_clase` decidiendo
    cuánto manda cada término. Así un observador que aporta imágenes de una
    familia escasa va donde esa familia lo necesita, no donde convenga al
    total.

    El déficit se mide **relativo al cupo** (fracción vacía) y no en imágenes
    absolutas, y eso no es un detalle de estilo. Los observadores son bloques
    indivisibles: una familia con cuatro fotógrafos de 150 fotos cada uno solo
    puede repartirse en trozos de 150. Con un déficit absoluto, el split
    grande sigue pareciendo el más necesitado hasta pasarse de largo, y los
    cuatro bloques acaban en aprendizaje con el examen vacío. Con el déficit
    relativo, en cuanto un split cubre su parte proporcional cede el turno, y
    los splits chicos reciben su bloque a tiempo. Además hace comparables los
    dos términos sin normalizar nada a mano: ambos son fracciones.

    Se conservan las dos propiedades que ya estaban probadas:

    - **ningún observador queda en dos splits**, porque el observador es la
      unidad indivisible de la asignación;
    - **el resultado es determinista e independiente del orden de llegada**,
      porque los observadores se recorren ordenados por tamaño descendente con
      el nombre como desempate, y el empate entre splits se rompe siempre por
      el orden fijo de `proporciones`.

    Cuando la especialización es extrema -tres fotógrafos para toda una
    familia- el reparto global se aleja de 70/15/15, porque con tres bloques
    indivisibles la única forma de que la familia tenga examen es dar uno a
    cada split. Es el intercambio correcto y está elegido a propósito: una
    proporción global bonita con una familia ausente del examen es peor que
    una proporción torcida con todas las familias evaluables. Con datos
    reales, donde la mayoría de las clases comparte fotógrafos, el desvío es
    pequeño.

    `asignacion_previa` es la asignación persistida de corridas anteriores:
    esos observadores conservan su split y ocupan cupo antes de repartir a los
    nuevos. Ver `leer_asignacion` para por qué eso importa.
    """
    tamanos: dict[str, int] = defaultdict(int)
    aporte: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    total_clase: dict[str, int] = defaultdict(int)
    for fila in filas:
        observador = fila["observador"]
        clase = _clave_clase(fila)
        tamanos[observador] += 1
        aporte[observador][clase] += 1
        total_clase[clase] += 1

    total = sum(tamanos.values()) or 1
    cupos = {split: proporcion * total for split, proporcion in proporciones.items()}
    cupos_clase = {
        clase: {split: proporcion * n for split, proporcion in proporciones.items()}
        for clase, n in total_clase.items()
    }
    asignados: dict[str, int] = {split: 0 for split in proporciones}
    asignados_clase: dict[str, dict[str, int]] = {
        clase: {split: 0 for split in proporciones} for clase in total_clase
    }
    asignacion: dict[str, str] = {}

    def _ocupar(observador: str, split: str) -> None:
        asignacion[observador] = split
        asignados[split] += tamanos[observador]
        for clase, n in aporte[observador].items():
            asignados_clase[clase][split] += n

    # Primero los observadores heredados: su split no se discute, pero sí
    # consume cupo, para que los nuevos se repartan sobre lo que queda libre.
    previa = asignacion_previa or {}
    for observador in sorted(tamanos, key=lambda o: (-tamanos[o], o)):
        split = previa.get(observador)
        if split in proporciones:
            _ocupar(observador, split)

    # De mayor a menor, con el nombre como desempate: el resultado no depende
    # del orden en que llegaron las filas.
    for observador in sorted(tamanos, key=lambda o: (-tamanos[o], o)):
        if observador in asignacion:
            continue

        def deficit(split: str, observador: str = observador) -> float:
            # Un cupo de cero (proporción 0) no es un split candidato: se le da
            # el déficit más bajo posible en vez de dividir entre cero.
            if not cupos[split]:
                return float("-inf")
            global_ = (cupos[split] - asignados[split]) / cupos[split]
            por_clase = 0.0
            for clase, n in aporte[observador].items():
                cupo = cupos_clase[clase][split]
                if not cupo:
                    continue
                faltante = cupo - asignados_clase[clase][split]
                por_clase += (n / tamanos[observador]) * (faltante / cupo)
            return (1.0 - peso_clase) * global_ + peso_clase * por_clase

        _ocupar(observador, max(cupos, key=deficit))

    return asignacion


def _diagnosticar_familias(
    filas: list[dict], asignacion: dict[str, str], onto: Ontologia
) -> dict[str, dict]:
    """Por familia: imágenes, fotógrafos distintos, conteo por split y decisión."""
    datos: dict[str, dict] = {}
    for fila in filas:
        familia = fila["familia"]
        if not familia:
            continue
        entrada = datos.setdefault(
            familia,
            {
                "imagenes": 0,
                "observadores": set(),
                "por_split": {split: 0 for split in PROPORCIONES},
            },
        )
        entrada["imagenes"] += 1
        entrada["observadores"].add(fila["observador"])
        entrada["por_split"][asignacion[fila["observador"]]] += 1

    # El umbral de escasez NO es la suma de los mínimos (150 + 30 = 180 con los
    # valores actuales). Esa suma ignora que el reparto real es PROPORCIONAL:
    # a train solo le toca el 70% del total, no el total entero. Con 180
    # imágenes, train recibe apenas ~126 (180 * 0.70), por debajo de su
    # mínimo de 150 -y lo mismo puede pasar por el lado de test-, así que una
    # familia justo por encima de 180 puede seguir sin llegar por pura
    # escasez, no por mal reparto. El umbral correcto es el total que hace
    # falta para que CADA split alcance su propio mínimo con su proporción; el
    # más exigente de los dos manda (con los mínimos actuales, es train: unos
    # 214 = 150 / 0.70).
    #
    # Por qué esto ya basta para no culpar a los fotógrafos equivocados: si
    # una familia tiene MENOS imágenes que este umbral, no importa cuántos
    # fotógrafos distintos las tomaron -3 o 30-, el reparto proporcional
    # jamás le daría a train su mínimo. "Pocas fotos" y "muchos fotógrafos" no
    # pueden coexistir del lado de SIN_REPARTO: el número de observadores que
    # ya viaja en el diagnóstico (`entrada["observadores"]`, usado más abajo
    # en el reporte) es precisamente lo que confirma, familia por familia, que
    # el problema del lado de arriba del umbral es de concentración de
    # fotógrafos y no de cantidad de material.
    umbral_escasez = max(
        onto.minimo_familia_train / PROPORCIONES["train"],
        onto.minimo_familia_test / PROPORCIONES["test"],
    )
    for entrada in datos.values():
        suficiente = (
            entrada["por_split"]["train"] >= onto.minimo_familia_train
            and entrada["por_split"]["test"] >= onto.minimo_familia_test
        )
        if suficiente:
            decision = DECISION_ADMITIDA
        elif entrada["imagenes"] < umbral_escasez:
            # Ni juntando todos los splits llega al mínimo que el reparto
            # proporcional necesita: el problema es la cantidad de material,
            # y ninguna asignación podría arreglarlo.
            decision = DECISION_MATERIAL_ESCASO
        else:
            # Hay material de sobra y aun así no se pudo repartir. Con el
            # particionado agrupado por observador, la causa es que ese
            # material viene de demasiado pocos fotógrafos.
            decision = DECISION_SIN_REPARTO
        entrada["decision"] = decision
        entrada["observadores"] = len(entrada["observadores"])
    return datos


def aplicar_regla_admision(
    filas: list[dict], asignacion: dict[str, str], onto: Ontologia
) -> tuple[list[dict], dict[str, str]]:
    """Reetiqueta como `Otros_<Orden>` las familias que no llegan al umbral.

    La decisión distingue las dos causas posibles de no llegar (ver el
    vocabulario `DECISION_*`), porque el consejo que hay que dar a la Facultad
    es distinto en cada caso.
    """
    diagnostico = _diagnosticar_familias(filas, asignacion, onto)
    decisiones = {familia: datos["decision"] for familia, datos in diagnostico.items()}

    salida = []
    for fila in filas:
        copia = dict(fila)
        if copia["familia"] and decisiones[copia["familia"]] != DECISION_ADMITIDA:
            copia["familia"] = f"{PREFIJO_OTROS}{copia['orden']}"
        salida.append(copia)
    return salida, decisiones


def particionar(
    filas: list[dict],
    onto: Ontologia,
    *,
    asignacion_previa: dict[str, str] | None = None,
) -> tuple[dict[str, list[dict]], dict]:
    """Devuelve las tres particiones y el resumen de lo decidido."""
    asignacion = asignar_grupos(filas, asignacion_previa=asignacion_previa)
    diagnostico = _diagnosticar_familias(filas, asignacion, onto)
    reetiquetadas, decisiones = aplicar_regla_admision(filas, asignacion, onto)

    particiones: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for fila in reetiquetadas:
        particiones[asignacion[fila["observador"]]].append(fila)

    # Imágenes y observadores únicos por clase y split, contados sobre la
    # asignación real (las particiones ya resueltas), no sobre una estimación.
    # Es la única forma de detectar que un split "suficiente" en imágenes
    # puede, aun así, provenir de una sola persona.
    imagenes_por_clase: dict[str, dict[str, int]] = defaultdict(
        lambda: {"train": 0, "val": 0, "test": 0}
    )
    observadores_por_clase: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"train": set(), "val": set(), "test": set()}
    )
    anonimos_por_split: dict[str, int] = {"train": 0, "val": 0, "test": 0}
    for split, filas_split in particiones.items():
        for fila in filas_split:
            clase = f"{fila['orden']}/{fila['familia'] or '_sin_familia'}"
            imagenes_por_clase[clase][split] += 1
            observadores_por_clase[clase][split].add(fila["observador"])
            if fila["observador"] == OBSERVADOR_DESCONOCIDO:
                anonimos_por_split[split] += 1

    por_clase = {
        clase: {
            split: {
                "imagenes": imagenes_por_clase[clase][split],
                "observadores": len(observadores_por_clase[clase][split]),
            }
            for split in ("train", "val", "test")
        }
        for clase in imagenes_por_clase
    }

    previa = asignacion_previa or {}
    reusados = sum(1 for o in asignacion if previa.get(o) == asignacion[o])

    resumen = {
        "total": len(filas),
        "por_split": {split: len(v) for split, v in particiones.items()},
        "decisiones": decisiones,
        "diagnostico_familias": diagnostico,
        "por_clase": por_clase,
        "anonimos_por_split": anonimos_por_split,
        "asignacion": asignacion,
        "observadores_reusados": reusados,
        "observadores_nuevos": len(asignacion) - reusados,
    }
    return particiones, resumen


def escribir_particiones(particiones: dict[str, list[dict]], destino: Path) -> None:
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    for split, filas in particiones.items():
        with (destino / f"{split}.csv").open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
            escritor.writeheader()
            for fila in filas:
                escritor.writerow({c: fila.get(c, "") for c in COLUMNAS_CURADO})


def _bloque_causas(resumen: dict) -> list[str]:
    """Las familias que no entraron, separadas por causa y con su consejo.

    Es la parte del reporte que la Facultad usa para decidir qué hacer con
    cada familia, así que el consejo tiene que corresponder a la causa: pedir
    más fotografías para una familia que ya tiene seiscientas de un solo
    fotógrafo no arregla nada, y sugerir sustituirla es lo contrario de lo
    que hace falta.
    """
    decisiones = resumen.get("decisiones") or {}
    diagnostico = resumen.get("diagnostico_familias") or {}

    escasas = sorted(f for f, d in decisiones.items() if d == DECISION_MATERIAL_ESCASO)
    sin_reparto = sorted(f for f, d in decisiones.items() if d == DECISION_SIN_REPARTO)
    if not escasas and not sin_reparto:
        return ["", "Todas las familias alcanzaron el umbral."]

    total = len(escasas) + len(sin_reparto)
    lineas = [
        "",
        f"**{total} familias no alcanzaron el umbral** y quedaron dentro de "
        "`Otros_<Orden>`. No todas por el mismo motivo, y el motivo cambia qué hay "
        "que hacer con cada una:",
    ]

    def _detalle(familia: str) -> str:
        datos = diagnostico.get(familia) or {}
        if not datos:
            return f"- `{familia}`"
        return (
            f"- `{familia}`: {datos['imagenes']} imágenes curadas de "
            f"{datos['observadores']} fotógrafo(s) distinto(s)."
        )

    if sin_reparto:
        lineas += [
            "",
            "### No se pudieron repartir: hacen falta **más fotógrafos**",
            "",
            "Estas familias **tienen material de sobra**. El problema es que ese "
            "material viene de muy pocas personas, y el particionado agrupa por "
            "fotógrafo -nunca por imagen suelta- para que las fotos de alguien no "
            "aparezcan a la vez en aprendizaje y en examen (§7 del diseño). Con "
            "pocos fotógrafos no hay forma de dejar el mínimo a ambos lados sin "
            "romper esa regla, y romperla convertiría la métrica en una mentira.",
            "",
            "**Conseguir más fotos de las mismas personas no arregla esto.** Lo que "
            "hace falta es material de fotógrafos distintos: otras colecciones, "
            "otros naturalistas, o fotografías propias tomadas por más de una "
            "persona. Tampoco tiene sentido sustituir estas familias por otras: el "
            "material existe, solo está mal distribuido.",
            "",
        ]
        lineas += [_detalle(f) for f in sin_reparto]

    if escasas:
        lineas += [
            "",
            "### Material insuficiente: hacen falta **más imágenes**",
            "",
            "Estas familias no llegan al mínimo ni sumando los tres splits, así que "
            "ninguna forma de repartirlas las salvaría. Para ellas sí aplica el "
            "consejo clásico: o se consiguen más imágenes, o la familia se queda "
            "dentro de `Otros_<Orden>` en esta versión del modelo.",
            "",
        ]
        lineas += [_detalle(f) for f in escasas]

    return lineas


def reporte_markdown(resumen: dict) -> str:
    lineas = [
        "# Reporte de particionado",
        "",
        f"Total de imágenes: **{resumen['total']}**",
        "",
        "| Split | Imágenes |",
        "| --- | ---: |",
    ]
    for split, cantidad in resumen["por_split"].items():
        lineas.append(f"| {split} | {cantidad} |")

    lineas += [
        "",
        "El particionado agrupa por **observador**: ninguna persona aparece en dos "
        "splits. Es la defensa contra la fuga de datos descrita en el diseño (§7). "
        "La asignación se estratifica además por clase, para que los fotógrafos de "
        "una misma familia no caigan todos del mismo lado.",
        "",
    ]
    if "observadores_reusados" in resumen:
        lineas += [
            f"De los observadores de esta corrida, **{resumen['observadores_reusados']}** "
            f"conservan el split que ya tenían y **{resumen['observadores_nuevos']}** se "
            f"repartieron ahora. La asignación vive en `{ARCHIVO_ASIGNACION}`, junto a los "
            "CSV de los splits: es lo que mantiene el conjunto de examen igual entre "
            "corridas. No es un archivo temporal.",
            "",
        ]
    lineas += [
        "## Decisiones de admisión de familias",
        "",
        "| Familia | Decisión |",
        "| --- | --- |",
    ]
    for familia, decision in sorted(resumen["decisiones"].items()):
        lineas.append(f"| {familia} | {decision} |")

    lineas += _bloque_causas(resumen)

    lineas += [
        "",
        "## Distribución por clase",
        "",
        "Cada celda muestra **imágenes / observadores distintos**: si el número de "
        "observadores es bajo —sobre todo en test— el número de imágenes por sí solo "
        "engaña sobre qué tan bien evaluada está esa clase.",
        "",
        "| Clase | train | val | test |",
        "| --- | ---: | ---: | ---: |",
    ]
    por_clase = resumen.get("por_clase", {})
    for clase, conteo in sorted(por_clase.items()):
        celdas = " | ".join(
            f"{conteo[split]['imagenes']} img / {conteo[split]['observadores']} obs"
            for split in ("train", "val", "test")
        )
        lineas.append(f"| {clase} | {celdas} |")

    clases_riesgo = sorted(
        clase for clase, conteo in por_clase.items() if conteo["test"]["observadores"] == 1
    )
    lineas += [
        "",
        "## Alerta: clases cuyo test depende de un solo fotógrafo",
        "",
    ]
    if clases_riesgo:
        lineas.append(
            "Estas clases superan el número mínimo de imágenes de prueba exigido, pero "
            "**todas esas imágenes de test vienen de una sola persona**. Eso significa que "
            "el resultado que el reporte de evaluación muestre para esa clase no mide qué "
            "tan bien el modelo reconoce la familia en el campo: mide qué tan bien memorizó "
            "la cámara, el encuadre, la iluminación o el fondo de esa única persona. Conviene "
            "tratar estos resultados con cautela en la reunión de decisión, hasta conseguir "
            "fotos de test de más observadores:"
        )
        lineas.append("")
        for clase in clases_riesgo:
            n_img = por_clase[clase]["test"]["imagenes"]
            lineas.append(f"- `{clase}`: {n_img} imágenes de test, todas del mismo observador.")
    else:
        lineas.append("Ninguna clase depende de un único fotógrafo en su conjunto de test.")

    anonimos = resumen.get("anonimos_por_split") or {"train": 0, "val": 0, "test": 0}
    total_anonimos = sum(anonimos.values())
    lineas += [
        "",
        "## Observaciones sin fotógrafo identificado",
        "",
    ]
    if total_anonimos:
        detalle = ", ".join(f"{split}: {cantidad}" for split, cantidad in anonimos.items())
        lineas.append(
            f"**{total_anonimos} imágenes** quedaron agrupadas bajo el identificador "
            f"`{OBSERVADOR_DESCONOCIDO}` porque la observación de iNaturalist no traía "
            "usuario registrado. Ese identificador **no es una sola persona**: es un cajón "
            "donde caen observaciones anónimas de gente distinta, agrupadas juntas a "
            "propósito (separarlas sin saber quién las tomó podría, en realidad, causar la "
            "fuga que este particionado evita, si dos de ellas compartieran fotógrafo). Se "
            f"repartieron así entre los splits: {detalle}. Si la cifra es una porción grande "
            "del total, conviene saberlo antes de confiar en la partición."
        )
    else:
        lineas.append("No hubo observaciones sin fotógrafo identificado.")

    return "\n".join(lineas) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Particionado del dataset curado")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--curado", default="datos/curado")
    parser.add_argument("--destino", default="datos/splits")
    parser.add_argument("--reporte", default="docs/reporte_splits.md")
    parser.add_argument(
        "--regenerar-asignacion",
        action="store_true",
        help=(
            "descarta la asignación observador->split guardada y reparte todo de "
            "cero. Invalida la comparación con cualquier modelo entrenado antes: "
            "fotógrafos que estaban en examen pueden pasar a aprendizaje. Usar solo "
            "a propósito."
        ),
    )
    args = parser.parse_args(argv)

    onto = cargar_ontologia(Path(args.ontologia))
    with (Path(args.curado) / "manifiesto_curado.csv").open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))

    destino = Path(args.destino)
    ruta_asignacion = destino / ARCHIVO_ASIGNACION
    if args.regenerar_asignacion:
        previa: dict[str, str] = {}
        print(
            f"--regenerar-asignacion: se ignora {ruta_asignacion} y se reparte de cero. "
            "Cualquier modelo entrenado con la partición anterior queda invalidado."
        )
    else:
        try:
            previa = leer_asignacion(ruta_asignacion)
        except ErrorAsignacion as error:
            # No se reparte de cero por las bravas: eso movería observadores de
            # examen a aprendizaje sin que nadie lo pidiera. Se para y se
            # explica cuál es la opción explícita.
            print(f"  !! ERROR: {error}")
            print(
                "No se escribió nada. Corregir el archivo a mano, o rehacer el reparto "
                "a propósito con --regenerar-asignacion (invalida cualquier modelo ya "
                "entrenado)."
            )
            return SALIDA_ASIGNACION_INVALIDA

    particiones, resumen = particionar(filas, onto, asignacion_previa=previa)

    # La asignación se persiste ANTES que los CSV: es el artefacto del que
    # todo lo demás se deriva. Si la corrida muere entre las dos escrituras,
    # la siguiente reproduce exactamente la misma partición; al revés, se
    # quedarían unos splits en disco que la siguiente corrida ya no sabría
    # reproducir. Se guarda la unión con lo previo para no olvidar a los
    # observadores que no aparecen en esta corrida pero podrían volver.
    escribir_asignacion(previa | resumen["asignacion"], ruta_asignacion)
    escribir_particiones(particiones, destino)

    ruta_reporte = Path(args.reporte)
    ruta_reporte.parent.mkdir(parents=True, exist_ok=True)
    ruta_reporte.write_text(reporte_markdown(resumen), encoding="utf-8")

    print({k: len(v) for k, v in particiones.items()})
    print(
        f"asignación en {ruta_asignacion}: "
        f"{resumen['observadores_reusados']} observadores heredados, "
        f"{resumen['observadores_nuevos']} nuevos"
    )
    return SALIDA_OK


if __name__ == "__main__":
    sys.exit(main())
