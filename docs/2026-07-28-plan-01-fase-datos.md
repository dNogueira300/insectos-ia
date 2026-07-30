# Plan 01 — Fase de datos (Semanas 1–7)

> **Para trabajadores agénticos:** SUB-SKILL REQUERIDA: usar `superpowers:subagent-driven-development` (recomendado) o `superpowers:executing-plans` para implementar este plan tarea por tarea. Los pasos usan sintaxis de casilla (`- [ ]`) para seguimiento.

**Goal:** Construir el pipeline reproducible que convierte la ontología de clases en un dataset curado, sin fugas y con licencias registradas, listo para entrenar el modelo jerárquico.

**Architecture:** Paquete Python `pipeline/` con módulos de responsabilidad única. Cada módulo expone funciones puras testeables y un `main()` de línea de comandos. El estado vive en archivos dentro de `datos/` (nunca versionados) y en manifiestos CSV que arrastran la trazabilidad — observación, observador, licencia — desde la descarga hasta los splits. `ontologia/clases.yaml` es la única fuente de nombres de clase; ningún módulo escribe un nombre de orden o familia literal.

**Tech Stack:** Python 3.12, requests, Pillow, numpy, PyYAML, imagehash, pandas, openpyxl, pytest. SQLite para la base de datos biológica.

**Documento de diseño:** `docs/2026-07-28-sistema-insectos-diseno.md`

## Descomposición en planes

Este es el primero de tres planes. Cada uno produce software funcional y testeable por sí mismo:

| Plan                   | Semanas | Alcance                                            | Estado             |
| ---------------------- | ------- | -------------------------------------------------- | ------------------ |
| **01 — Fase de datos** | 1–7     | Ontología, censo, descarga, curación, splits, BD   | **este documento** |
| 02 — Modelo            | 8–11    | Entrenamiento multi-tarea, evaluación, export ONNX | por escribir       |
| 03 — Prototipo         | 12–14   | Backend FastAPI + frontend React                   | por escribir       |

## Global Constraints

- **Python 3.12**, no 3.14: `py -3.12 -m venv .venv`. La 3.14 aún no tiene ruedas estables de torch/onnxruntime, que hacen falta en el Plan 02. El entorno se crea una vez en la Tarea 1.
- **Todo el código, comentarios, docstrings y mensajes de commit en español**, como el resto del proyecto.
- **Ningún nombre de orden o familia escrito literal en el código.** Todo sale de `ontologia/clases.yaml`. Un test lo verifica en la Tarea 1.
- **`datos/` nunca se versiona.** Solo manifiestos y reportes entran a git.
- **Ninguna prueba hace llamadas de red.** Las APIs se simulan con objetos de sesión falsos.
- **Toda llamada a API lleva `User-Agent`** identificando el proyecto y un correo de contacto, y respeta una pausa de 1 segundo entre páginas. Es requisito de uso de iNaturalist.
- **Solo se aceptan imágenes con licencia Creative Commons declarada.** Las de "todos los derechos reservados" (`license_code` nulo) se descartan en la descarga.
- **Comandos en PowerShell** (Windows 11). Rutas con `\`.
- Si un agente hace el commit, el mensaje termina con `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## Estructura de archivos

```
insectos-ia/
├─ .gitignore                    T1  qué queda fuera de git
├─ pyproject.toml                T1  dependencias y configuración de pytest
├─ README.md                     T1  cómo levantar el entorno y correr el pipeline
├─ ontologia/
│   clases.yaml                  T1  clases confirmadas (v1 se congela en Semana 3)
│   candidatas.yaml              T3  clases a censar antes de decidir
├─ pipeline/
│   __init__.py                  T1
│   ontologia.py                 T1  carga y valida clases.yaml
│   inat.py                      T2  cliente de la API de iNaturalist
│   gbif.py                      T3  conteo de ocurrencias en GBIF
│   censo.py                     T3  tabla de disponibilidad por clase
│   imagenes.py                  T4  descarga, normalización y hash perceptual
│   descarga.py                  T5  descarga masiva + manifiesto
│   curacion.py                  T6  deduplicado y filtros de calidad
│   splits.py                    T7  particionado agrupado + regla de admisión
│   bd.py                        T8  Excel → SQLite con validación
│   campo.py                     T9  ingesta del conjunto de prueba de campo
├─ bd/
│   esquema.sql                  T8  esquema SQLite de la base biológica
├─ tests/
│   conftest.py                  T1  fixtures compartidas
│   test_ontologia.py            T1
│   test_inat.py                 T2
│   test_censo.py                T3
│   test_imagenes.py             T4
│   test_descarga.py             T5
│   test_curacion.py             T6
│   test_splits.py               T7
│   test_bd.py                   T8
│   test_campo.py                T9
├─ datos/                        (gitignored)
│   crudo/  curado/  splits/  campo_crudo/
└─ docs/                         reportes generados por el pipeline
```

**Refinamiento respecto al spec:** el spec listaba `pipeline/censo.py`, `descarga.py`, `curacion.py`, `splits.py`. Se añaden `ontologia.py`, `inat.py`, `gbif.py`, `imagenes.py`, `bd.py` y `campo.py` para que cada archivo tenga una sola responsabilidad y sea testeable sin red. La estructura de carpetas y el contrato de `clases.yaml` no cambian.

**Decisión YAGNI:** GBIF se usa en el censo (conteo de disponibilidad, endpoint trivial) pero **no** para descargar imágenes en esta fase. iNaturalist ya entrega imágenes con etiqueta validada por la comunidad y metadatos de licencia limpios. Si el censo muestra que alguna clase no llega al umbral solo con iNaturalist, la descarga desde GBIF se agrega entonces, con el dato en la mano.

---

## Task 1: Andamiaje del repositorio y ontología

**Files:**

- Create: `.gitignore`, `pyproject.toml`, `README.md`
- Create: `pipeline/__init__.py`, `pipeline/ontologia.py`
- Create: `ontologia/clases.yaml`
- Test: `tests/conftest.py`, `tests/test_ontologia.py`

**Interfaces:**

- Consumes: nada (primera tarea)

- Produces:
  
  - `class ErrorOntologia(Exception)`
  - `@dataclass(frozen=True) Familia(nombre: str, inat_taxon_id: int, nombre_comun: str = "", importancia: str = "")`
  - `@dataclass(frozen=True) Orden(nombre: str, inat_taxon_id: int, nombre_comun: str = "", gbif_key: int | None = None, familias: tuple[Familia, ...] = ())`
  - `@dataclass(frozen=True) Ontologia(version: int, minimo_familia_train: int, minimo_familia_test: int, ordenes: tuple[Orden, ...])` con métodos `nombres_ordenes() -> list[str]`, `nombres_familias() -> list[str]`, `orden_de_familia(familia: str) -> str`, `matriz_pertenencia() -> list[list[bool]]`
  - `cargar_ontologia(ruta: Path) -> Ontologia`
  - `PREFIJO_OTROS: str = "Otros_"`

- [ ] **Step 1: Crear el entorno virtual e instalar dependencias**

```powershell
cd D:\300\OTROS\XXX\DAN\IA\agro\insectos-ia
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
```

- [ ] **Step 2: Crear `.gitignore`**

```gitignore
# entorno
.venv/
__pycache__/
*.pyc

# metadata de build generada por "pip install -e" (nombre de paquete variable)
*.egg-info/

# datos: nunca se versionan (pesan GB y las licencias son por imagen)
datos/

# artefactos de modelo
modelo/*.onnx
modelo/*.pth

# sistema
.DS_Store
Thumbs.db
```

- [ ] **Step 3: Crear `pyproject.toml`**

```toml
[project]
name = "insectos-ia"
version = "0.1.0"
description = "Identificación jerárquica de órdenes y familias de insectos amazónicos"
requires-python = ">=3.12,<3.13"
dependencies = [
    "requests>=2.32",
    "pillow>=11.0",
    "numpy>=2.1",
    "pyyaml>=6.0",
    "imagehash>=4.3",
    "pandas>=2.2",
    "openpyxl>=3.1",
]

[project.optional-dependencies]
dev = ["pytest>=8.3"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
# Explícito a propósito: la raíz tiene varios directorios (ontologia, bd,
# tests, docs) y la detección automática de setuptools falla con
# "Multiple top-level packages discovered in a flat-layout".
packages = ["pipeline"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

Instalar:

```powershell
.venv\Scripts\python -m pip install -e ".[dev]"
```

- [ ] **Step 4: Crear `ontologia/clases.yaml` semilla**

Solo cuatro órdenes con una familia cada uno, para arrancar. La lista real se congela en la Semana 3 con el censo (Tarea 3). Los `inat_taxon_id` de los órdenes están verificados en la demo; los de familia se completan en la Tarea 3.

```yaml
version: 1
minimos:
  familia_train: 150
  familia_test: 30
ordenes:
  - nombre: Coleoptera
    inat_taxon_id: 47208
    gbif_key: 1470
    nombre_comun: escarabajos
    familias:
      - nombre: Curculionidae
        inat_taxon_id: 62956
        nombre_comun: gorgojos
        importancia: plaga
  - nombre: Lepidoptera
    inat_taxon_id: 47157
    gbif_key: 797
    nombre_comun: mariposas y polillas
    familias:
      - nombre: Noctuidae
        inat_taxon_id: 49556
        nombre_comun: nóctuidos
        importancia: plaga
  - nombre: Hymenoptera
    inat_taxon_id: 47201
    gbif_key: 1457
    nombre_comun: abejas, avispas y hormigas
    familias:
      - nombre: Formicidae
        inat_taxon_id: 47336
        nombre_comun: hormigas
        importancia: mixta
  - nombre: Odonata
    inat_taxon_id: 47792
    gbif_key: 789
    nombre_comun: libélulas
    familias: []
```

- [ ] **Step 5: Crear `pipeline/__init__.py` vacío y `tests/conftest.py`**

`pipeline/__init__.py`: archivo vacío.

`tests/conftest.py`:

```python
"""Fixtures compartidas por todas las pruebas."""
from pathlib import Path

import pytest

YAML_MINIMO = """
version: 1
minimos:
  familia_train: 150
  familia_test: 30
ordenes:
  - nombre: Coleoptera
    inat_taxon_id: 47208
    nombre_comun: escarabajos
    familias:
      - nombre: Curculionidae
        inat_taxon_id: 62956
      - nombre: Chrysomelidae
        inat_taxon_id: 50340
  - nombre: Odonata
    inat_taxon_id: 47792
    nombre_comun: libelulas
    familias:
      - nombre: Libellulidae
        inat_taxon_id: 49279
"""


@pytest.fixture
def ruta_ontologia(tmp_path: Path) -> Path:
    """Escribe una ontología válida mínima y devuelve su ruta."""
    ruta = tmp_path / "clases.yaml"
    ruta.write_text(YAML_MINIMO, encoding="utf-8")
    return ruta
```

- [ ] **Step 6: Escribir las pruebas que fallan**

`tests/test_ontologia.py`:

```python
from pathlib import Path

import pytest

from pipeline.ontologia import ErrorOntologia, cargar_ontologia


def test_carga_ontologia_valida(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    assert onto.version == 1
    assert onto.minimo_familia_train == 150
    assert onto.minimo_familia_test == 30
    assert len(onto.ordenes) == 2


def test_nombres_en_orden_alfabetico_estable(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    assert onto.nombres_ordenes() == ["Coleoptera", "Odonata"]
    assert onto.nombres_familias() == [
        "Chrysomelidae",
        "Curculionidae",
        "Libellulidae",
    ]


def test_orden_de_familia(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    assert onto.orden_de_familia("Libellulidae") == "Odonata"


def test_orden_de_familia_desconocida_falla(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    with pytest.raises(ErrorOntologia):
        onto.orden_de_familia("Inexistente")


def test_matriz_pertenencia_una_sola_verdad_por_fila(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    matriz = onto.matriz_pertenencia()
    assert len(matriz) == 3          # tres familias
    assert len(matriz[0]) == 2       # dos ordenes
    for fila in matriz:
        assert sum(fila) == 1        # cada familia pertenece a exactamente un orden


def test_familia_repetida_en_dos_ordenes_falla(tmp_path: Path):
    (tmp_path / "c.yaml").write_text(
        """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: A
    inat_taxon_id: 1
    familias: [{nombre: X, inat_taxon_id: 10}]
  - nombre: B
    inat_taxon_id: 2
    familias: [{nombre: X, inat_taxon_id: 11}]
""",
        encoding="utf-8",
    )
    with pytest.raises(ErrorOntologia, match="X"):
        cargar_ontologia(tmp_path / "c.yaml")


def test_orden_sin_taxon_id_falla(tmp_path: Path):
    (tmp_path / "c.yaml").write_text(
        """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: A
    familias: []
""",
        encoding="utf-8",
    )
    with pytest.raises(ErrorOntologia, match="inat_taxon_id"):
        cargar_ontologia(tmp_path / "c.yaml")


def test_archivo_del_proyecto_es_valido():
    """La ontología real del repositorio debe cargar sin errores."""
    onto = cargar_ontologia(Path("ontologia/clases.yaml"))
    assert len(onto.ordenes) >= 1


def test_ningun_modulo_escribe_nombres_de_clase_literales():
    """Los nombres taxonómicos solo pueden vivir en la ontología, no en el código."""
    prohibidos = ("Coleoptera", "Lepidoptera", "Hymenoptera", "Odonata")
    for archivo in Path("pipeline").glob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        for palabra in prohibidos:
            assert palabra not in texto, f"{archivo} contiene el literal {palabra}"
```

- [ ] **Step 7: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_ontologia.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'pipeline.ontologia'`.

- [ ] **Step 8: Implementar `pipeline/ontologia.py`**

```python
"""Carga y validación de la ontología de clases.

Es la única fuente de verdad sobre qué órdenes y familias existen en el
sistema. Ningún otro módulo debe escribir un nombre taxonómico literal.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class ErrorOntologia(Exception):
    """La ontología es inválida, está incompleta o es inconsistente."""


# Prefijo de las clases que agrupan familias por debajo del umbral de admisión.
# Vive aquí, y no en splits.py, porque es una convención de nombres de clase:
# el backend necesita interpretarla sin importar el pipeline de datos.
PREFIJO_OTROS = "Otros_"


@dataclass(frozen=True)
class Familia:
    nombre: str
    inat_taxon_id: int
    nombre_comun: str = ""
    importancia: str = ""


@dataclass(frozen=True)
class Orden:
    nombre: str
    inat_taxon_id: int
    nombre_comun: str = ""
    gbif_key: int | None = None
    familias: tuple[Familia, ...] = ()


@dataclass(frozen=True)
class Ontologia:
    version: int
    minimo_familia_train: int
    minimo_familia_test: int
    ordenes: tuple[Orden, ...]

    def nombres_ordenes(self) -> list[str]:
        """Nombres de orden en alfabético: fija los índices del modelo."""
        return sorted(o.nombre for o in self.ordenes)

    def nombres_familias(self) -> list[str]:
        """Nombres de familia en alfabético: fija los índices del modelo."""
        return sorted(f.nombre for o in self.ordenes for f in o.familias)

    def orden_de_familia(self, familia: str) -> str:
        for orden in self.ordenes:
            for fam in orden.familias:
                if fam.nombre == familia:
                    return orden.nombre
        raise ErrorOntologia(f"familia desconocida: {familia}")

    def matriz_pertenencia(self) -> list[list[bool]]:
        """Matriz [familia][orden] usada para enmascarar en inferencia."""
        ordenes = self.nombres_ordenes()
        return [
            [self.orden_de_familia(fam) == orden for orden in ordenes]
            for fam in self.nombres_familias()
        ]


def _entero_obligatorio(dic: dict, clave: str, contexto: str) -> int:
    valor = dic.get(clave)
    if not isinstance(valor, int):
        raise ErrorOntologia(f"{contexto}: falta '{clave}' entero")
    return valor


def cargar_ontologia(ruta: Path) -> Ontologia:
    """Lee el YAML de clases y devuelve una Ontologia validada."""
    datos = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ErrorOntologia("el archivo no contiene un mapa YAML")

    minimos = datos.get("minimos") or {}
    ordenes: list[Orden] = []
    vistos_orden: set[str] = set()
    vistas_familia: dict[str, str] = {}

    for bruto in datos.get("ordenes") or []:
        nombre = bruto.get("nombre")
        if not nombre:
            raise ErrorOntologia("hay un orden sin 'nombre'")
        if nombre in vistos_orden:
            raise ErrorOntologia(f"orden repetido: {nombre}")
        vistos_orden.add(nombre)

        familias: list[Familia] = []
        for fam in bruto.get("familias") or []:
            fnombre = fam.get("nombre")
            if not fnombre:
                raise ErrorOntologia(f"orden {nombre}: hay una familia sin 'nombre'")
            if fnombre in vistas_familia:
                raise ErrorOntologia(
                    f"familia {fnombre} declarada en {vistas_familia[fnombre]} y en {nombre}"
                )
            vistas_familia[fnombre] = nombre
            familias.append(
                Familia(
                    nombre=fnombre,
                    inat_taxon_id=_entero_obligatorio(fam, "inat_taxon_id", f"familia {fnombre}"),
                    nombre_comun=fam.get("nombre_comun", ""),
                    importancia=fam.get("importancia", ""),
                )
            )

        ordenes.append(
            Orden(
                nombre=nombre,
                inat_taxon_id=_entero_obligatorio(bruto, "inat_taxon_id", f"orden {nombre}"),
                nombre_comun=bruto.get("nombre_comun", ""),
                gbif_key=bruto.get("gbif_key"),
                familias=tuple(familias),
            )
        )

    if not ordenes:
        raise ErrorOntologia("la ontología no declara ningún orden")

    return Ontologia(
        version=_entero_obligatorio(datos, "version", "raíz"),
        minimo_familia_train=_entero_obligatorio(minimos, "familia_train", "minimos"),
        minimo_familia_test=_entero_obligatorio(minimos, "familia_test", "minimos"),
        ordenes=tuple(ordenes),
    )
```

- [ ] **Step 9: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_ontologia.py -v
```

Esperado: PASS, 9 pruebas.

- [ ] **Step 10: Escribir `README.md`**

````markdown
# insectos-ia

Sistema de IA para la identificación jerárquica (orden → familia) de insectos
amazónicos de importancia económica.
Proyecto Formativo INAAM–FISI + Responsabilidad Social, UNAP.

Diseño: `docs/2026-07-28-sistema-insectos-diseno.md`
Plan de la fase de datos: `docs/2026-07-28-plan-01-fase-datos.md`

## Entorno

Requiere **Python 3.12** (no 3.14: falta soporte estable de torch/onnxruntime).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```

## Estructura

- `ontologia/clases.yaml` — única fuente de verdad de las clases del sistema.

- `pipeline/` — censo, descarga, curación y particionado de datos.

- `bd/` — base de datos biológica (Excel → SQLite).

- `datos/` — imágenes y manifiestos. **No se versiona.**

- `docs/` — diseño, planes y reportes generados.
````

- [ ] **Step 11: Commit**

```powershell
git add .gitignore pyproject.toml README.md ontologia pipeline tests
git commit -m "feat: andamiaje del repositorio y carga validada de la ontologia"
```

---

## Task 2: Cliente de la API de iNaturalist

**Files:**

- Create: `pipeline/inat.py`
- Test: `tests/test_inat.py`

**Interfaces:**

- Consumes: nada de tareas anteriores
- Produces:
  - `@dataclass(frozen=True) Observacion(id: int, taxon_id: int, taxon_nombre: str, rango: str, observador: str, foto_url: str, licencia: str, atribucion: str, latitud: float | None, longitud: float | None, fecha: str)`
  - `nueva_sesion() -> requests.Session`
  - `contar_observaciones(taxon_id: int, *, solo_adultos: bool = True, lugar_id: int | None = None, sesion=None) -> int`
  - `iterar_observaciones(taxon_id: int, *, limite: int, solo_adultos: bool = True, lugar_id: int | None = None, sesion=None, pausa: float = 1.0) -> Iterator[Observacion]`
  - `buscar_lugar(nombre: str, sesion=None) -> int | None`

**Contexto que el implementador necesita:** la API de iNaturalist limita la paginación clásica a 10 000 resultados (`page × per_page`). Para bajar decenas de miles de observaciones hay que paginar con cursor: `order_by=id&order=asc&id_above=<último id visto>`. La demo (`agro/insectos-demo/descargar_datos.py`) usa `page`, y por eso se topaba a las 10 000. Este cliente usa cursor desde el principio.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_inat.py`:

```python
import pytest

from pipeline.inat import (
    Observacion,
    buscar_lugar,
    contar_observaciones,
    iterar_observaciones,
)


class RespuestaFalsa:
    def __init__(self, cuerpo):
        self._cuerpo = cuerpo

    def raise_for_status(self):
        return None

    def json(self):
        return self._cuerpo


class SesionFalsa:
    """Devuelve páginas predefinidas y registra los parámetros recibidos."""

    def __init__(self, paginas):
        self.paginas = list(paginas)
        self.llamadas = []

    def get(self, url, params=None, timeout=None):
        self.llamadas.append(params)
        cuerpo = self.paginas.pop(0) if self.paginas else {"results": []}
        return RespuestaFalsa(cuerpo)


def obs_cruda(oid, con_foto=True, licencia="cc-by"):
    return {
        "id": oid,
        "taxon": {"id": 999, "name": "Especie ejemplo", "rank": "species"},
        "user": {"login": f"usuario{oid % 3}"},
        "location": "-3.75,-73.25",
        "observed_on": "2026-01-15",
        "photos": (
            [
                {
                    "url": "https://inaturalist-open-data.s3.amazonaws.com/photos/1/square.jpg",
                    "license_code": licencia,
                    "attribution": "(c) alguien, algunos derechos reservados",
                }
            ]
            if con_foto
            else []
        ),
    }


def test_contar_pide_per_page_cero():
    sesion = SesionFalsa([{"total_results": 4321, "results": []}])
    total = contar_observaciones(47208, sesion=sesion)
    assert total == 4321
    assert sesion.llamadas[0]["per_page"] == 0
    assert sesion.llamadas[0]["quality_grade"] == "research"


def test_contar_incluye_filtro_de_adultos_por_defecto():
    sesion = SesionFalsa([{"total_results": 10, "results": []}])
    contar_observaciones(47208, sesion=sesion)
    assert sesion.llamadas[0]["term_id"] == 1
    assert sesion.llamadas[0]["term_value_id"] == 2


def test_contar_sin_filtro_de_adultos_omite_los_terminos():
    sesion = SesionFalsa([{"total_results": 10, "results": []}])
    contar_observaciones(47208, solo_adultos=False, sesion=sesion)
    assert "term_id" not in sesion.llamadas[0]


def test_contar_con_lugar_agrega_place_id():
    sesion = SesionFalsa([{"total_results": 10, "results": []}])
    contar_observaciones(47208, lugar_id=7041, sesion=sesion)
    assert sesion.llamadas[0]["place_id"] == 7041


def test_iterar_convierte_la_observacion():
    sesion = SesionFalsa([{"results": [obs_cruda(100)]}])
    obs = list(iterar_observaciones(47208, limite=1, sesion=sesion, pausa=0))
    assert len(obs) == 1
    o = obs[0]
    assert isinstance(o, Observacion)
    assert o.id == 100
    assert o.observador == "usuario1"
    assert o.latitud == pytest.approx(-3.75)
    assert o.longitud == pytest.approx(-73.25)
    assert o.fecha == "2026-01-15"
    assert o.licencia == "cc-by"


def test_iterar_pide_la_foto_en_tamano_medium():
    sesion = SesionFalsa([{"results": [obs_cruda(100)]}])
    o = next(iter(iterar_observaciones(47208, limite=1, sesion=sesion, pausa=0)))
    assert o.foto_url.endswith("medium.jpg")


def test_iterar_respeta_el_limite():
    pagina = {"results": [obs_cruda(i) for i in range(1, 51)]}
    sesion = SesionFalsa([pagina, pagina])
    obs = list(iterar_observaciones(47208, limite=10, sesion=sesion, pausa=0))
    assert len(obs) == 10


def test_iterar_avanza_el_cursor_id_above():
    p1 = {"results": [obs_cruda(i) for i in range(1, 6)]}
    p2 = {"results": [obs_cruda(i) for i in range(6, 11)]}
    sesion = SesionFalsa([p1, p2, {"results": []}])
    list(iterar_observaciones(47208, limite=100, sesion=sesion, pausa=0))
    assert sesion.llamadas[0]["id_above"] == 0
    assert sesion.llamadas[1]["id_above"] == 5
    assert sesion.llamadas[2]["id_above"] == 10


def test_iterar_descarta_observaciones_sin_foto():
    sesion = SesionFalsa(
        [{"results": [obs_cruda(1, con_foto=False), obs_cruda(2)]}, {"results": []}]
    )
    obs = list(iterar_observaciones(47208, limite=100, sesion=sesion, pausa=0))
    assert [o.id for o in obs] == [2]


def test_iterar_termina_con_pagina_vacia():
    sesion = SesionFalsa([{"results": []}])
    assert list(iterar_observaciones(47208, limite=100, sesion=sesion, pausa=0)) == []


def test_iterar_tolera_ubicacion_ausente():
    cruda = obs_cruda(1)
    del cruda["location"]
    sesion = SesionFalsa([{"results": [cruda]}, {"results": []}])
    o = next(iter(iterar_observaciones(47208, limite=1, sesion=sesion, pausa=0)))
    assert o.latitud is None and o.longitud is None


def test_iterar_descarta_observacion_sin_id():
    sin_id = obs_cruda(1)
    del sin_id["id"]
    sesion = SesionFalsa([{"results": [sin_id, obs_cruda(2)]}, {"results": []}])
    obs = list(iterar_observaciones(47208, limite=100, sesion=sesion, pausa=0))
    assert [o.id for o in obs] == [2]


def test_iterar_avanza_cursor_pese_a_observacion_sin_id():
    sin_id = obs_cruda(3)
    del sin_id["id"]
    p1 = {"results": [obs_cruda(1), sin_id, obs_cruda(5)]}
    sesion = SesionFalsa([p1, {"results": []}])
    list(iterar_observaciones(47208, limite=100, sesion=sesion, pausa=0))
    assert sesion.llamadas[0]["id_above"] == 0
    assert sesion.llamadas[1]["id_above"] == 5


def test_iterar_conserva_url_sin_square_tal_cual():
    cruda = obs_cruda(1)
    cruda["photos"][0]["url"] = (
        "https://inaturalist-open-data.s3.amazonaws.com/photos/1/original.jpg"
    )
    sesion = SesionFalsa([{"results": [cruda]}, {"results": []}])
    o = next(iter(iterar_observaciones(47208, limite=1, sesion=sesion, pausa=0)))
    assert o.foto_url == (
        "https://inaturalist-open-data.s3.amazonaws.com/photos/1/original.jpg"
    )


def test_iterar_reemplaza_solo_la_ultima_aparicion_de_square():
    cruda = obs_cruda(1)
    cruda["photos"][0]["url"] = "https://squarehost.example.com/photos/1/square.jpg"
    sesion = SesionFalsa([{"results": [cruda]}, {"results": []}])
    o = next(iter(iterar_observaciones(47208, limite=1, sesion=sesion, pausa=0)))
    assert o.foto_url == "https://squarehost.example.com/photos/1/medium.jpg"


def test_buscar_lugar_sin_id_en_el_resultado_devuelve_none():
    sesion = SesionFalsa([{"results": [{"name": "Iquitos"}]}])
    assert buscar_lugar("Iquitos", sesion=sesion) is None
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_inat.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'pipeline.inat'`.

- [ ] **Step 3: Implementar `pipeline/inat.py`**

```python
"""Cliente de la API pública de iNaturalist.

Paginación por cursor (`id_above`), no por número de página: la API corta la
paginación clásica en 10 000 resultados y el sistema necesita bajar más.
"""
from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass

import requests

API = "https://api.inaturalist.org/v1"
USER_AGENT = "insectos-ia-UNAP/1.0 (proyecto academico; eliasdna0499@gmail.com)"
POR_PAGINA = 200
PAUSA_SEGUNDOS = 1.0


@dataclass(frozen=True)
class Observacion:
    id: int
    taxon_id: int
    taxon_nombre: str
    rango: str
    observador: str
    foto_url: str
    licencia: str
    atribucion: str
    latitud: float | None
    longitud: float | None
    fecha: str


def nueva_sesion() -> requests.Session:
    """Sesión con el User-Agent que exige iNaturalist."""
    sesion = requests.Session()
    sesion.headers.update({"User-Agent": USER_AGENT})
    return sesion


def _parametros(taxon_id: int, solo_adultos: bool, lugar_id: int | None) -> dict:
    params = {
        "taxon_id": taxon_id,
        "quality_grade": "research",
        "photos": "true",
        "locale": "es",
    }
    if solo_adultos:
        # Anotación "Life Stage = Adult": excluye larvas, orugas y ninfas,
        # que ensucian las clases y hunden la precisión.
        params["term_id"] = 1
        params["term_value_id"] = 2
    if lugar_id:
        params["place_id"] = lugar_id
    return params


def contar_observaciones(
    taxon_id: int,
    *,
    solo_adultos: bool = True,
    lugar_id: int | None = None,
    sesion=None,
) -> int:
    """Cuántas observaciones existen, sin descargar ninguna."""
    sesion = sesion or nueva_sesion()
    params = _parametros(taxon_id, solo_adultos, lugar_id) | {"per_page": 0}
    respuesta = sesion.get(f"{API}/observations", params=params, timeout=30)
    respuesta.raise_for_status()
    return int(respuesta.json().get("total_results", 0))


def _a_observacion(cruda: dict) -> Observacion | None:
    oid = cruda.get("id")
    if oid is None:
        return None

    fotos = cruda.get("photos") or []
    if not fotos:
        return None
    url = fotos[0].get("url") or ""
    if not url:
        return None
    prefijo, separador, sufijo = url.rpartition("square")
    if separador:
        # Solo se reemplaza la última aparición de "square" (el nombre de
        # archivo del tamaño de la foto); una aparición previa en la ruta
        # (por ejemplo en el dominio) queda intacta.
        url = f"{prefijo}medium{sufijo}"
    # Si "square" no aparece en la URL, se entrega tal cual: la descarga
    # posterior filtra por tamaño mínimo, así que no hace falta descartarla.

    taxon = cruda.get("taxon") or {}
    latitud = longitud = None
    ubicacion = cruda.get("location")
    if ubicacion and "," in ubicacion:
        try:
            latitud, longitud = (float(v) for v in ubicacion.split(",", 1))
        except ValueError:
            latitud = longitud = None

    return Observacion(
        id=int(oid),
        taxon_id=int(taxon.get("id") or 0),
        taxon_nombre=taxon.get("name") or "",
        rango=taxon.get("rank") or "",
        observador=(cruda.get("user") or {}).get("login") or "desconocido",
        foto_url=url,
        licencia=fotos[0].get("license_code") or "",
        atribucion=fotos[0].get("attribution") or "",
        latitud=latitud,
        longitud=longitud,
        fecha=cruda.get("observed_on") or "",
    )


def iterar_observaciones(
    taxon_id: int,
    *,
    limite: int,
    solo_adultos: bool = True,
    lugar_id: int | None = None,
    sesion=None,
    pausa: float = PAUSA_SEGUNDOS,
) -> Iterator[Observacion]:
    """Entrega hasta `limite` observaciones, una foto por observación."""
    sesion = sesion or nueva_sesion()
    entregadas = 0
    id_above = 0

    while entregadas < limite:
        params = _parametros(taxon_id, solo_adultos, lugar_id) | {
            "per_page": POR_PAGINA,
            "order_by": "id",
            "order": "asc",
            "id_above": id_above,
        }
        respuesta = sesion.get(f"{API}/observations", params=params, timeout=30)
        respuesta.raise_for_status()
        resultados = respuesta.json().get("results", [])
        if not resultados:
            return

        for cruda in resultados:
            oid = cruda.get("id")
            if oid is not None:
                id_above = max(id_above, int(oid))
            observacion = _a_observacion(cruda)
            if observacion is None:
                continue
            yield observacion
            entregadas += 1
            if entregadas >= limite:
                return

        if pausa:
            time.sleep(pausa)


def buscar_lugar(nombre: str, sesion=None) -> int | None:
    """Resuelve el `place_id` de iNaturalist a partir de un nombre.

    Se usa para no escribir identificadores de lugar a mano en la configuración.
    """
    sesion = sesion or nueva_sesion()
    respuesta = sesion.get(
        f"{API}/places/autocomplete", params={"q": nombre, "per_page": 1}, timeout=30
    )
    respuesta.raise_for_status()
    resultados = respuesta.json().get("results", [])
    if not resultados:
        return None
    oid = resultados[0].get("id")
    return int(oid) if oid is not None else None
```

- [ ] **Step 4: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_inat.py -v
```

Esperado: PASS, 16 pruebas.

- [ ] **Step 5: Verificar contra la API real (una sola llamada)**

```powershell
.venv\Scripts\python -c "from pipeline.inat import contar_observaciones; print(contar_observaciones(47208))"
```

Esperado: un entero de seis o siete cifras. Si falla con error de red, revisar el `User-Agent` antes de tocar el código.

- [ ] **Step 6: Commit**

```powershell
git add pipeline/inat.py tests/test_inat.py
git commit -m "feat: cliente de iNaturalist con paginacion por cursor"
```

---

## Task 3: Censo de disponibilidad por clase

**Files:**

- Create: `pipeline/gbif.py`, `pipeline/censo.py`, `ontologia/candidatas.yaml`
- Test: `tests/test_censo.py`

**Interfaces:**

- Consumes: `pipeline.ontologia.cargar_ontologia`, `pipeline.ontologia.Ontologia`, `pipeline.inat.contar_observaciones`, `pipeline.inat.buscar_lugar`, `pipeline.inat.PAUSA_SEGUNDOS`
- Produces:
  - `pipeline.gbif.contar_ocurrencias(taxon_key: int, *, pais: str | None = None, sesion=None) -> int`
  - `SIN_DATO: int = -1` — marca un conteo que no se obtuvo (fallo de red, o fuente que no aplica a esa clase), para no confundirlo con un 0 real.
  - `VEREDICTO_ERROR: str = "error_consulta"` — veredicto de una clase cuya consulta falló; no equivale a "insuficiente".
  - `@dataclass(frozen=True) FilaCenso(nivel: str, orden: str, nombre: str, inat_global: int, inat_lugar: int, gbif_global: int, gbif_pais: int, objetivo: int, veredicto: str)`
  - `pipeline.censo.censar(onto, *, lugar_id: int | None, pais_gbif: str | None, sesion_inat=None, sesion_gbif=None, pausa_segundos: float = inat.PAUSA_SEGUNDOS, al_avanzar: Callable[[list[FilaCenso]], None] | None = None) -> list[FilaCenso]`
  - `pipeline.censo.a_markdown(filas: list[FilaCenso], onto) -> str`

**Por qué existe esta tarea:** es el entregable que permite a la Facultad decidir qué clases entran con datos delante, en lugar de por intuición (§5 del diseño). Su salida, `docs/censo_disponibilidad.md`, es el insumo de la reunión de Semana 3.

**Factor de curación:** el censo cuenta observaciones crudas, pero el umbral de admisión (150 train + 30 test) se aplica sobre imágenes *curadas*. Se asume que sobrevive el 67% (`FACTOR_CURACION = 1.5`), estimado a partir de la demo. Es una estimación declarada, no un dato: se recalibra tras la primera corrida de curación (Tarea 6) y se anota en el reporte.

**Resiliencia del censo (hallazgo de revisión):** censar decenas de clases contra dos APIs externas es justo el tipo de proceso largo que una falla de red a mitad de camino puede arruinar. `censar` captura cualquier excepción por clase individual (no solo `requests.RequestException`, porque un fallo de red real puede aparecer como error de conexión, tiempo de espera, código HTTP o una respuesta sin el campo esperado) y le asigna el veredicto `VEREDICTO_ERROR` en vez de abortar el censo completo — "no se sabe todavía", distinto de "insuficiente" ("se consultó y no alcanza"). Además `censar` acepta un callback `al_avanzar` que `main()` usa para volcar a disco lo censado hasta el momento después de cada clase, y una `pausa_segundos` (reutilizando `pipeline.inat.PAUSA_SEGUNDOS`) entre clases para no saturar la API. El reporte en Markdown declara tres advertencias que antes no existían: qué significa `N/D`, que el veredicto solo pondera *iNat global* (no la columna regional) y qué es `error_consulta`.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_censo.py`:

```python
from pathlib import Path

from pipeline import censo
from pipeline.censo import SIN_DATO, VEREDICTO_ERROR, FilaCenso, a_markdown, censar
from pipeline.ontologia import cargar_ontologia


class SesionContadora:
    """Devuelve un conteo fijo por taxon_id consultado."""

    def __init__(self, conteos, clave="total_results"):
        self.conteos = conteos
        self.clave = clave
        self.llamadas = []

    def get(self, url, params=None, timeout=None):
        self.llamadas.append(params)
        taxon = params.get("taxon_id") or params.get("taxonKey")
        total = self.conteos.get(taxon, 0)
        if params.get("place_id") or params.get("country"):
            total = total // 10
        clave = self.clave
        return type(
            "R", (), {"raise_for_status": lambda s: None, "json": lambda s: {clave: total}}
        )()


class SesionQueFalla:
    """Como SesionContadora, pero un taxon_id concreto revienta la llamada.

    Simula un fallo de red (timeout, 5xx, conexión caída) al consultar una
    sola clase, para probar que el resto del censo sobrevive.
    """

    def __init__(self, conteos, taxon_que_falla, clave="total_results"):
        self.conteos = conteos
        self.taxon_que_falla = taxon_que_falla
        self.clave = clave

    def get(self, url, params=None, timeout=None):
        taxon = params.get("taxon_id") or params.get("taxonKey")
        if taxon == self.taxon_que_falla:
            raise ConnectionError("fallo de red simulado")
        total = self.conteos.get(taxon, 0)
        clave = self.clave
        return type(
            "R", (), {"raise_for_status": lambda s: None, "json": lambda s: {clave: total}}
        )()


def test_censa_ordenes_y_familias(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    inat = SesionContadora({47208: 50000, 47792: 30000, 62956: 900, 50340: 400, 49279: 5000})
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
    niveles = [f.nivel for f in filas]
    assert niveles.count("orden") == 2
    assert niveles.count("familia") == 3


def test_veredicto_suficiente_cuando_supera_el_objetivo(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    # objetivo = (150 + 30) * 1.5 = 270
    inat = SesionContadora({47208: 9999, 47792: 9999, 62956: 900, 50340: 100, 49279: 5000})
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
    por_nombre = {f.nombre: f for f in filas}
    assert por_nombre["Curculionidae"].veredicto == "suficiente"
    assert por_nombre["Chrysomelidae"].veredicto == "insuficiente"


def test_objetivo_se_calcula_desde_los_minimos_de_la_ontologia(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    inat = SesionContadora({})
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
    familia = next(f for f in filas if f.nivel == "familia")
    assert familia.objetivo == 270


def test_censo_con_lugar_consulta_dos_veces_por_taxon(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    inat = SesionContadora({47208: 1000, 47792: 1000, 62956: 1000, 50340: 1000, 49279: 1000})
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=7041, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
    fila = filas[0]
    assert fila.inat_global == 1000
    assert fila.inat_lugar == 100


def test_markdown_incluye_todas_las_filas_y_el_factor(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = [
        FilaCenso("orden", "Coleoptera", "Coleoptera", 5000, 500, 900, 90, 270, "suficiente"),
        FilaCenso("familia", "Coleoptera", "Curculionidae", 100, 10, 20, 2, 270, "insuficiente"),
    ]
    texto = a_markdown(filas, onto)
    assert "Curculionidae" in texto
    assert "insuficiente" in texto
    assert "1.5" in texto  # el factor de curación debe estar declarado


def test_fallo_de_red_en_una_clase_no_aborta_el_censo(ruta_ontologia: Path):
    """Hallazgo 1: una clase que falla no debe tumbar el censo completo."""
    onto = cargar_ontologia(ruta_ontologia)
    # 62956 = Curculionidae: su consulta revienta; las otras cuatro clases
    # (2 órdenes + Chrysomelidae + Libellulidae) deben censarse con normalidad.
    inat = SesionQueFalla(
        {47208: 50000, 47792: 30000, 50340: 400, 49279: 5000}, taxon_que_falla=62956
    )
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
    assert len(filas) == 5  # ninguna clase se pierde por el fallo de una sola

    por_nombre = {f.nombre: f for f in filas}
    fallida = por_nombre["Curculionidae"]
    assert fallida.veredicto == VEREDICTO_ERROR
    assert fallida.veredicto != "insuficiente"  # no confundir "no se sabe" con "no alcanza"
    assert fallida.inat_global == SIN_DATO

    # las demás clases se censaron con normalidad, sin contagiarse del fallo
    assert por_nombre["Chrysomelidae"].veredicto in ("suficiente", "insuficiente")
    assert por_nombre["Chrysomelidae"].inat_global == 400


def test_pausa_es_parametrizable_y_no_duerme_con_cero(ruta_ontologia: Path, monkeypatch):
    """Hallazgo 2: la pausa entre consultas se reutiliza de pipeline.inat y
    puede desactivarse para que las pruebas sean instantáneas."""
    onto = cargar_ontologia(ruta_ontologia)
    inat_ses = SesionContadora({47208: 100, 47792: 100, 62956: 100, 50340: 100, 49279: 100})
    gbif_ses = SesionContadora({}, clave="count")
    pausas: list[float] = []
    monkeypatch.setattr(censo.time, "sleep", lambda segundos: pausas.append(segundos))

    censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat_ses, sesion_gbif=gbif_ses,
        pausa_segundos=0,
    )
    assert pausas == []  # con 0 no debe invocarse time.sleep en absoluto

    censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat_ses, sesion_gbif=gbif_ses,
        pausa_segundos=2,
    )
    assert pausas  # con un valor positivo sí se pausa entre clases
    assert all(p == 2 for p in pausas)


def test_markdown_declara_los_supuestos_de_gbif_veredicto_y_adultos(ruta_ontologia: Path):
    """Hallazgo 3: el reporte debe advertir sobre N/D, el alcance del
    veredicto y el filtro de adultos, para no inducir a error en la reunión
    de decisión con la Facultad."""
    onto = cargar_ontologia(ruta_ontologia)
    filas = [
        FilaCenso("orden", "Coleoptera", "Coleoptera", 5000, 500, 900, 90, 270, "suficiente"),
        FilaCenso(
            "familia", "Coleoptera", "Curculionidae", 100, 10, SIN_DATO, SIN_DATO, 270,
            "insuficiente",
        ),
        FilaCenso(
            "familia", "Odonata", "Libellulidae", SIN_DATO, SIN_DATO, SIN_DATO, SIN_DATO, 270,
            VEREDICTO_ERROR,
        ),
    ]
    texto = a_markdown(filas, onto)

    # N/D en vez de -1 para lo no consultado (GBIF de familia y filas con error)
    assert "N/D" in texto
    assert "-1" not in texto

    # el filtro de adultos queda declarado
    assert "adultos" in texto.lower()

    # el reporte aclara que el veredicto no pondera la columna regional
    assert "iNat global" in texto
    assert "amazónic" in texto.lower() or "regional" in texto.lower()

    # error_consulta queda explicado y no se confunde con insuficiente
    assert VEREDICTO_ERROR in texto
    assert "reintentar" in texto.lower()
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_censo.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'pipeline.censo'`.

- [ ] **Step 3: Implementar `pipeline/gbif.py`**

```python
"""Conteo de ocurrencias con imagen en GBIF.

Solo se usa para el censo de disponibilidad. La descarga de imágenes en esta
fase sale de iNaturalist; GBIF entra como fuente de imágenes solo si el censo
muestra que alguna clase no llega al umbral.
"""
from __future__ import annotations

import requests

API = "https://api.gbif.org/v1/occurrence/search"
USER_AGENT = "insectos-ia-UNAP/1.0 (proyecto academico; eliasdna0499@gmail.com)"


def nueva_sesion() -> requests.Session:
    sesion = requests.Session()
    sesion.headers.update({"User-Agent": USER_AGENT})
    return sesion


def contar_ocurrencias(taxon_key: int, *, pais: str | None = None, sesion=None) -> int:
    """Ocurrencias con foto para un taxón. `pais` es código ISO-2, p. ej. 'PE'."""
    if not taxon_key:
        return 0
    sesion = sesion or nueva_sesion()
    params = {"taxonKey": taxon_key, "mediaType": "StillImage", "limit": 0}
    if pais:
        params["country"] = pais
    respuesta = sesion.get(API, params=params, timeout=30)
    respuesta.raise_for_status()
    return int(respuesta.json().get("count", 0))
```

- [ ] **Step 4: Implementar `pipeline/censo.py`**

```python
"""Censo de disponibilidad de imágenes por clase.

Produce la tabla con la que la Facultad decide qué órdenes y familias entran
al sistema, antes de descargar un solo archivo.
"""
from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from pipeline import gbif, inat
from pipeline.ontologia import Ontologia, cargar_ontologia

# El censo cuenta observaciones crudas; el umbral de admisión se aplica sobre
# imágenes curadas. Se estima que sobrevive ~67% (duplicados, fotos chicas,
# fotos de hábitat). Recalibrar tras la primera corrida de curación.
FACTOR_CURACION = 1.5

# Marca un conteo que no se obtuvo: por un fallo de red al consultarlo, o
# porque la fuente no aplica para esa clase (p. ej. GBIF en una familia, que
# no tiene `gbif_key` propio en la ontología). No debe confundirse con un 0
# real (0 significa "se consultó y no hay registros").
SIN_DATO = -1

# Veredicto de una clase en la que falló la consulta de red (iNaturalist o
# GBIF). No es "insuficiente" -esa palabra implica que sí se consultó y no
# alcanza el objetivo-, sino "no se sabe todavía": hay que reintentarla.
VEREDICTO_ERROR = "error_consulta"


@dataclass(frozen=True)
class FilaCenso:
    nivel: str          # "orden" o "familia"
    orden: str
    nombre: str
    inat_global: int
    inat_lugar: int
    gbif_global: int
    gbif_pais: int
    objetivo: int
    veredicto: str      # "suficiente", "insuficiente" o VEREDICTO_ERROR


def _objetivo(onto: Ontologia) -> int:
    return round((onto.minimo_familia_train + onto.minimo_familia_test) * FACTOR_CURACION)


def censar(
    onto: Ontologia,
    *,
    lugar_id: int | None,
    pais_gbif: str | None,
    sesion_inat=None,
    sesion_gbif=None,
    pausa_segundos: float = inat.PAUSA_SEGUNDOS,
    al_avanzar: Callable[[list[FilaCenso]], None] | None = None,
) -> list[FilaCenso]:
    """Consulta iNaturalist y GBIF para cada clase de la ontología.

    Un fallo de red al consultar una clase no aborta el censo completo: se
    captura, la fila queda con sus conteos en `SIN_DATO` y veredicto
    `VEREDICTO_ERROR`, y el recorrido sigue con la siguiente clase. Distinguir
    ese caso de "insuficiente" importa porque "insuficiente" implica que sí
    se consultó y no alcanza el objetivo; "error_consulta" significa que no
    se sabe todavía y hay que reintentar. Se captura `Exception` en general
    (no solo `requests.RequestException`) porque un fallo de red real puede
    aparecer como error de conexión, tiempo de espera, código HTTP, o incluso
    una respuesta sin el campo JSON esperado -no vale la pena enumerar cada
    subtipo cuando el tratamiento es el mismo: no perder el resto del censo.

    `pausa_segundos` throttlea las llamadas a iNaturalist entre una clase y
    la siguiente, reutilizando por defecto `pipeline.inat.PAUSA_SEGUNDOS` (la
    misma constante que ya usa `iterar_observaciones` entre páginas). Las
    pruebas pasan 0 para no dormir de verdad.

    Si se pasa `al_avanzar`, se invoca con una copia de las filas censadas
    hasta el momento después de cada clase, para que quien llama pueda
    persistir el progreso incrementalmente y no perder el trabajo hecho si
    el proceso se interrumpe a mitad de camino.
    """
    sesion_inat = sesion_inat or inat.nueva_sesion()
    sesion_gbif = sesion_gbif or gbif.nueva_sesion()
    objetivo = _objetivo(onto)
    filas: list[FilaCenso] = []

    for orden in sorted(onto.ordenes, key=lambda o: o.nombre):
        candidatos = [("orden", orden.nombre, orden.inat_taxon_id, orden.gbif_key)]
        candidatos += [
            ("familia", fam.nombre, fam.inat_taxon_id, None)
            for fam in sorted(orden.familias, key=lambda f: f.nombre)
        ]

        for nivel, nombre, taxon_id, gbif_key in candidatos:
            try:
                global_ = inat.contar_observaciones(taxon_id, sesion=sesion_inat)
                en_lugar = (
                    inat.contar_observaciones(taxon_id, lugar_id=lugar_id, sesion=sesion_inat)
                    if lugar_id
                    else 0
                )
                if pausa_segundos:
                    time.sleep(pausa_segundos)
                g_global = (
                    gbif.contar_ocurrencias(gbif_key, sesion=sesion_gbif)
                    if gbif_key
                    else SIN_DATO
                )
                g_pais = (
                    gbif.contar_ocurrencias(gbif_key, pais=pais_gbif, sesion=sesion_gbif)
                    if gbif_key and pais_gbif
                    else SIN_DATO
                )
                veredicto = "suficiente" if global_ >= objetivo else "insuficiente"
            except Exception:
                global_ = en_lugar = g_global = g_pais = SIN_DATO
                veredicto = VEREDICTO_ERROR

            filas.append(
                FilaCenso(
                    nivel=nivel,
                    orden=orden.nombre,
                    nombre=nombre,
                    inat_global=global_,
                    inat_lugar=en_lugar,
                    gbif_global=g_global,
                    gbif_pais=g_pais,
                    objetivo=objetivo,
                    veredicto=veredicto,
                )
            )
            if al_avanzar is not None:
                al_avanzar(list(filas))
    return filas


def _celda(valor: int) -> str:
    """Renderiza un conteo; `SIN_DATO` se ve como `N/D`, nunca como `-1`."""
    return "N/D" if valor == SIN_DATO else str(valor)


def a_markdown(filas: list[FilaCenso], onto: Ontologia) -> str:
    """Reporte legible para llevar a la reunión con la Facultad."""
    objetivo = _objetivo(onto)
    lineas = [
        "# Censo de disponibilidad de imágenes por clase",
        "",
        f"Umbral de admisión de una familia: **{onto.minimo_familia_train} imágenes curadas "
        f"en train y {onto.minimo_familia_test} en test**.",
        "",
        f"Factor de curación estimado: **{FACTOR_CURACION}** (se asume que sobrevive ~"
        f"{round(100 / FACTOR_CURACION)}% de lo descargado tras deduplicar y filtrar). "
        f"Por eso el objetivo de observaciones crudas es **{objetivo}** por familia.",
        "",
        "La columna *en lugar* filtra por la región configurada; sirve para ver cuánto "
        "del material disponible es realmente amazónico.",
        "",
        "**Los conteos incluyen solo ejemplares adultos** (`solo_adultos=True` excluye "
        "larvas, orugas y ninfas por defecto en la consulta a iNaturalist). Quien compare "
        "estas cifras contra la web pública de iNaturalist verá números menores por esa razón; "
        "no es un error del censo.",
        "",
        "**El veredicto se calcula solo con la columna *iNat global* (conteo mundial)**, no "
        "con *iNat en lugar*. Una clase abundante en el mundo pero casi ausente en la región "
        "configurada puede salir marcada como \"suficiente\" igual: no se debe leer "
        "\"suficiente\" como \"suficiente material amazónico\". Si el veredicto debe ponderar "
        "la columna regional es una decisión pendiente, todavía sin tomar.",
        "",
        "**`N/D`** marca una celda que no se consultó, para no confundirla con un 0 real "
        "(0 significa \"se consultó y no hay registros\"). Las columnas GBIF de las familias "
        "siempre muestran `N/D`: la ontología solo asigna `gbif_key` a nivel de orden, así "
        "que GBIF nunca se consulta para una familia por sí sola. También aparece `N/D` en "
        "cualquier columna de una fila con veredicto `error_consulta`.",
        "",
        f"**`{VEREDICTO_ERROR}`** marca una clase en la que la consulta a iNaturalist o a "
        "GBIF falló (red, límite de tasa, etc.). No equivale a \"insuficiente\": significa "
        "que no se sabe todavía y hay que reintentar esa clase.",
        "",
        "| Nivel | Orden | Clase | iNat global | iNat en lugar | GBIF global | GBIF país | Objetivo | Veredicto |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for f in filas:
        lineas.append(
            f"| {f.nivel} | {f.orden} | {f.nombre} | {_celda(f.inat_global)} | "
            f"{_celda(f.inat_lugar)} | {_celda(f.gbif_global)} | {_celda(f.gbif_pais)} | "
            f"{f.objetivo} | {f.veredicto} |"
        )

    insuficientes = [f.nombre for f in filas if f.nivel == "familia" and f.veredicto == "insuficiente"]
    con_error = [f"{f.orden}/{f.nombre}" for f in filas if f.veredicto == VEREDICTO_ERROR]
    lineas += [
        "",
        "## Familias que no alcanzan el umbral",
        "",
        (
            ", ".join(insuficientes)
            if insuficientes
            else "Ninguna: todas las familias censadas alcanzan el objetivo."
        ),
        "",
        "Estas familias no entran como clase propia. Se agrupan en `Otros_<Orden>` "
        "dentro de su orden, o se reemplazan por otras que la Facultad considere "
        "igual de relevantes y con más material disponible.",
    ]
    if con_error:
        lineas += [
            "",
            "## Clases que no se pudieron consultar (reintentar antes de decidir)",
            "",
            ", ".join(con_error),
        ]
    return "\n".join(lineas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Censo de disponibilidad por clase")
    parser.add_argument("--ontologia", default="ontologia/candidatas.yaml")
    parser.add_argument("--lugar", default="Peru", help="nombre del lugar en iNaturalist")
    parser.add_argument("--pais-gbif", default="PE", help="código ISO-2 para GBIF")
    parser.add_argument("--salida", default="docs/censo_disponibilidad.md")
    args = parser.parse_args()

    onto = cargar_ontologia(Path(args.ontologia))
    sesion = inat.nueva_sesion()
    lugar_id = inat.buscar_lugar(args.lugar, sesion=sesion) if args.lugar else None
    print(f"Lugar '{args.lugar}' resuelto a place_id={lugar_id}")

    ruta_salida = Path(args.salida)
    ruta_json = Path("datos/censo.json")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    ruta_json.parent.mkdir(exist_ok=True)

    def _guardar_avance(filas_hasta_ahora: list[FilaCenso]) -> None:
        # Guardado incremental (Hallazgo 1): si el proceso se interrumpe a
        # mitad de camino -límite de tasa, corte de red, cierre manual-, lo
        # censado hasta ese punto ya quedó en disco y no hay que reiniciar
        # el censo completo.
        ruta_json.write_text(
            json.dumps([asdict(f) for f in filas_hasta_ahora], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        ruta_salida.write_text(a_markdown(filas_hasta_ahora, onto), encoding="utf-8")

    filas = censar(
        onto,
        lugar_id=lugar_id,
        pais_gbif=args.pais_gbif,
        sesion_inat=sesion,
        al_avanzar=_guardar_avance,
    )

    _guardar_avance(filas)
    print(f"Censo escrito en {args.salida} ({len(filas)} clases)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_censo.py -v
```

Esperado: PASS, 8 pruebas.

- [ ] **Step 6: Crear `ontologia/candidatas.yaml` con las clases a censar**

Es la lista *amplia* de candidatas — todo lo que valga la pena consultar antes de decidir, sin compromiso. Debe incluir los 15 órdenes de la hoja de alcance y las familias que proponga el entomólogo. Los `inat_taxon_id` se obtienen buscando cada taxón en `https://www.inaturalist.org/taxa` y leyendo el número de la URL, o con:

```powershell
.venv\Scripts\python -c "import requests;print([(r['id'],r['name'],r['rank']) for r in requests.get('https://api.inaturalist.org/v1/taxa',params={'q':'Curculionidae','rank':'family'},headers={'User-Agent':'insectos-ia-UNAP/1.0'}).json()['results'][:3]])"
```

Mismo formato que `clases.yaml`. Empezar copiando `clases.yaml` y ampliando.

- [ ] **Step 7: Correr el censo real**

```powershell
.venv\Scripts\python -m pipeline.censo --ontologia ontologia/candidatas.yaml
```

Esperado: `docs/censo_disponibilidad.md` con una fila por clase candidata. Revisar que los conteos globales sean plausibles (cientos de miles para órdenes grandes) — un cero indica un `inat_taxon_id` equivocado en `candidatas.yaml`.

- [ ] **Step 8: Commit**

```powershell
git add pipeline/gbif.py pipeline/censo.py tests/test_censo.py ontologia/candidatas.yaml docs/censo_disponibilidad.md
git commit -m "feat: censo de disponibilidad de imagenes por clase"
```

> **Hito de Semana 3 (bloqueante para la Tarea 5):** presentar `docs/censo_disponibilidad.md` a la Facultad, acordar la lista definitiva y escribirla en `ontologia/clases.yaml`. Commit aparte: `docs: ontologia v1 congelada con la Facultad`. Las Tareas 4, 6, 7 y 8 no dependen de esta decisión y pueden avanzar en paralelo.

---

## Task 4: Utilidades de imagen y hash perceptual

**Files:**

- Create: `pipeline/imagenes.py`
- Test: `tests/test_imagenes.py`

**Interfaces:**

- Consumes: nada de tareas anteriores
- Produces:
  - `descargar_imagen(url: str, *, sesion, min_lado: int = 224, timeout: int = 30) -> Image.Image | None`
  - `normalizar(img: Image.Image, lado_max: int = 800) -> Image.Image`
  - `guardar_jpeg(img: Image.Image, ruta: Path, calidad: int = 90) -> None`
  - `hash_perceptual(img: Image.Image) -> str` (16 caracteres hexadecimales)
  - `distancia(hash_a: str, hash_b: str) -> int`
  - `bandas(hash_hex: str) -> tuple[str, str, str, str]`

**Sobre `bandas`:** el deduplicado de la Tarea 6 no puede comparar todos los pares (20 000 imágenes son 200 millones de comparaciones). Se parte el hash de 64 bits en 4 bandas de 16 bits: por el principio del palomar, dos hashes que difieren en **3 bits o menos** comparten al menos una banda idéntica. Eso permite indexar por banda y comparar solo dentro de cada cubeta. Por eso el umbral de deduplicado es 3 y no un número mayor.

**Normalización de la huella (hallazgo de revisión):** `distancia` compara el valor entero de la huella, así que un cero a la izquierda perdido al serializar (huella con menos de 16 caracteres) o un cambio de mayúsculas/minúsculas (p. ej. al pasar por un CSV o una hoja de cálculo que capitaliza texto) no le afectan. Pero `bandas` trocea por **posición de carácter**: cualquiera de esos dos accidentes desplaza las bandas y hace que dos huellas idénticas dejen de compartir cubeta, dejando pasar el duplicado en silencio. Por eso `bandas` y `distancia` normalizan la huella (`zfill(16)` + minúsculas) antes de operar sobre ella.

**`descargar_imagen` registra el motivo del fallo con `logging`** (antes lo tragaba en silencio): una descarga masiva de horas no puede morir por una foto rota, pero sin rastro es imposible distinguir después "la URL no respondió" de "el archivo llegó corrupto" o "la imagen era más chica que `min_lado`".

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_imagenes.py`:

```python
import io
import logging
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pipeline.imagenes import (
    bandas,
    descargar_imagen,
    distancia,
    guardar_jpeg,
    hash_perceptual,
    normalizar,
)


def imagen_patron(semilla: int, lado: int = 300) -> Image.Image:
    """Imagen determinista con estructura suficiente para un hash útil."""
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    return Image.fromarray(base).resize((lado, lado), Image.BICUBIC)


def a_bytes(img: Image.Image) -> bytes:
    buffer = io.BytesIO()
    img.save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


class RespuestaFalsa:
    def __init__(self, contenido):
        self.content = contenido

    def raise_for_status(self):
        return None


class SesionImagen:
    def __init__(self, contenido):
        self.contenido = contenido

    def get(self, url, timeout=None):
        return RespuestaFalsa(self.contenido)


def test_hash_tiene_16_caracteres_hex():
    h = hash_perceptual(imagen_patron(1))
    assert len(h) == 16
    int(h, 16)  # no debe lanzar


def test_distancia_cero_para_la_misma_imagen():
    img = imagen_patron(2)
    assert distancia(hash_perceptual(img), hash_perceptual(img)) == 0


def test_distancia_pequena_tras_recomprimir_y_redimensionar():
    img = imagen_patron(3)
    variante = Image.open(io.BytesIO(a_bytes(img.resize((220, 220))))).convert("RGB")
    assert distancia(hash_perceptual(img), hash_perceptual(variante)) <= 3


def test_distancia_grande_entre_imagenes_distintas():
    a = hash_perceptual(imagen_patron(10))
    b = hash_perceptual(imagen_patron(99))
    assert distancia(a, b) > 3


def test_bandas_son_cuatro_de_cuatro_hex():
    partes = bandas("0123456789abcdef")
    assert partes == ("0123", "4567", "89ab", "cdef")


def con_bits_volteados(hash_hex: str, posiciones: tuple[int, ...]) -> str:
    """Devuelve la huella con los bits indicados invertidos.

    Permite construir huellas a una distancia de Hamming exacta, sin depender
    de que una transformación de imagen produzca esa distancia por azar.
    """
    valor = int(hash_hex, 16)
    for posicion in posiciones:
        valor ^= 1 << posicion
    return f"{valor:016x}"


BASE = "3f2a9c07b15e6d84"


@pytest.mark.parametrize(
    "posiciones",
    [(0,), (17,), (0, 40), (5, 33, 61), (2, 3, 4)],
    ids=["1 bit", "1 bit lejano", "2 bits", "3 bits dispersos", "3 bits juntos"],
)
def test_hashes_a_distancia_maxima_tres_comparten_una_banda(posiciones):
    """Garantía del principio del palomar en la que se apoya el deduplicado.

    Con 4 bandas disjuntas de 16 bits, tres diferencias no pueden repartirse
    entre las cuatro: al menos una banda queda intacta.
    """
    otra = con_bits_volteados(BASE, posiciones)
    assert distancia(BASE, otra) == len(posiciones)
    assert set(bandas(BASE)) & set(bandas(otra))


def test_cuatro_bits_repartidos_pueden_no_compartir_banda():
    """Control: el palomar solo garantiza hasta 3. Con 4 la garantía cesa."""
    otra = con_bits_volteados(BASE, (0, 16, 32, 48))  # uno en cada banda
    assert distancia(BASE, otra) == 4
    assert not set(bandas(BASE)) & set(bandas(otra))


def test_la_misma_huella_sin_cero_a_la_izquierda_da_las_mismas_bandas():
    """Un cero perdido al serializar no debe desalinear el troceado."""
    completa = "0abc123456789abc"
    sin_cero = completa.lstrip("0")
    assert distancia(completa, sin_cero) == 0
    assert bandas(completa) == bandas(sin_cero)


def test_la_misma_huella_en_mayusculas_da_las_mismas_bandas_y_distancia_cero():
    """Un cambio de mayúsculas (p. ej. al viajar por un CSV) no debe desalinear
    el troceado ni hacer parecer distintas dos huellas idénticas."""
    minusculas = "abcdefabcdefabcd"
    mayusculas = minusculas.upper()
    assert distancia(minusculas, mayusculas) == 0
    assert bandas(minusculas) == bandas(mayusculas)


def test_imagen_recomprimida_conserva_banda_comun():
    """La variante de una imagen debe seguir siendo detectable como duplicada."""
    img = imagen_patron(4)
    variante = Image.open(io.BytesIO(a_bytes(img.resize((260, 260))))).convert("RGB")
    a, b = hash_perceptual(img), hash_perceptual(variante)
    assert distancia(a, b) <= 3
    assert set(bandas(a)) & set(bandas(b))


def test_descargar_imagen_registra_el_motivo_del_fallo(caplog):
    """Un fallo silencioso en una descarga de horas es indiagnosticable."""
    sesion = SesionImagen(b"esto no es una imagen")
    with caplog.at_level(logging.DEBUG, logger="pipeline.imagenes"):
        assert descargar_imagen("http://x/rota.jpg", sesion=sesion) is None
    assert "http://x/rota.jpg" in caplog.text


def test_normalizar_limita_el_lado_mayor():
    salida = normalizar(imagen_patron(5, lado=2000), lado_max=800)
    assert max(salida.size) == 800


def test_normalizar_no_agranda_imagenes_pequenas():
    salida = normalizar(imagen_patron(5, lado=300), lado_max=800)
    assert max(salida.size) == 300


def test_descargar_imagen_devuelve_none_si_es_muy_chica():
    sesion = SesionImagen(a_bytes(imagen_patron(6, lado=100)))
    assert descargar_imagen("http://x/y.jpg", sesion=sesion, min_lado=224) is None


def test_descargar_imagen_devuelve_rgb():
    sesion = SesionImagen(a_bytes(imagen_patron(7, lado=400)))
    img = descargar_imagen("http://x/y.jpg", sesion=sesion, min_lado=224)
    assert img is not None and img.mode == "RGB"


def test_descargar_imagen_devuelve_none_si_el_contenido_no_es_imagen():
    sesion = SesionImagen(b"esto no es una imagen")
    assert descargar_imagen("http://x/y.jpg", sesion=sesion) is None


def test_guardar_jpeg_crea_las_carpetas(tmp_path: Path):
    destino = tmp_path / "a" / "b" / "foto.jpg"
    guardar_jpeg(imagen_patron(8), destino)
    assert destino.exists()
    assert Image.open(destino).mode == "RGB"
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_imagenes.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'pipeline.imagenes'`.

- [ ] **Step 3: Implementar `pipeline/imagenes.py`**

```python
"""Descarga, normalización y huella perceptual de imágenes."""
from __future__ import annotations

import io
import logging
from pathlib import Path

import imagehash
from PIL import Image

Image.MAX_IMAGE_PIXELS = 100_000_000  # evita el aviso de bomba de descompresión

# Longitud en caracteres hexadecimales de una huella de 64 bits.
LARGO_HUELLA = 16

_log = logging.getLogger(__name__)


def descargar_imagen(
    url: str, *, sesion, min_lado: int = 224, timeout: int = 30
) -> Image.Image | None:
    """Descarga una imagen. Devuelve None si falla o si es demasiado chica.

    Nunca propaga la excepción: una descarga masiva de horas no puede morir
    por una foto rota. Pero sí registra el motivo, porque sin rastro es
    imposible distinguir "la URL no respondió" de "el archivo está corrupto".
    """
    try:
        respuesta = sesion.get(url, timeout=timeout)
        respuesta.raise_for_status()
        img = Image.open(io.BytesIO(respuesta.content)).convert("RGB")
    except Exception as error:
        _log.debug("no se pudo descargar %s: %s: %s", url, type(error).__name__, error)
        return None
    if min(img.size) < min_lado:
        _log.debug("descartada %s: lado menor %d < %d", url, min(img.size), min_lado)
        return None
    return img


def normalizar(img: Image.Image, lado_max: int = 800) -> Image.Image:
    """Reduce la imagen si excede `lado_max`. Nunca la agranda."""
    if max(img.size) <= lado_max:
        return img
    escala = lado_max / max(img.size)
    nuevo = (round(img.width * escala), round(img.height * escala))
    return img.resize(nuevo, Image.LANCZOS)


def guardar_jpeg(img: Image.Image, ruta: Path, calidad: int = 90) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta, "JPEG", quality=calidad)


def hash_perceptual(img: Image.Image) -> str:
    """Huella de 64 bits en hexadecimal. Resistente a recompresión y escalado.

    Se fuerza minúsculas de forma explícita: `imagehash` hoy siempre las
    produce, pero es un detalle interno de esa librería y no un contrato
    documentado. Fijarlo aquí evita depender de que siga siendo así en una
    versión futura.
    """
    return str(imagehash.phash(img)).lower()


def _normalizada(hash_hex: str) -> str:
    """Rellena la huella a 16 caracteres y la pasa a minúsculas.

    No es redundante: `bandas` trocea por posición de carácter, así que una
    huella deformada por cualquiera de estas dos vías produciría bandas
    desplazadas y sin solape con las de la misma huella bien formada, aunque
    `distancia` (que compara el valor entero) no note ninguna diferencia:

    - un cero a la izquierda perdido al serializarse (longitud < 16), o
    - un cambio de mayúsculas/minúsculas (p. ej. al pasar por un CSV o una
      hoja de cálculo que capitaliza texto).

    En ambos casos el deduplicado dejaría pasar el duplicado en silencio. No
    quitar ninguna de las dos normalizaciones.
    """
    return hash_hex.zfill(LARGO_HUELLA).lower()


def distancia(hash_a: str, hash_b: str) -> int:
    """Distancia de Hamming entre dos huellas hexadecimales."""
    return bin(int(_normalizada(hash_a), 16) ^ int(_normalizada(hash_b), 16)).count("1")


def bandas(hash_hex: str) -> tuple[str, str, str, str]:
    """Parte la huella en 4 bandas de 16 bits.

    Dos huellas a distancia <= 3 comparten al menos una banda idéntica
    (principio del palomar): tres diferencias no pueden repartirse entre
    cuatro bandas disjuntas sin dejar una intacta. Es lo que hace viable
    deduplicar sin comparar todos los pares.
    """
    huella = _normalizada(hash_hex)
    return (huella[0:4], huella[4:8], huella[8:12], huella[12:16])
```

- [ ] **Step 4: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_imagenes.py -v
```

Esperado: PASS, 21 pruebas.

- [ ] **Step 5: Commit**

```powershell
git add pipeline/imagenes.py tests/test_imagenes.py
git commit -m "feat: utilidades de imagen y huella perceptual por bandas"
```

---

## Task 5: Descarga masiva con manifiesto de trazabilidad

**Files:**

- Create: `pipeline/descarga.py`
- Test: `tests/test_descarga.py`

**Interfaces:**

- Consumes: `pipeline.ontologia.cargar_ontologia`, `pipeline.inat.iterar_observaciones`, `pipeline.inat.Observacion`, `pipeline.inat.PAUSA_SEGUNDOS`, `pipeline.imagenes.descargar_imagen`, `normalizar`, `guardar_jpeg`
- Produces:
  - `COLUMNAS_MANIFIESTO: tuple[str, ...]` = `("archivo", "obs_id", "observador", "orden", "familia", "taxon_nombre", "rango", "licencia", "atribucion", "latitud", "longitud", "fecha", "url", "fuente")`
  - `LICENCIAS_PERMITIDAS: frozenset[str]`
  - `INTERVALO_PERSISTENCIA_MANIFIESTO: int = 25`
  - `leer_manifiesto(ruta: Path) -> list[dict]`
  - `escribir_manifiesto(filas: list[dict], ruta: Path) -> None` (escritura atómica vía archivo temporal + `os.replace`)
  - `descargar_clase(orden: str, familia: str, taxon_id: int, *, cupo: int, raiz: Path, ya_descargados: set[int], sesion_api, sesion_img, pausa: float = 1.0, manifiesto_previo: list[dict] = (), intervalo_persistencia: int = INTERVALO_PERSISTENCIA_MANIFIESTO) -> list[dict]`
  - `descargar_todo(onto, *, raiz: Path, cupo_orden: int, cupo_familia: int, sesion_api=None, sesion_img=None) -> list[dict]`

**Diseño de la descarga:** por cada orden se baja una cuota general (`cupo_orden`) etiquetada solo con el orden — esas imágenes alimentan la cabeza de orden aunque su familia se desconozca, y en el manifiesto van con `familia` vacía. Por cada familia declarada se baja además su propia cuota. La reanudación es por `obs_id`: si el manifiesto ya lo tiene, se salta. Así una corrida interrumpida se retoma sin volver a bajar nada.

**Escritura atómica y persistencia incremental (hallazgo de revisión):** `escribir_manifiesto` nunca trunca el destino directamente: arma el CSV completo en un archivo temporal junto al destino y lo reemplaza con `os.replace` solo cuando la escritura terminó sin fallos — el mismo patrón que `importar()` en `pipeline/bd.py`. Sin esto, una interrupción a mitad de una reescritura no solo perdería las filas nuevas: truncaría también las que ya estaban a salvo en disco. Además, dentro de `descargar_clase` la unidad de confirmación no es la clase completa: cada `intervalo_persistencia` imágenes nuevas (25 por defecto) se vuelca a disco el manifiesto acumulado. Sin esto, un corte a mitad de una clase con cupo alto (hasta 1200) dejaría en disco archivos `.jpg` sin fila correspondiente, y al reanudar `ya_descargados` no los reconocería, volviendo a bajarlos de la red.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_descarga.py`:

```python
import csv
import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pipeline.descarga import (
    COLUMNAS_MANIFIESTO,
    descargar_clase,
    escribir_manifiesto,
    leer_manifiesto,
)
from pipeline.inat import Observacion


def bytes_imagen(lado=400):
    rng = np.random.default_rng(1)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(base).resize((lado, lado)).save(buffer, "JPEG")
    return buffer.getvalue()


class SesionImagenOK:
    def __init__(self, lado=400):
        self.contenido = bytes_imagen(lado)
        self.pedidos = []

    def get(self, url, timeout=None):
        self.pedidos.append(url)
        return type("R", (), {"content": self.contenido, "raise_for_status": lambda s: None})()


def obs(oid, licencia="cc-by", observador=None):
    return Observacion(
        id=oid,
        taxon_id=62956,
        taxon_nombre="Ejemplo sp.",
        rango="species",
        observador=observador or f"u{oid}",
        foto_url=f"https://x/{oid}/medium.jpg",
        licencia=licencia,
        atribucion="(c) alguien",
        latitud=-3.7,
        longitud=-73.2,
        fecha="2026-02-01",
    )


def falso_iterador(observaciones):
    def _iterar(taxon_id, *, limite, **kwargs):
        for i, o in enumerate(observaciones):
            if i >= limite:
                return
            yield o

    return _iterar


def test_descarga_guarda_archivos_y_devuelve_filas(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(1), obs(2)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert len(filas) == 2
    for fila in filas:
        assert set(fila) == set(COLUMNAS_MANIFIESTO)
        assert (tmp_path / fila["archivo"]).exists()


def test_ruta_de_archivo_refleja_orden_y_familia(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(7)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=1, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert filas[0]["archivo"] == "OrdenA/FamiliaX/7.jpg"


def test_sin_familia_va_a_carpeta_propia(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(8)]))
    filas = descargar_clase(
        "OrdenA", "", 47208,
        cupo=1, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert filas[0]["archivo"] == "OrdenA/_sin_familia/8.jpg"
    assert filas[0]["familia"] == ""


def test_descarta_licencias_no_permitidas(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(
        mod, "iterar_observaciones", falso_iterador([obs(1, licencia=""), obs(2, licencia="cc0")])
    )
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert [f["obs_id"] for f in filas] == [2]


def test_salta_observaciones_ya_descargadas(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(1), obs(2), obs(3)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados={1, 3},
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert [f["obs_id"] for f in filas] == [2]


def test_respeta_el_cupo(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(i) for i in range(1, 30)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=4, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert len(filas) == 4


def test_imagen_chica_no_entra_al_manifiesto(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(1)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(lado=100), pausa=0,
    )
    assert filas == []


def test_manifiesto_ida_y_vuelta(tmp_path: Path):
    filas = [
        {c: "" for c in COLUMNAS_MANIFIESTO} | {"archivo": "A/B/1.jpg", "obs_id": 1, "observador": "u1"}
    ]
    ruta = tmp_path / "manifiesto.csv"
    escribir_manifiesto(filas, ruta)
    leidas = leer_manifiesto(ruta)
    assert leidas[0]["archivo"] == "A/B/1.jpg"
    assert leidas[0]["obs_id"] == "1"


def test_leer_manifiesto_inexistente_da_lista_vacia(tmp_path: Path):
    assert leer_manifiesto(tmp_path / "no_existe.csv") == []


def test_escritura_interrumpida_no_trunca_el_manifiesto_anterior(tmp_path: Path, monkeypatch):
    """Una escritura que revienta a mitad de camino no debe tocar el archivo anterior.

    `escribir_manifiesto` nunca debe escribir directamente sobre el destino:
    arma el CSV completo en un temporal y solo lo promueve con `os.replace`
    cuando termina sin errores. Se simula el corte parcheando
    `csv.DictWriter.writerows` (el paso que vuelca el cuerpo del CSV, ya con
    la cabecera escrita) para que falle, sin matar el proceso de verdad.
    """
    ruta = tmp_path / "manifiesto.csv"
    filas_previas = [
        {c: "" for c in COLUMNAS_MANIFIESTO} | {"archivo": f"A/B/{i}.jpg", "obs_id": str(i)}
        for i in range(1, 51)
    ]
    escribir_manifiesto(filas_previas, ruta)
    contenido_previo = ruta.read_text(encoding="utf-8")
    assert len(leer_manifiesto(ruta)) == 50

    def _revienta(self, filas):
        raise OSError("fallo de disco simulado a mitad de la reescritura")

    monkeypatch.setattr(csv.DictWriter, "writerows", _revienta)

    filas_nuevas = filas_previas + [
        {c: "" for c in COLUMNAS_MANIFIESTO} | {"archivo": "A/B/99.jpg", "obs_id": "99"}
    ]
    with pytest.raises(OSError):
        escribir_manifiesto(filas_nuevas, ruta)

    assert ruta.read_text(encoding="utf-8") == contenido_previo
    assert len(leer_manifiesto(ruta)) == 50


def test_escritura_interrumpida_no_deja_temporales_huerfanos(tmp_path: Path, monkeypatch):
    ruta = tmp_path / "manifiesto.csv"
    escribir_manifiesto([], ruta)

    def _revienta(self, filas):
        raise OSError("fallo de disco simulado a mitad de la reescritura")

    monkeypatch.setattr(csv.DictWriter, "writerows", _revienta)

    with pytest.raises(OSError):
        escribir_manifiesto([{c: "" for c in COLUMNAS_MANIFIESTO}], ruta)

    restantes = sorted(p.name for p in tmp_path.iterdir())
    assert restantes == ["manifiesto.csv"]


def test_manifiesto_se_persiste_a_mitad_de_una_clase(tmp_path: Path, monkeypatch):
    """Un corte a mitad de una clase no debe dejar el manifiesto vacío.

    Se fuerza un fallo en `guardar_jpeg` (no capturado por `descargar_clase`,
    a diferencia de los fallos de descarga de imagen) después de la quinta
    observación, simulando que el proceso muere ahí. Con
    `intervalo_persistencia=2` deben quedar en disco las filas de los dos
    últimos volcados parciales completados (4), no ninguna.
    """
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(i) for i in range(1, 6)]))

    contador = {"n": 0}
    guardar_original = mod.imagenes.guardar_jpeg

    def guardar_que_revienta_en_la_quinta(img, ruta):
        contador["n"] += 1
        if contador["n"] == 5:
            raise RuntimeError("corte simulado a mitad de la clase")
        guardar_original(img, ruta)

    monkeypatch.setattr(mod.imagenes, "guardar_jpeg", guardar_que_revienta_en_la_quinta)

    with pytest.raises(RuntimeError):
        descargar_clase(
            "OrdenA", "FamiliaX", 62956,
            cupo=5, raiz=tmp_path, ya_descargados=set(),
            sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
            intervalo_persistencia=2,
        )

    filas_persistidas = leer_manifiesto(tmp_path / "manifiesto.csv")
    assert len(filas_persistidas) == 4
    assert [f["obs_id"] for f in filas_persistidas] == ["1", "2", "3", "4"]
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_descarga.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'pipeline.descarga'`.

- [ ] **Step 3: Implementar `pipeline/descarga.py`**

```python
"""Descarga masiva de imágenes con manifiesto de trazabilidad.

El manifiesto es la pieza central del pipeline: arrastra observación,
observador y licencia hasta los splits. Sin él no se puede agrupar por
observador (Tarea 7) ni atribuir las fotos.
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import time
from pathlib import Path

from pipeline import imagenes, inat
from pipeline.inat import iterar_observaciones
from pipeline.ontologia import Ontologia, cargar_ontologia

_log = logging.getLogger(__name__)

COLUMNAS_MANIFIESTO = (
    "archivo",
    "obs_id",
    "observador",
    "orden",
    "familia",
    "taxon_nombre",
    "rango",
    "licencia",
    "atribucion",
    "latitud",
    "longitud",
    "fecha",
    "url",
    "fuente",
)

# Códigos de licencia de iNaturalist que permiten uso y redistribución con
# atribución. Una licencia vacía significa "todos los derechos reservados".
LICENCIAS_PERMITIDAS = frozenset(
    {"cc0", "cc-by", "cc-by-nc", "cc-by-sa", "cc-by-nc-sa", "cc-by-nd", "cc-by-nc-nd"}
)

# Carpeta donde caen las imágenes de la cuota de orden, cuya familia se
# desconoce (o cuyo taxón identificado no llega a nivel de familia).
SIN_FAMILIA = "_sin_familia"

# Cada cuántas imágenes NUEVAS, dentro de una misma clase, se vuelca el
# manifiesto completo a disco (además del volcado al terminar la clase).
# 25 acota lo que se repetiría al reanudar tras un corte a menos del 4% de
# la cuota más chica (600, la de familia) sin multiplicar en exceso las
# reescrituras completas del archivo, que crecen con el tamaño total del
# manifiesto: un valor mucho más chico paga esa reescritura completa muchas
# más veces de las necesarias; uno mucho más grande deja de proteger nada.
INTERVALO_PERSISTENCIA_MANIFIESTO = 25


def leer_manifiesto(ruta: Path) -> list[dict]:
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def escribir_manifiesto(filas: list[dict], ruta: Path) -> None:
    """Escribe el manifiesto de forma atómica.

    Nunca trunca `ruta` directamente: arma el CSV completo en un archivo
    temporal junto al destino y lo reemplaza con `os.replace` solo cuando la
    escritura terminó sin fallos (mismo patrón que `importar()` en
    `pipeline/bd.py`). `descargar_todo` llama a esta función una y otra vez
    sobre el manifiesto completo y creciente, así que sin esta protección
    una interrupción a mitad de una reescritura no solo perdería las filas
    nuevas: truncaría también las que ya estaban a salvo en disco.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta_temporal = ruta.with_name(f".{ruta.name}.tmp-{os.getpid()}")
    ruta_temporal.unlink(missing_ok=True)  # restos de una corrida anterior interrumpida

    try:
        with ruta_temporal.open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_MANIFIESTO))
            escritor.writeheader()
            escritor.writerows(filas)
        os.replace(ruta_temporal, ruta)
    except Exception:
        ruta_temporal.unlink(missing_ok=True)
        raise


def descargar_clase(
    orden: str,
    familia: str,
    taxon_id: int,
    *,
    cupo: int,
    raiz: Path,
    ya_descargados: set[int],
    sesion_api,
    sesion_img,
    pausa: float = inat.PAUSA_SEGUNDOS,
    manifiesto_previo: list[dict] = (),
    intervalo_persistencia: int = INTERVALO_PERSISTENCIA_MANIFIESTO,
) -> list[dict]:
    """Descarga hasta `cupo` imágenes nuevas para una clase.

    Se pide un margen de `cupo * 3` observaciones al iterador porque se
    descartan las ya vistas, las de licencia no permitida y las de imagen
    inservible. Si aun con ese margen no se alcanza el cupo, no se falla en
    silencio: se deja constancia en el log de cuánto faltó y por qué se
    descartó cada observación, junto con una pista de si el margen se agotó
    (la fuente tenía observaciones de sobra pero se descartaron demasiadas)
    o si la fuente simplemente no tenía más observaciones que ofrecer. Sin
    ese aviso, una corrida de horas podría dejar una clase corta sin que
    nadie lo note hasta que la regla de admisión posterior la descarte.

    La unidad de confirmación en el manifiesto no es la clase completa: cada
    `intervalo_persistencia` imágenes nuevas se vuelca a disco el manifiesto
    acumulado (`manifiesto_previo` más lo bajado hasta ese punto). Sin esto,
    un corte a mitad de una clase con cupo alto (hasta 1200) dejaría en disco
    archivos `.jpg` sin fila correspondiente: no contaminan el dataset -la
    curación solo copia lo que figura en el manifiesto-, pero al reanudar
    `ya_descargados` no los reconoce y la corrida los vuelve a bajar de la
    red, tirando ese trabajo.
    """
    carpeta = familia or SIN_FAMILIA
    ruta_manifiesto = Path(raiz) / "manifiesto.csv"
    filas: list[dict] = []
    vistas = 0
    descartes_repetida = 0
    descartes_licencia = 0
    descartes_imagen = 0

    for observacion in iterar_observaciones(
        taxon_id, limite=cupo * 3, sesion=sesion_api, pausa=pausa
    ):
        if len(filas) >= cupo:
            break
        vistas += 1
        if observacion.id in ya_descargados:
            descartes_repetida += 1
            continue
        if observacion.licencia not in LICENCIAS_PERMITIDAS:
            descartes_licencia += 1
            continue

        img = imagenes.descargar_imagen(observacion.foto_url, sesion=sesion_img)
        if img is None:
            descartes_imagen += 1
            continue

        relativo = f"{orden}/{carpeta}/{observacion.id}.jpg"
        imagenes.guardar_jpeg(imagenes.normalizar(img), Path(raiz) / relativo)
        ya_descargados.add(observacion.id)
        filas.append(
            {
                "archivo": relativo,
                "obs_id": observacion.id,
                "observador": observacion.observador,
                "orden": orden,
                "familia": familia,
                "taxon_nombre": observacion.taxon_nombre,
                "rango": observacion.rango,
                "licencia": observacion.licencia,
                "atribucion": observacion.atribucion,
                "latitud": observacion.latitud if observacion.latitud is not None else "",
                "longitud": observacion.longitud if observacion.longitud is not None else "",
                "fecha": observacion.fecha,
                "url": observacion.foto_url,
                "fuente": "iNaturalist",
            }
        )
        if intervalo_persistencia and len(filas) % intervalo_persistencia == 0:
            escribir_manifiesto(list(manifiesto_previo) + filas, ruta_manifiesto)
        if pausa:
            time.sleep(pausa * 0.15)

    if len(filas) < cupo:
        # `vistas` llega a cupo * 3 solo si el iterador tenía tanto material
        # como se le pidió; si se quedó corto, la causa es la propia fuente,
        # no el margen de 3x.
        margen_insuficiente = vistas >= cupo * 3
        motivo = (
            "el margen de 3x no alcanzó (demasiados descartes)"
            if margen_insuficiente
            else "la fuente no tenía más observaciones que ofrecer"
        )
        _log.warning(
            "%s/%s: cupo no alcanzado (%d de %d). %s. "
            "observaciones vistas=%d, descartadas por ya_descargada=%d, "
            "licencia_no_permitida=%d, imagen_inservible=%d",
            orden, carpeta, len(filas), cupo, motivo,
            vistas, descartes_repetida, descartes_licencia, descartes_imagen,
        )
    return filas


def descargar_todo(
    onto: Ontologia,
    *,
    raiz: Path,
    cupo_orden: int,
    cupo_familia: int,
    sesion_api=None,
    sesion_img=None,
) -> list[dict]:
    """Descarga la cuota de cada orden y de cada familia declarada.

    La reanudación es por `obs_id`: si el manifiesto ya existente en `raiz`
    lo tiene, se salta. Así una corrida interrumpida se retoma sin volver a
    bajar nada. El manifiesto se reescribe después de cada clase, para no
    perder lo ya bajado si la corrida se corta a mitad de camino.
    """
    sesion_api = sesion_api or inat.nueva_sesion()
    sesion_img = sesion_img or inat.nueva_sesion()
    raiz = Path(raiz)

    manifiesto = leer_manifiesto(raiz / "manifiesto.csv")
    ya = {int(f["obs_id"]) for f in manifiesto if f.get("obs_id")}

    for orden in sorted(onto.ordenes, key=lambda o: o.nombre):
        print(f"[{orden.nombre}] cuota de orden (cupo {cupo_orden})...")
        nuevas = descargar_clase(
            orden.nombre, "", orden.inat_taxon_id,
            cupo=cupo_orden, raiz=raiz, ya_descargados=ya,
            sesion_api=sesion_api, sesion_img=sesion_img,
            manifiesto_previo=manifiesto,
        )
        manifiesto += nuevas
        escribir_manifiesto(manifiesto, raiz / "manifiesto.csv")
        print(f"  +{len(nuevas)} imágenes")

        for fam in sorted(orden.familias, key=lambda f: f.nombre):
            print(f"[{orden.nombre}/{fam.nombre}] (cupo {cupo_familia})...")
            nuevas = descargar_clase(
                orden.nombre, fam.nombre, fam.inat_taxon_id,
                cupo=cupo_familia, raiz=raiz, ya_descargados=ya,
                sesion_api=sesion_api, sesion_img=sesion_img,
                manifiesto_previo=manifiesto,
            )
            manifiesto += nuevas
            escribir_manifiesto(manifiesto, raiz / "manifiesto.csv")
            print(f"  +{len(nuevas)} imágenes")

    return manifiesto


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga de imágenes por clase")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--raiz", default="datos/crudo")
    parser.add_argument("--cupo-orden", type=int, default=1200)
    parser.add_argument("--cupo-familia", type=int, default=600)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    onto = cargar_ontologia(Path(args.ontologia))
    manifiesto = descargar_todo(
        onto,
        raiz=Path(args.raiz),
        cupo_orden=args.cupo_orden,
        cupo_familia=args.cupo_familia,
    )
    print(f"Manifiesto con {len(manifiesto)} imágenes en {args.raiz}/manifiesto.csv")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_descarga.py -v
```

Esperado: PASS, 12 pruebas.

- [ ] **Step 5: Prueba de humo con cupos mínimos contra la API real**

```powershell
.venv\Scripts\python -m pipeline.descarga --cupo-orden 5 --cupo-familia 5 --raiz datos/prueba
```

Esperado: carpetas por orden con archivos `.jpg` y un `manifiesto.csv` con columna `licencia` no vacía en todas las filas. Verificar:

```powershell
.venv\Scripts\python -c "from pipeline.descarga import leer_manifiesto; f=leer_manifiesto('datos/prueba/manifiesto.csv'); print(len(f)); print(sorted({x['licencia'] for x in f}))"
```

- [ ] **Step 6: Correr la descarga completa** (varias horas; dejar corriendo)

```powershell
.venv\Scripts\python -m pipeline.descarga
```

Si se interrumpe, volver a lanzarla: retoma desde el manifiesto.

- [ ] **Step 7: Commit**

```powershell
git add pipeline/descarga.py tests/test_descarga.py
git commit -m "feat: descarga masiva con manifiesto de trazabilidad y licencias"
```

---

## Task 6: Curación — deduplicado y filtros de calidad

**Files:**

- Create: `pipeline/curacion.py`
- Test: `tests/test_curacion.py`

**Interfaces:**

- Consumes: `pipeline.descarga.leer_manifiesto`, `escribir_manifiesto`, `COLUMNAS_MANIFIESTO`; `pipeline.imagenes.hash_perceptual`, `distancia`, `bandas`
- Produces:
  - `COLUMNAS_CURADO: tuple[str, ...]` = `COLUMNAS_MANIFIESTO + ("hash",)`
  - `NOMBRE_MANIFIESTO_CURADO: str = "manifiesto_curado.csv"`
  - `MARCA_DESTINO: str = ".curacion_destino"` — archivo centinela que marca `raiz_curado` como administrado por `curar()`.
  - `class ErrorDestinoNoReconocido(Exception)` — `raiz_curado` existe, tiene contenido y no lleva la marca de una corrida anterior.
  - `hashes_de(filas: list[dict], raiz: Path) -> list[dict]`
  - `deduplicar(filas: list[dict], *, umbral: int = 3, hashes_externos: set[str] | None = None) -> tuple[list[dict], list[dict]]`
  - `curar(raiz_crudo: Path, raiz_curado: Path, *, umbral: int = 3, hashes_externos: set[str] | None = None) -> dict`
  - `reporte_markdown(resumen: dict) -> str`

**Nota sobre el orden de descarte:** una imagen puede aparecer dos veces legítimamente — la cuota del orden y la cuota de la familia pueden traer la misma observación. Al deduplicar se conserva **la fila con familia declarada** frente a la que tiene familia vacía, porque aporta más información de etiqueta.

**Reconciliación del destino y marca de propiedad (hallazgo de revisión):** `curar()` reconcilia `raiz_curado` — borra ahí cualquier archivo que ya no figure en el manifiesto curado (por ejemplo, tras corregir la descarga de origen), para que nada quede huérfano y visible a un `ImageFolder` que liste carpetas en vez de leer el manifiesto. Pero reconciliar sin saber si el directorio es "propio" es peligroso: una primera corrida contra una carpeta ajena (una ruta `--curado` mal escrita) podría acabar borrando contenido de otra persona en una segunda corrida. Por eso `curar()` primero verifica el destino (`_verificar_destino`): si `raiz_curado` existe, tiene contenido, y no lleva el archivo-marca `MARCA_DESTINO` de una corrida anterior, se rechaza con `ErrorDestinoNoReconocido` **sin escribir nada**. La marca se escribe al **inicio** de la corrida (antes de copiar nada), no al final, porque una corrida real dura horas y es justo el tipo de proceso que se interrumpe a mitad de camino: si la marca dependiera del manifiesto (que se escribe al final), un corte o un manifiesto borrado a mano dejarían el directorio sin identificar. La marca solo cuenta si es un **archivo regular** (`.is_file()`, nunca `.exists()`): un directorio que por accidente se llame igual no debe confundirse con ella.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_curacion.py`:

```python
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pipeline.curacion import (
    COLUMNAS_CURADO,
    MARCA_DESTINO,
    ErrorDestinoNoReconocido,
    curar,
    deduplicar,
    hashes_de,
    reporte_markdown,
)
from pipeline.descarga import COLUMNAS_MANIFIESTO, escribir_manifiesto, leer_manifiesto


def fila(archivo, obs_id, orden="OrdenA", familia="FamX", hash_=None):
    base = {c: "" for c in COLUMNAS_MANIFIESTO}
    base.update(archivo=archivo, obs_id=str(obs_id), orden=orden, familia=familia,
                observador=f"u{obs_id}", licencia="cc-by")
    if hash_ is not None:
        base["hash"] = hash_
    return base


def escribir_imagen(raiz: Path, relativo: str, semilla: int, lado: int = 300):
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    destino = raiz / relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(base).resize((lado, lado), Image.BICUBIC).save(destino, "JPEG", quality=90)


def test_deduplicar_conserva_una_de_dos_identicas():
    filas = [fila("a.jpg", 1, hash_="ffff0000ffff0000"), fila("b.jpg", 2, hash_="ffff0000ffff0000")]
    conservadas, descartadas = deduplicar(filas)
    assert len(conservadas) == 1
    assert len(descartadas) == 1
    assert descartadas[0]["motivo"] == "duplicado"


def test_deduplicar_no_toca_imagenes_distintas():
    filas = [fila("a.jpg", 1, hash_="ffff0000ffff0000"), fila("b.jpg", 2, hash_="0000ffff0000ffff")]
    conservadas, descartadas = deduplicar(filas)
    assert len(conservadas) == 2
    assert descartadas == []


def test_deduplicar_prefiere_la_fila_con_familia():
    filas = [
        fila("sin.jpg", 1, familia="", hash_="ffff0000ffff0000"),
        fila("con.jpg", 2, familia="FamX", hash_="ffff0000ffff0000"),
    ]
    conservadas, _ = deduplicar(filas)
    assert conservadas[0]["familia"] == "FamX"


def test_deduplicar_descarta_contra_hashes_externos():
    filas = [fila("a.jpg", 1, hash_="ffff0000ffff0000")]
    conservadas, descartadas = deduplicar(filas, hashes_externos={"ffff0000ffff0000"})
    assert conservadas == []
    assert descartadas[0]["motivo"] == "duplicado_externo"


def test_hashes_de_marca_los_archivos_ilegibles(tmp_path: Path):
    escribir_imagen(tmp_path, "ok.jpg", 1)
    (tmp_path / "roto.jpg").write_bytes(b"no soy una imagen")
    filas = [fila("ok.jpg", 1), fila("roto.jpg", 2)]
    resultado = hashes_de(filas, tmp_path)
    assert resultado[0]["hash"]
    assert resultado[1]["hash"] == ""


def test_curar_copia_solo_las_conservadas(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 1)   # misma semilla: duplicada
    escribir_imagen(crudo, "OrdenA/FamX/3.jpg", 77)  # distinta
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2), fila("OrdenA/FamX/3.jpg", 3)],
        crudo / "manifiesto.csv",
    )

    resumen = curar(crudo, curado)

    assert resumen["entrada"] == 3
    assert resumen["conservadas"] == 2
    assert (curado / "manifiesto_curado.csv").exists()
    copiadas = list(curado.rglob("*.jpg"))
    assert len(copiadas) == 2


def test_manifiesto_curado_incluye_la_columna_hash(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 5)
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")
    curar(crudo, curado)
    texto = (curado / "manifiesto_curado.csv").read_text(encoding="utf-8")
    assert "hash" in texto.splitlines()[0]
    assert set(COLUMNAS_CURADO) == set(COLUMNAS_MANIFIESTO) | {"hash"}


def test_curar_descarta_archivos_ilegibles(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 6)
    (crudo / "OrdenA/FamX/2.jpg").write_bytes(b"basura")
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2)], crudo / "manifiesto.csv"
    )
    resumen = curar(crudo, curado)
    assert resumen["conservadas"] == 1
    assert resumen["por_motivo"]["ilegible"] == 1


def test_segunda_corrida_elimina_archivos_que_el_manifiesto_ya_no_incluye(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 77)
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2)],
        crudo / "manifiesto.csv",
    )
    curar(crudo, curado)
    assert (curado / "OrdenA/FamX/2.jpg").exists()

    # La descarga se corrige y el manifiesto de origen ya no trae la obs. 2.
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")
    curar(crudo, curado)

    assert not (curado / "OrdenA/FamX/2.jpg").exists()
    assert (curado / "OrdenA/FamX/1.jpg").exists()


def test_destino_coincide_exactamente_con_el_manifiesto_curado(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 1)   # duplicada de la 1
    escribir_imagen(crudo, "OrdenA/FamX/3.jpg", 77)
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2), fila("OrdenA/FamX/3.jpg", 3)],
        crudo / "manifiesto.csv",
    )

    curar(crudo, curado)

    conservadas = leer_manifiesto(curado / "manifiesto_curado.csv")
    rutas_del_manifiesto = {(curado / c["archivo"]).resolve() for c in conservadas}
    rutas_en_disco = {p.resolve() for p in curado.rglob("*.jpg")}
    assert rutas_en_disco == rutas_del_manifiesto


def test_curar_es_idempotente_en_corridas_repetidas(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 1)   # duplicada de la 1
    escribir_imagen(crudo, "OrdenA/FamX/3.jpg", 77)
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2), fila("OrdenA/FamX/3.jpg", 3)],
        crudo / "manifiesto.csv",
    )

    resumen_1 = curar(crudo, curado)
    archivos_1 = sorted(p.relative_to(curado) for p in curado.rglob("*.jpg"))

    resumen_2 = curar(crudo, curado)
    archivos_2 = sorted(p.relative_to(curado) for p in curado.rglob("*.jpg"))

    assert resumen_1 == resumen_2
    assert archivos_1 == archivos_2


def test_borrar_el_manifiesto_a_mano_no_impide_reconciliar_en_la_siguiente_corrida(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 77)
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2)],
        crudo / "manifiesto.csv",
    )
    curar(crudo, curado)
    assert (curado / "OrdenA/FamX/2.jpg").exists()

    # Alguien borra el manifiesto curado a mano entre corridas.
    (curado / "manifiesto_curado.csv").unlink()

    # El manifiesto de origen tambien se corrige y ya no trae la obs. 2.
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")
    curar(crudo, curado)

    assert not (curado / "OrdenA/FamX/2.jpg").exists()
    assert (curado / "OrdenA/FamX/1.jpg").exists()


def test_corrida_interrumpida_deja_el_destino_marcado_y_se_reconcilia_despues(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")

    # Simula una corrida anterior que murio a mitad de camino: alcanzo a
    # marcar el destino y a copiar una imagen, pero nunca llego a escribir
    # el manifiesto curado.
    huerfano = curado / "OrdenA/FamX/99.jpg"
    huerfano.parent.mkdir(parents=True)
    huerfano.write_bytes(b"copia parcial de una corrida interrumpida")
    (curado / MARCA_DESTINO).write_text("marca", encoding="utf-8")
    assert not (curado / "manifiesto_curado.csv").exists()

    curar(crudo, curado)

    assert not huerfano.exists()
    assert (curado / "OrdenA/FamX/1.jpg").exists()


def test_destino_con_contenido_y_sin_marca_es_rechazado_sin_escribir_nada(tmp_path: Path):
    """Reemplaza a la prueba anterior de "no pierde contenido previo".

    Antes, una corrida contra una carpeta ajena no borraba nada, pero SÍ la
    marcaba y copiaba imágenes -dejándola lista para que una segunda corrida
    con la misma ruta equivocada sí la reconociera como propia y borrara el
    contenido del usuario-. Ahora la primera corrida debe rechazarse por
    completo: ni marca, ni imágenes, ni manifiesto. Se verifica el contenido
    de la carpeta antes y después, incluida una subcarpeta anidada.
    """
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")

    # `curado` ya existe con contenido ajeno: nunca fue administrado por
    # curar() (no tiene la marca de propiedad).
    curado.mkdir(parents=True)
    notas = curado / "notas_del_entomologo.txt"
    notas.write_text("no tocar", encoding="utf-8")
    foto_personal = curado / "fotos_personales" / "familia.jpg"
    foto_personal.parent.mkdir(parents=True)
    foto_personal.write_bytes(b"una foto que no tiene nada que ver con el dataset")

    contenido_antes = sorted(p.relative_to(curado) for p in curado.rglob("*") if p.is_file())

    with pytest.raises(ErrorDestinoNoReconocido):
        curar(crudo, curado)

    contenido_despues = sorted(p.relative_to(curado) for p in curado.rglob("*") if p.is_file())
    assert contenido_despues == contenido_antes
    assert notas.read_text(encoding="utf-8") == "no tocar"
    assert not (curado / MARCA_DESTINO).exists()
    assert not (curado / "manifiesto_curado.csv").exists()


def test_directorio_con_el_nombre_de_la_marca_no_cuenta_como_marca(tmp_path: Path):
    """Un directorio llamado como `MARCA_DESTINO` no es una marca válida.

    Antes de este arreglo, la marca se reconocía con `.exists()`, verdadero
    tanto para un archivo como para un directorio. Una carpeta con ese
    nombre -por accidente, o por un descomprimido raro- pasaba como marca
    válida: `curar()` asumía la propiedad total del directorio y la
    reconciliación borraba cualquier otro contenido que hubiera ahí, sin
    que hiciera falta ninguna corrida previa.
    """
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")

    curado.mkdir(parents=True)
    (curado / MARCA_DESTINO).mkdir()  # directorio-disfraz, no un archivo
    otro = curado / "otro_archivo.txt"
    otro.write_text("contenido ajeno", encoding="utf-8")

    with pytest.raises(ErrorDestinoNoReconocido):
        curar(crudo, curado)

    assert otro.exists()
    assert otro.read_text(encoding="utf-8") == "contenido ajeno"
    assert (curado / MARCA_DESTINO).is_dir()  # el directorio-disfraz sigue intacto


def test_marca_que_es_archivo_regular_sigue_funcionando_como_antes(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")

    curado.mkdir(parents=True)
    (curado / MARCA_DESTINO).write_text("marca", encoding="utf-8")  # marca valida: archivo regular
    huerfano = curado / "OrdenA/FamX/99.jpg"
    huerfano.parent.mkdir(parents=True)
    huerfano.write_bytes(b"restos de una corrida anterior")

    resumen = curar(crudo, curado)

    assert resumen["conservadas"] == 1
    assert (curado / "OrdenA/FamX/1.jpg").exists()
    assert not huerfano.exists()  # se reconcilio con normalidad, como antes de este arreglo


def test_destino_existente_y_vacio_se_acepta_con_normalidad(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")

    curado.mkdir(parents=True)  # existe, pero vacio

    resumen = curar(crudo, curado)

    assert resumen["conservadas"] == 1
    assert (curado / "OrdenA/FamX/1.jpg").exists()
    assert (curado / MARCA_DESTINO).exists()


def test_destino_inexistente_se_acepta_con_normalidad(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")

    assert not curado.exists()

    resumen = curar(crudo, curado)

    assert resumen["conservadas"] == 1
    assert (curado / "OrdenA/FamX/1.jpg").exists()


def test_destino_ya_marcado_de_corrida_previa_se_acepta_y_reconcilia(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 77)
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2)],
        crudo / "manifiesto.csv",
    )
    curar(crudo, curado)  # primera corrida: deja la marca puesta

    # El manifiesto de origen se corrige y ya no trae la obs. 2.
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")
    resumen = curar(crudo, curado)  # segunda corrida: destino ya marcado

    assert resumen["conservadas"] == 1
    assert (curado / "OrdenA/FamX/1.jpg").exists()
    assert not (curado / "OrdenA/FamX/2.jpg").exists()


def test_reporte_menciona_el_factor_real_de_curacion():
    resumen = {
        "entrada": 100,
        "conservadas": 60,
        "por_motivo": {"duplicado": 30, "ilegible": 10},
        "por_clase": {"OrdenA/FamX": 60},
    }
    texto = reporte_markdown(resumen)
    assert "1.67" in texto  # 100/60, el factor a comparar con el estimado del censo
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_curacion.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'pipeline.curacion'`.

- [ ] **Step 3: Implementar `pipeline/curacion.py`**

```python
"""Curación del dataset: deduplicado perceptual y descarte de archivos malos.

El deduplicado usa indexado por bandas: dos huellas a distancia <= 3
comparten al menos una banda de 16 bits, así que basta comparar dentro de
cada cubeta en vez de todos los pares.
"""
from __future__ import annotations

import argparse
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image

from pipeline import imagenes
from pipeline.descarga import COLUMNAS_MANIFIESTO, leer_manifiesto

COLUMNAS_CURADO = COLUMNAS_MANIFIESTO + ("hash",)

# Nombre del manifiesto que `curar` escribe en `raiz_curado`.
NOMBRE_MANIFIESTO_CURADO = "manifiesto_curado.csv"

# Archivo centinela que marca `raiz_curado` como un directorio administrado
# por `curar()`. A diferencia del manifiesto, se escribe al INICIO de la
# corrida, antes de copiar nada: una descarga y curación real dura horas y
# es justo el tipo de proceso que se interrumpe a mitad de camino, o al que
# alguien le borra el manifiesto a mano entre corridas. Si la marca dependiera
# del manifiesto (que se escribe al final), cualquiera de esos dos casos
# dejaría el directorio sin identificar y la siguiente corrida no
# reconciliaría los archivos huérfanos. Ver `_marcar_destino` y `curar`.
# No es basura: no borrar.
#
# La marca solo cuenta si es un ARCHIVO REGULAR: en todo el módulo se
# comprueba con `.is_file()`, nunca con `.exists()`. Un directorio que por
# accidente (o por un descomprimido raro) se llame igual que la marca no
# debe confundirse con ella -si `.exists()` bastara, cualquier carpeta con
# ese nombre haría que `curar()` asumiera la propiedad total del directorio
# y reconciliara -es decir, borrara- contenido ajeno sin que hubiera existido
# ninguna corrida previa.
MARCA_DESTINO = ".curacion_destino"


class ErrorDestinoNoReconocido(Exception):
    """`raiz_curado` existe, tiene contenido y no es un destino de curación."""


def hashes_de(filas: list[dict], raiz: Path) -> list[dict]:
    """Añade la columna `hash` a cada fila. Vacía si el archivo es ilegible."""
    raiz = Path(raiz)
    salida = []
    for fila in filas:
        copia = dict(fila)
        try:
            with Image.open(raiz / fila["archivo"]) as img:
                copia["hash"] = imagenes.hash_perceptual(img.convert("RGB"))
        except Exception:
            copia["hash"] = ""
        salida.append(copia)
    return salida


def _prioridad(fila: dict) -> tuple[int, int]:
    """Ordena para que, entre duplicadas, gane la fila con familia declarada."""
    return (0 if fila.get("familia") else 1, int(fila.get("obs_id") or 0))


def deduplicar(
    filas: list[dict], *, umbral: int = 3, hashes_externos: set[str] | None = None
) -> tuple[list[dict], list[dict]]:
    """Separa las filas en conservadas y descartadas."""
    externos = hashes_externos or set()
    conservadas: list[dict] = []
    descartadas: list[dict] = []
    indice: dict[str, list[str]] = defaultdict(list)  # banda -> huellas conservadas

    for fila in sorted(filas, key=_prioridad):
        huella = fila.get("hash", "")
        if not huella:
            descartadas.append(dict(fila, motivo="ilegible"))
            continue

        if any(imagenes.distancia(huella, ext) <= umbral for ext in externos):
            descartadas.append(dict(fila, motivo="duplicado_externo"))
            continue

        candidatas = {c for banda in imagenes.bandas(huella) for c in indice[banda]}
        if any(imagenes.distancia(huella, c) <= umbral for c in candidatas):
            descartadas.append(dict(fila, motivo="duplicado"))
            continue

        conservadas.append(fila)
        for banda in imagenes.bandas(huella):
            indice[banda].append(huella)

    return conservadas, descartadas


def _escribir_curado(filas: list[dict], ruta: Path) -> None:
    import csv

    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({c: fila.get(c, "") for c in COLUMNAS_CURADO})


def _verificar_destino(raiz_curado: Path) -> None:
    """Rechaza `raiz_curado` si existe, tiene contenido y no es propio.

    Se llama antes de marcar y antes de copiar nada. Sin esta comprobación,
    una primera corrida contra una carpeta ajena (p. ej. `--curado` escrito
    por error) no borraba nada -correcto-, pero SÍ la marcaba y copiaba
    imágenes ahí, dejándola lista para que una segunda corrida con la misma
    ruta equivocada la reconociera como propia y borrara el contenido del
    usuario. Basta con equivocarse dos veces con la misma ruta, algo
    plausible en una herramienta de línea de comandos. Rechazar de entrada,
    sin tocar nada, cierra esa ventana: un directorio ajeno con contenido
    nunca llega a marcarse.

    No aplica a los tres casos legítimos: destino inexistente, existente y
    vacío, o ya marcado por una corrida anterior. La marca solo cuenta si es
    un archivo regular (`.is_file()`, no `.exists()`): un directorio que por
    accidente se llame igual no es una marca válida, así que cae en la
    comprobación de contenido de más abajo y el destino se rechaza -es
    justamente el caso que se quiere atrapar-.
    """
    if not raiz_curado.exists():
        return
    if (raiz_curado / MARCA_DESTINO).is_file():
        return
    if any(raiz_curado.iterdir()):
        raise ErrorDestinoNoReconocido(
            f"'{raiz_curado}' ya existe, tiene contenido, y no parece un "
            f"destino de curación (no tiene la marca '{MARCA_DESTINO}' de una "
            "corrida anterior de curar()). Para no arriesgarse a borrar "
            "archivos ajenos por una ruta --curado mal escrita, curar() se "
            "detiene sin tocar nada. Usa una carpeta vacía o inexistente "
            "para --curado, o verifica que esta sea realmente la carpeta de "
            "una corrida de curación anterior."
        )


def _marcar_destino(raiz_curado: Path) -> None:
    """Crea la marca de propiedad de `raiz_curado` si todavía no existe.

    Se llama al principio de `curar`, antes de copiar nada, para que incluso
    una corrida que se interrumpe a mitad de camino deje el directorio
    identificado como propio: la siguiente corrida completa podrá
    reconciliar lo que esta alcanzó a copiar.

    En el flujo normal de `curar`, `_verificar_destino` ya descartó antes
    cualquier directorio-disfraz con ese nombre (cuenta como "contenido" y
    el destino se rechaza). Pero si algo distinto a un archivo regular
    ocupara esta ruta -por ejemplo, si se llamara a esta función fuera de
    ese flujo-, escribir ahí fallaría con una excepción cruda del sistema
    de archivos (`IsADirectoryError` en algunos sistemas, `PermissionError`
    en otros). Se comprueba explícitamente para fallar con un mensaje
    legible en su lugar.
    """
    marca = raiz_curado / MARCA_DESTINO
    if marca.is_file():
        return
    if marca.exists():
        raise ErrorDestinoNoReconocido(
            f"'{marca}' ya existe pero no es un archivo regular, así que no "
            f"puede usarse como marca de propiedad de '{raiz_curado}'. "
            "Elimina manualmente esa ruta -revisando antes que no sea nada "
            "importante- y vuelve a correr curar()."
        )
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(
        "Este directorio es administrado por pipeline.curacion.curar().\n"
        "No borrar este archivo: sin él, curar() no puede distinguir este\n"
        "directorio de una carpeta ajena y deja de reconciliar archivos\n"
        "huerfanos entre corridas, para no arriesgarse a borrar algo que no\n"
        "puso.\n",
        encoding="utf-8",
    )


def _reconciliar_destino(raiz_curado: Path, conservadas: list[dict]) -> None:
    """Deja en `raiz_curado` solo los archivos listados en `conservadas`.

    Una corrida anterior pudo haber copiado imágenes que esta corrida ya no
    conserva -por ejemplo, si el manifiesto de origen cambió entre medio, o
    si una corrida previa murió a mitad de la copia-. Sin esto esos archivos
    quedarían huérfanos: sin fila que los respalde en el CSV, pero visibles
    para cualquier cargador que liste carpetas directamente en vez de leer
    el manifiesto (así funcionan los `ImageFolder` típicos), coleándose al
    entrenamiento sin trazabilidad, sin licencia y sin haber pasado por el
    particionado por observador de la Tarea 7.

    Quien llama (`curar`) decide cuándo invocar esta función: solo cuando
    `raiz_curado` ya era, antes de esta corrida, un directorio propio (ver
    `MARCA_DESTINO` y `_marcar_destino`). No se repite esa comprobación aquí
    porque para este punto `_marcar_destino` ya escribió la marca de esta
    misma corrida, y comprobar su existencia ahora siempre daría verdadero.

    ADVERTENCIA sobre el alcance del borrado: una vez que `raiz_curado` está
    legítimamente marcado, esta función borra TODO lo que no esté en
    `conservadas` (salvo el manifiesto y la marca) -incluido cualquier
    contenido ajeno que hubiera quedado ahí de antes, aunque no lo haya
    puesto `curar()`-. Esto es intencional, no un descuido: la marca
    significa "este directorio me pertenece por completo", no "reconcilia
    solo lo que yo mismo copié". `_verificar_destino` es la única barrera
    contra perder contenido ajeno, y actúa antes de marcar; una vez marcado,
    el directorio es del todo de `curar()`.
    """
    protegidos = {
        (raiz_curado / NOMBRE_MANIFIESTO_CURADO).resolve(),
        (raiz_curado / MARCA_DESTINO).resolve(),
    }
    esperados = {(raiz_curado / fila["archivo"]).resolve() for fila in conservadas}
    for existente in raiz_curado.rglob("*"):
        if existente.is_file():
            resuelta = existente.resolve()
            if resuelta not in protegidos and resuelta not in esperados:
                existente.unlink()

    # Elimina las carpetas de clase que quedaron vacías tras el borrado,
    # de las más profundas a las más superficiales.
    carpetas = sorted(
        (p for p in raiz_curado.rglob("*") if p.is_dir()),
        key=lambda p: len(p.parts),
        reverse=True,
    )
    for carpeta in carpetas:
        if not any(carpeta.iterdir()):
            carpeta.rmdir()


def curar(
    raiz_crudo: Path,
    raiz_curado: Path,
    *,
    umbral: int = 3,
    hashes_externos: set[str] | None = None,
) -> dict:
    """Cura el dataset completo y devuelve el resumen de lo ocurrido.

    Lanza `ErrorDestinoNoReconocido` si `raiz_curado` existe, tiene
    contenido y no lleva la marca de una corrida anterior -ver
    `_verificar_destino`-, sin escribir absolutamente nada en ese caso.
    """
    raiz_crudo, raiz_curado = Path(raiz_crudo), Path(raiz_curado)
    _verificar_destino(raiz_curado)

    # Se determina ANTES de tocar nada: si la marca ya estaba puesta, este
    # directorio es propio desde una corrida anterior -completa o
    # interrumpida- y es seguro reconciliarlo. Si no estaba, gracias a
    # `_verificar_destino` sabemos que el directorio no existía o estaba
    # vacío -nunca contenido ajeno-, así que esta primera corrida no tiene
    # nada que reconciliar; solo deja la marca puesta para que la siguiente
    # sí pueda.
    directorio_ya_propio = (raiz_curado / MARCA_DESTINO).is_file()
    _marcar_destino(raiz_curado)

    filas = leer_manifiesto(raiz_crudo / "manifiesto.csv")
    con_hash = hashes_de(filas, raiz_crudo)
    conservadas, descartadas = deduplicar(
        con_hash, umbral=umbral, hashes_externos=hashes_externos
    )

    for fila in conservadas:
        destino = raiz_curado / fila["archivo"]
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raiz_crudo / fila["archivo"], destino)

    if directorio_ya_propio:
        _reconciliar_destino(raiz_curado, conservadas)

    _escribir_curado(conservadas, raiz_curado / NOMBRE_MANIFIESTO_CURADO)

    por_motivo: dict[str, int] = defaultdict(int)
    for fila in descartadas:
        por_motivo[fila["motivo"]] += 1
    por_clase: dict[str, int] = defaultdict(int)
    for fila in conservadas:
        por_clase[f"{fila['orden']}/{fila['familia'] or '_sin_familia'}"] += 1

    return {
        "entrada": len(filas),
        "conservadas": len(conservadas),
        "por_motivo": dict(por_motivo),
        "por_clase": dict(por_clase),
    }


def reporte_markdown(resumen: dict) -> str:
    entrada = resumen["entrada"]
    conservadas = resumen["conservadas"]
    factor = round(entrada / conservadas, 2) if conservadas else 0.0
    lineas = [
        "# Reporte de curación",
        "",
        f"- Imágenes de entrada: **{entrada}**",
        f"- Conservadas: **{conservadas}**",
        f"- Factor de curación real: **{factor}** "
        "(comparar con el 1.5 estimado en el censo y corregirlo si difiere).",
        "",
        "## Descartes por motivo",
        "",
        "| Motivo | Cantidad |",
        "| --- | ---: |",
    ]
    for motivo, cantidad in sorted(resumen["por_motivo"].items()):
        lineas.append(f"| {motivo} | {cantidad} |")

    lineas += ["", "## Imágenes conservadas por clase", "", "| Clase | Cantidad |", "| --- | ---: |"]
    for clase, cantidad in sorted(resumen["por_clase"].items()):
        lineas.append(f"| {clase} | {cantidad} |")
    return "\n".join(lineas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Curación del dataset descargado")
    parser.add_argument("--crudo", default="datos/crudo")
    parser.add_argument("--curado", default="datos/curado")
    parser.add_argument("--umbral", type=int, default=3)
    parser.add_argument(
        "--demo",
        default="",
        help="carpeta de imágenes de la demo, para no reutilizar sus fotos",
    )
    args = parser.parse_args()

    externos: set[str] = set()
    if args.demo:
        for ruta in Path(args.demo).rglob("*.jpg"):
            try:
                with Image.open(ruta) as img:
                    externos.add(imagenes.hash_perceptual(img.convert("RGB")))
            except Exception:
                continue
        print(f"{len(externos)} huellas externas cargadas de {args.demo}")

    resumen = curar(Path(args.crudo), Path(args.curado), umbral=args.umbral, hashes_externos=externos)
    Path("docs/reporte_curacion.md").write_text(reporte_markdown(resumen), encoding="utf-8")
    print(f"Curación: {resumen['conservadas']}/{resumen['entrada']} conservadas")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_curacion.py -v
```

Esperado: PASS, 20 pruebas.

- [ ] **Step 5: Curar el dataset real, excluyendo las fotos de la demo**

```powershell
.venv\Scripts\python -m pipeline.curacion --demo ..\insectos-demo\data
```

Esperado: `docs/reporte_curacion.md`. **Comparar el factor real con el 1.5 estimado en el censo**; si difiere mucho, actualizar `FACTOR_CURACION` en `pipeline/censo.py` y anotarlo en el reporte del censo.

- [ ] **Step 6: Commit**

```powershell
git add pipeline/curacion.py tests/test_curacion.py docs/reporte_curacion.md
git commit -m "feat: curacion con deduplicado perceptual indexado por bandas"
```

---

## Task 7: Particionado agrupado y regla de admisión

**Files:**

- Create: `pipeline/splits.py`
- Test: `tests/test_splits.py`

**Interfaces:**

- Consumes: `pipeline.ontologia.cargar_ontologia`, `Ontologia`, `PREFIJO_OTROS`; `pipeline.curacion.COLUMNAS_CURADO`
- Produces:
  - `PROPORCIONES: dict[str, float]` = `{"train": 0.70, "val": 0.15, "test": 0.15}`
  - `OBSERVADOR_DESCONOCIDO: str = "desconocido"` — placeholder que `pipeline.inat` asigna al observador cuando la observación no trae usuario registrado; no representa a una sola persona.
  - `asignar_grupos(filas: list[dict], *, proporciones: dict[str, float] = PROPORCIONES) -> dict[str, str]` (observador → split)
  - `aplicar_regla_admision(filas: list[dict], asignacion: dict[str, str], onto) -> tuple[list[dict], dict[str, str]]`
  - `particionar(filas: list[dict], onto) -> tuple[dict[str, list[dict]], dict]`
  - `reporte_markdown(resumen: dict) -> str`

**El punto crítico de todo el plan.** Si un observador aparece en train y en test, sus fotos —tomadas con la misma cámara, el mismo fondo y a menudo el mismo individuo— inflan la métrica y el sistema se derrumba en campo. El agrupamiento es por **observador**, que es más estricto que por observación y las subsume: todas las observaciones de una persona caen en el mismo split.

**Observadores únicos y clases de riesgo (hallazgo de revisión):** contar imágenes por split no basta para saber si una clase está bien evaluada — una familia puede superar el mínimo de imágenes de test y aun así provenir de un solo fotógrafo, lo que mide memorización de esa cámara y ese fondo, no reconocimiento real. `particionar` ahora también cuenta **observadores únicos** por clase y por split (recompuestos de la asignación real, no estimados), y `reporte_markdown` señala en prosa las clases cuyo test depende de un único fotógrafo. El reporte también declara cuántas imágenes cayeron bajo `OBSERVADOR_DESCONOCIDO` y en qué split: ese identificador agrupa observaciones anónimas de gente distinta (no es "una persona"), y su peso debe quedar visible para no confiar a ciegas en la partición si es una porción grande del total.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_splits.py`:

```python
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
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_splits.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'pipeline.splits'`.

- [ ] **Step 3: Implementar `pipeline/splits.py`**

```python
"""Particionado train/val/test agrupado por observador y regla de admisión.

Agrupar por observador es la defensa contra la fuga de datos: las fotos de una
misma persona comparten cámara, fondo y a menudo el mismo individuo. Si se
reparten entre train y test, la métrica sube y el sistema falla en campo.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from pipeline.curacion import COLUMNAS_CURADO
from pipeline.ontologia import PREFIJO_OTROS, Ontologia, cargar_ontologia

PROPORCIONES = {"train": 0.70, "val": 0.15, "test": 0.15}

# Placeholder que pipeline.inat asigna al campo `observador` cuando la
# observación de iNaturalist no trae usuario registrado (ver
# `Observacion.observador` en pipeline/inat.py). No representa a una persona:
# es un cajón donde caen observaciones anónimas de gente distinta. Se
# mantiene como un observador más para el agrupamiento (separarlas sin saber
# quién las tomó arriesgaría fuga si en realidad compartieran fotógrafo),
# pero su peso debe quedar visible en el reporte.
OBSERVADOR_DESCONOCIDO = "desconocido"


def asignar_grupos(
    filas: list[dict], *, proporciones: dict[str, float] = PROPORCIONES
) -> dict[str, str]:
    """Asigna cada observador a un split. Determinista y balanceado por tamaño."""
    tamanos: dict[str, int] = defaultdict(int)
    for fila in filas:
        tamanos[fila["observador"]] += 1

    total = sum(tamanos.values())
    cupos = {split: proporcion * total for split, proporcion in proporciones.items()}
    asignados: dict[str, int] = {split: 0 for split in proporciones}
    asignacion: dict[str, str] = {}

    # De mayor a menor, con el nombre como desempate: el resultado no depende
    # del orden en que llegaron las filas.
    for observador in sorted(tamanos, key=lambda o: (-tamanos[o], o)):
        elegido = max(cupos, key=lambda s: cupos[s] - asignados[s])
        asignacion[observador] = elegido
        asignados[elegido] += tamanos[observador]
    return asignacion


def aplicar_regla_admision(
    filas: list[dict], asignacion: dict[str, str], onto: Ontologia
) -> tuple[list[dict], dict[str, str]]:
    """Reetiqueta como `Otros_<Orden>` las familias que no llegan al umbral."""
    conteo: dict[tuple[str, str], int] = defaultdict(int)
    for fila in filas:
        if fila["familia"]:
            conteo[(fila["familia"], asignacion[fila["observador"]])] += 1

    decisiones: dict[str, str] = {}
    for familia in {f["familia"] for f in filas if f["familia"]}:
        suficiente = (
            conteo[(familia, "train")] >= onto.minimo_familia_train
            and conteo[(familia, "test")] >= onto.minimo_familia_test
        )
        decisiones[familia] = "admitida" if suficiente else "agrupada"

    salida = []
    for fila in filas:
        copia = dict(fila)
        if copia["familia"] and decisiones[copia["familia"]] == "agrupada":
            copia["familia"] = f"{PREFIJO_OTROS}{copia['orden']}"
        salida.append(copia)
    return salida, decisiones


def particionar(filas: list[dict], onto: Ontologia) -> tuple[dict[str, list[dict]], dict]:
    """Devuelve las tres particiones y el resumen de lo decidido."""
    asignacion = asignar_grupos(filas)
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

    resumen = {
        "total": len(filas),
        "por_split": {split: len(v) for split, v in particiones.items()},
        "decisiones": decisiones,
        "por_clase": por_clase,
        "anonimos_por_split": anonimos_por_split,
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
        "splits. Es la defensa contra la fuga de datos descrita en el diseño (§7).",
        "",
        "## Decisiones de admisión de familias",
        "",
        "| Familia | Decisión |",
        "| --- | --- |",
    ]
    for familia, decision in sorted(resumen["decisiones"].items()):
        lineas.append(f"| {familia} | {decision} |")

    agrupadas = [f for f, d in resumen["decisiones"].items() if d == "agrupada"]
    lineas += [
        "",
        (
            f"**{len(agrupadas)} familias no alcanzaron el umbral** y quedaron dentro de "
            f"`Otros_<Orden>`: {', '.join(sorted(agrupadas))}. Llevar esta lista a la "
            "Facultad: o se consiguen más imágenes para ellas, o se sustituyen por otras."
            if agrupadas
            else "Todas las familias alcanzaron el umbral."
        ),
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Particionado del dataset curado")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--curado", default="datos/curado")
    parser.add_argument("--destino", default="datos/splits")
    args = parser.parse_args()

    onto = cargar_ontologia(Path(args.ontologia))
    with (Path(args.curado) / "manifiesto_curado.csv").open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))

    particiones, resumen = particionar(filas, onto)
    escribir_particiones(particiones, Path(args.destino))
    Path("docs/reporte_splits.md").write_text(reporte_markdown(resumen), encoding="utf-8")
    print({k: len(v) for k, v in particiones.items()})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_splits.py -v
```

Esperado: PASS, 13 pruebas.

- [ ] **Step 5: Particionar el dataset real**

```powershell
.venv\Scripts\python -m pipeline.splits
```

Esperado: `datos/splits/{train,val,test}.csv` y `docs/reporte_splits.md`. **Leer la lista de familias agrupadas: es el insumo de la siguiente conversación con la Facultad.**

- [ ] **Step 6: Verificar a mano que no hay fuga**

```powershell
.venv\Scripts\python -c "import csv;g=lambda s:{r['observador'] for r in csv.DictReader(open(f'datos/splits/{s}.csv',encoding='utf-8'))};t,v,e=g('train'),g('val'),g('test');print('cruces:',len(t&v),len(t&e),len(v&e))"
```

Esperado: `cruces: 0 0 0`. Cualquier otro resultado detiene el plan hasta corregirlo.

- [ ] **Step 7: Commit**

```powershell
git add pipeline/splits.py tests/test_splits.py docs/reporte_splits.md
git commit -m "feat: particionado agrupado por observador y regla de admision"
```

---

## Task 8: Base de datos biológica — Excel a SQLite

**Files:**

- Create: `bd/esquema.sql`, `pipeline/bd.py`
- Test: `tests/test_bd.py`

**Interfaces:**

- Consumes: `pipeline.ontologia.cargar_ontologia`, `Ontologia`
- Produces:
  - `COLUMNAS_BD: tuple[str, ...]` — las 19 columnas del documento IF
  - `validar(df, onto) -> list[str]` (recibe un `pandas.DataFrame`; devuelve errores legibles, vacío si todo bien)
  - `importar(ruta_excel: Path, ruta_sqlite: Path, onto) -> tuple[int, list[str]]`

> **pandas se importa dentro de `importar()`, no a nivel de módulo.** El backend del Plan 03 importa `COLUMNAS_BD` de aquí y no debe arrastrar pandas a sus dependencias de despliegue.

Las 19 columnas, en orden, según `agro/reunion/5_Base_de_Datos_Estructura.md`: `ID`, `Archivo_imagen`, `Vistas_fotograficas`, `Orden`, `Familia`, `Nombre_cientifico`, `Nombre_comun`, `Cultivo_asociado`, `Tipo_de_dano`, `Hospedero`, `Localidad`, `Coordenadas`, `Fecha`, `Colector`, `Importancia_economica`, `Estado_biologico`, `Fuente`, `Verificado_por`, `Observaciones`.

**Escritura atómica y validación semántica (hallazgo de revisión):** `importar()` nunca escribe directamente sobre `ruta_sqlite` — arma la base completa en un archivo temporal junto al destino (mismo patrón que `escribir_manifiesto` en `pipeline/descarga.py`) y solo lo reemplaza con `os.replace` cuando `_construir_sqlite` terminó sin fallos; así un error a mitad de camino (disco lleno, E/S) deja el destino exactamente como estaba, sin excepción cruda. La validación de `Fecha` y `Coordenadas` dejó de ser solo sintáctica: además del formato `AAAA-MM-DD`, `Fecha` debe ser una fecha real de calendario (`datetime.date` la rechaza si no lo es, p. ej. `2026-02-30`), y `Coordenadas` debe caer dentro de rangos geográficos válidos (latitud entre -90 y 90, longitud entre -180 y 180).

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_bd.py`:

```python
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
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_bd.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'pipeline.bd'`.

- [ ] **Step 3: Crear `bd/esquema.sql`**

```sql
-- Base de datos biológica de insectos amazónicos.
-- Las 19 columnas provienen del documento "Proyecto Formativo IF", sección IX.
-- Se genera desde bd_insectos.xlsx con: python -m pipeline.bd

DROP TABLE IF EXISTS insectos;

CREATE TABLE insectos (
    ID                    TEXT PRIMARY KEY,
    Archivo_imagen        TEXT,
    Vistas_fotograficas   TEXT,
    Orden                 TEXT NOT NULL,
    Familia               TEXT,
    Nombre_cientifico     TEXT,
    Nombre_comun          TEXT,
    Cultivo_asociado      TEXT,
    Tipo_de_dano          TEXT,
    Hospedero             TEXT,
    Localidad             TEXT,
    Coordenadas           TEXT,
    Fecha                 TEXT,
    Colector              TEXT,
    Importancia_economica TEXT,
    Estado_biologico      TEXT,
    Fuente                TEXT,
    Verificado_por        TEXT,
    Observaciones         TEXT
);

CREATE INDEX idx_insectos_orden   ON insectos (Orden);
CREATE INDEX idx_insectos_familia ON insectos (Familia);
CREATE INDEX idx_insectos_cultivo ON insectos (Cultivo_asociado);
```

- [ ] **Step 4: Implementar `pipeline/bd.py`**

```python
"""Importación validada de la base de datos biológica: Excel a SQLite.

La valida contra la ontología para que Agronomía no pueda registrar un orden
o una familia que el sistema desconoce. Si hay un solo error, no se escribe
nada: es preferible una BD ausente a una BD silenciosamente inconsistente.

Ese mismo principio rige la escritura: `importar()` nunca toca el archivo de
destino directamente. Arma la base completa en un archivo temporal y solo
reemplaza el destino cuando la escritura terminó sin fallos, así que un
error a mitad de camino (disco lleno, E/S, lo que sea) deja el destino
exactamente como estaba, sin propagar una excepción cruda.
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sqlite3
from datetime import date
from pathlib import Path

from pipeline.ontologia import Ontologia, cargar_ontologia

# pandas se importa dentro de `importar()`, no aquí: el backend del Plan 03
# necesita COLUMNAS_BD y no debe arrastrar pandas al despliegue.

COLUMNAS_BD = (
    "ID",
    "Archivo_imagen",
    "Vistas_fotograficas",
    "Orden",
    "Familia",
    "Nombre_cientifico",
    "Nombre_comun",
    "Cultivo_asociado",
    "Tipo_de_dano",
    "Hospedero",
    "Localidad",
    "Coordenadas",
    "Fecha",
    "Colector",
    "Importancia_economica",
    "Estado_biologico",
    "Fuente",
    "Verificado_por",
    "Observaciones",
)

HOJA = "BD_Insectos"
PATRON_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PATRON_COORDENADAS = re.compile(r"^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$")
LATITUD_MINIMA, LATITUD_MAXIMA = -90.0, 90.0
LONGITUD_MINIMA, LONGITUD_MAXIMA = -180.0, 180.0


def _texto(valor) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return ""
    return str(valor).strip()


def validar(df, onto: Ontologia) -> list[str]:
    """Devuelve la lista de errores legibles. Vacía si el marco es válido."""
    errores: list[str] = []

    faltantes = [c for c in COLUMNAS_BD if c not in df.columns]
    if faltantes:
        return [f"faltan columnas obligatorias: {', '.join(faltantes)}"]

    ordenes = set(onto.nombres_ordenes())
    familias = set(onto.nombres_familias())
    vistos: set[str] = set()

    for posicion, registro in df.iterrows():
        etiqueta = f"fila {posicion + 2}"  # +2: encabezado y base 1 de Excel

        identificador = _texto(registro["ID"])
        if not identificador:
            errores.append(f"{etiqueta}: ID vacío")
        elif identificador in vistos:
            errores.append(f"{etiqueta}: ID duplicado {identificador}")
        else:
            vistos.add(identificador)

        orden = _texto(registro["Orden"])
        if not orden:
            errores.append(f"{etiqueta}: Orden vacío")
        elif orden not in ordenes:
            errores.append(f"{etiqueta}: Orden '{orden}' no existe en la ontología")

        familia = _texto(registro["Familia"])
        if familia:
            if familia not in familias:
                errores.append(f"{etiqueta}: Familia '{familia}' no existe en la ontología")
            elif orden in ordenes and onto.orden_de_familia(familia) != orden:
                errores.append(
                    f"{etiqueta}: Familia '{familia}' no pertenece al orden '{orden}'"
                )

        fecha = _texto(registro["Fecha"])
        if fecha:
            if not PATRON_FECHA.match(fecha):
                errores.append(f"{etiqueta}: Fecha '{fecha}' no tiene formato AAAA-MM-DD")
            else:
                anio, mes, dia = (int(parte) for parte in fecha.split("-"))
                try:
                    date(anio, mes, dia)
                except ValueError:
                    errores.append(
                        f"{etiqueta}: Fecha '{fecha}' no es una fecha real de colecta"
                    )

        coordenadas = _texto(registro["Coordenadas"])
        if coordenadas:
            coincidencia = PATRON_COORDENADAS.match(coordenadas)
            if not coincidencia:
                errores.append(
                    f"{etiqueta}: Coordenadas '{coordenadas}' no tienen formato 'lat, lon' decimal"
                )
            else:
                latitud, longitud = (float(g) for g in coincidencia.groups())
                if not (LATITUD_MINIMA <= latitud <= LATITUD_MAXIMA) or not (
                    LONGITUD_MINIMA <= longitud <= LONGITUD_MAXIMA
                ):
                    errores.append(
                        f"{etiqueta}: Coordenadas '{coordenadas}' fuera de rango "
                        f"(latitud entre {LATITUD_MINIMA:.0f} y {LATITUD_MAXIMA:.0f}, "
                        f"longitud entre {LONGITUD_MINIMA:.0f} y {LONGITUD_MAXIMA:.0f})"
                    )

    return errores


def _construir_sqlite(df, ruta_temporal: Path) -> None:
    """Crea el esquema y vuelca las filas de `df` en un archivo nuevo.

    `ruta_temporal` no es el destino final: `importar()` solo lo promueve a
    destino si esta función termina sin lanzar ninguna excepción. `DROP TABLE
    IF EXISTS` del esquema corre aquí, sobre el archivo temporal, así que
    nunca toca datos previos del destino.
    """
    esquema = (Path(__file__).resolve().parent.parent / "bd" / "esquema.sql").read_text(
        encoding="utf-8"
    )
    conexion = sqlite3.connect(ruta_temporal)
    try:
        conexion.executescript(esquema)
        conexion.executemany(
            f"INSERT INTO insectos ({', '.join(COLUMNAS_BD)}) "
            f"VALUES ({', '.join('?' * len(COLUMNAS_BD))})",
            [tuple(_texto(fila[c]) for c in COLUMNAS_BD) for _, fila in df.iterrows()],
        )
        conexion.commit()
    finally:
        conexion.close()


def importar(ruta_excel: Path, ruta_sqlite: Path, onto: Ontologia) -> tuple[int, list[str]]:
    """Valida el Excel y, si está limpio, lo vuelca a SQLite de forma atómica.

    Nunca escribe directamente sobre `ruta_sqlite`: construye la base en un
    archivo temporal junto a él (`_construir_sqlite`) y solo lo reemplaza,
    con `os.replace`, cuando esa escritura terminó sin errores. La conexión
    ya está cerrada para ese momento, así que el reemplazo funciona también
    en Windows. Si algo falla en cualquier punto, se borra el temporal y el
    destino queda exactamente como estaba (con los datos previos intactos si
    existían, o inexistente si no existía); el fallo se devuelve como error,
    nunca como excepción sin capturar.
    """
    import pandas as pd  # local: mantiene el módulo importable sin pandas

    df = pd.read_excel(ruta_excel, sheet_name=HOJA, dtype=str).fillna("")
    errores = validar(df, onto)
    if errores:
        return 0, errores

    ruta_sqlite = Path(ruta_sqlite)
    ruta_sqlite.parent.mkdir(parents=True, exist_ok=True)
    ruta_temporal = ruta_sqlite.with_name(f".{ruta_sqlite.name}.tmp-{os.getpid()}")
    ruta_temporal.unlink(missing_ok=True)  # restos de una corrida anterior interrumpida

    try:
        _construir_sqlite(df, ruta_temporal)
        os.replace(ruta_temporal, ruta_sqlite)
    except Exception as error:
        ruta_temporal.unlink(missing_ok=True)
        return 0, [f"no se pudo escribir la base de datos: {error}"]

    return len(df), []


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa la BD biológica de Excel a SQLite")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--excel", default="bd/bd_insectos.xlsx")
    parser.add_argument("--sqlite", default="bd/bd_insectos.sqlite")
    args = parser.parse_args()

    onto = cargar_ontologia(Path(args.ontologia))
    cantidad, errores = importar(Path(args.excel), Path(args.sqlite), onto)
    if errores:
        print(f"NO se importó nada. {len(errores)} errores:")
        for error in errores:
            print(f"  - {error}")
        raise SystemExit(1)
    print(f"{cantidad} registros importados en {args.sqlite}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_bd.py -v
```

Esperado: PASS, 20 pruebas.

- [ ] **Step 6: Copiar el Excel de la reunión e importarlo**

```powershell
copy "..\reunion\BD_Insectos_Amazonicos.xlsx" bd\bd_insectos.xlsx
.venv\Scripts\python -m pipeline.bd
```

Esperado: si las 5 filas de ejemplo del Excel usan órdenes o familias que no están en `clases.yaml`, el comando falla listando cada error. Eso es correcto: o se corrigen las filas, o se amplía la ontología. Resolverlo antes de seguir.

- [ ] **Step 7: Commit**

```powershell
git add bd/esquema.sql bd/bd_insectos.xlsx pipeline/bd.py tests/test_bd.py
git commit -m "feat: importacion validada de la base de datos biologica a sqlite"
```

---

## Task 9: Conjunto de prueba de campo

**Files:**

- Create: `pipeline/campo.py`
- Test: `tests/test_campo.py`

**Interfaces:**

- Consumes: `pipeline.ontologia.cargar_ontologia`, `Ontologia`; `pipeline.imagenes.hash_perceptual`, `distancia`, `bandas`; `pipeline.curacion.COLUMNAS_CURADO`
- Produces:
  - `EXTENSIONES: set[str]` = `{".jpg", ".jpeg", ".png", ".webp"}`
  - `SPLITS_DE_REFERENCIA: tuple[str, ...]` = `("train", "val", "test")` — los tres splits contra los que se verifica la fuga, no solo `train`.
  - `ingerir(raiz_campo: Path, onto) -> tuple[list[dict], list[str]]`
  - `ErrorReferencias` — falta alguno de los splits de referencia; ver `cargar_referencias`.
  - `cargar_referencias(directorio_splits: Path) -> dict[str, list[dict]]`
  - `detectar_colisiones(filas_campo: list[dict], filas_referencia: list[dict], *, umbral: int = 3, etiqueta: str = "entrenamiento") -> list[str]`
  - `main(argv: list[str] | None = None) -> int` — opción `--splits <directorio>` (train.csv, val.csv y test.csv, los tres obligatorios), no `--train <archivo>`: la comparación es contra los tres splits, no solo contra train.

**Por qué es una tarea aparte:** el conjunto de campo es la única medición honesta del sistema (§7.4 y §8 del diseño). Se construye a partir de las fotos que aporte la Facultad, colocadas a mano en `datos/campo_crudo/<Orden>/<Familia>/`, y **nunca** entra a entrenamiento. La detección de colisiones existe porque si alguien sube a la Facultad una foto que también está en iNaturalist, el test de campo dejaría de ser independiente.

**Ninguna extensión no reconocida desaparece en silencio (hallazgo de revisión):** `ingerir` acepta `.jpg`, `.jpeg`, `.png` y `.webp` (Pillow decodifica WEBP de forma nativa, sin plugins). Un archivo con cualquier otra extensión — típicamente `.heic` de iPhone — se reporta como **error explícito** en vez de omitirse calladamente: el conjunto de campo es la única medición honesta del sistema, y perder fotos sin que nadie se entere invalidaría esa medición sin avisar. Solo la basura real del sistema operativo (`Thumbs.db`, `.DS_Store`, archivos ocultos) se ignora sin generar error, porque nadie la "entregó" a propósito.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_campo.py`:

```python
from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.campo import detectar_colisiones, ingerir
from pipeline.ontologia import cargar_ontologia


def escribir_imagen(raiz: Path, relativo: str, semilla: int, lado: int = 300, formato: str = "JPEG"):
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    destino = raiz / relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(base).resize((lado, lado), Image.BICUBIC).save(destino, formato, quality=90)


def test_ingerir_lee_orden_y_familia_de_la_ruta(tmp_path: Path, ruta_ontologia: Path):
    # La raíz de campo vive en su propia subcarpeta, separada de donde el
    # fixture `ruta_ontologia` escribe clases.yaml: si compartieran tmp_path,
    # `ingerir` (que ahora reporta cualquier archivo que no encaje, en vez de
    # ignorarlo en silencio) marcaría clases.yaml como un archivo fuera de la
    # estructura esperada. No es una entrega de la Facultad; no debe mezclarse
    # con la carpeta que sí se recorre.
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Coleoptera/Curculionidae/foto1.jpg", 1)
    filas, errores = ingerir(raiz, onto)
    assert errores == []
    assert filas[0]["orden"] == "Coleoptera"
    assert filas[0]["familia"] == "Curculionidae"
    assert filas[0]["fuente"] == "campo"
    assert filas[0]["hash"]


def test_ingerir_acepta_carpeta_sin_familia(tmp_path: Path, ruta_ontologia: Path):
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Coleoptera/_sin_familia/foto1.jpg", 2)
    filas, errores = ingerir(raiz, onto)
    assert errores == []
    assert filas[0]["familia"] == ""


def test_ingerir_reporta_orden_desconocido(tmp_path: Path, ruta_ontologia: Path):
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Inventado/FamY/foto1.jpg", 3)
    filas, errores = ingerir(raiz, onto)
    assert filas == []
    assert any("Inventado" in e for e in errores)


def test_ingerir_reporta_familia_de_otro_orden(tmp_path: Path, ruta_ontologia: Path):
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Odonata/Curculionidae/foto1.jpg", 4)
    filas, errores = ingerir(raiz, onto)
    assert filas == []
    assert any("Curculionidae" in e for e in errores)


def test_ingerir_reporta_archivo_ilegible(tmp_path: Path, ruta_ontologia: Path):
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    destino = raiz / "Coleoptera" / "Curculionidae" / "roto.jpg"
    destino.parent.mkdir(parents=True)
    destino.write_bytes(b"basura")
    filas, errores = ingerir(raiz, onto)
    assert filas == []
    assert any("roto.jpg" in e for e in errores)


def test_ingerir_reporta_extension_no_reconocida(tmp_path: Path, ruta_ontologia: Path):
    """Una extensión que no se reconoce debe reportarse, no desaparecer.

    Fotos de campo tomadas con celular llegan a menudo en formatos como
    .heic (iPhone): si el archivo se descarta en silencio, alguien puede
    entregar 200 fotos y ver un conteo final que no las incluye todas, sin
    ninguna pista de que faltan.
    """
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    destino = raiz / "Coleoptera" / "Curculionidae" / "foto1.heic"
    destino.parent.mkdir(parents=True)
    destino.write_bytes(b"contenido de una foto heic simulada, no se llega a abrir")
    filas, errores = ingerir(raiz, onto)
    assert filas == []
    assert any("foto1.heic" in e and ".heic" in e for e in errores)


def test_ingerir_ignora_archivos_de_metadatos_del_sistema(tmp_path: Path, ruta_ontologia: Path):
    """Thumbs.db, .DS_Store y demás basura de sistema no son entregas: se
    ignoran sin generar error, a diferencia de un archivo con extensión
    desconocida que sí fue puesto ahí por una persona."""
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Coleoptera/Curculionidae/foto1.jpg", 6)
    carpeta = raiz / "Coleoptera" / "Curculionidae"
    (carpeta / "Thumbs.db").write_bytes(b"basura de windows")
    (carpeta / ".DS_Store").write_bytes(b"basura de macos")
    filas, errores = ingerir(raiz, onto)
    assert errores == []
    assert len(filas) == 1


def test_ingerir_acepta_webp(tmp_path: Path, ruta_ontologia: Path):
    """WEBP se acepta porque Pillow lo decodifica de forma nativa."""
    raiz = tmp_path / "campo"
    onto = cargar_ontologia(ruta_ontologia)
    escribir_imagen(raiz, "Coleoptera/Curculionidae/foto1.webp", 7, formato="WEBP")
    filas, errores = ingerir(raiz, onto)
    assert errores == []
    assert filas[0]["hash"]


def test_detecta_colision_con_entrenamiento():
    campo = [{"archivo": "c1.jpg", "hash": "ffff0000ffff0000"}]
    train = [{"archivo": "t1.jpg", "hash": "ffff0000ffff0000"}]
    colisiones = detectar_colisiones(campo, train)
    assert len(colisiones) == 1
    assert "c1.jpg" in colisiones[0]


def test_sin_colision_cuando_las_imagenes_difieren():
    campo = [{"archivo": "c1.jpg", "hash": "ffff0000ffff0000"}]
    train = [{"archivo": "t1.jpg", "hash": "0000ffff0000ffff"}]
    assert detectar_colisiones(campo, train) == []
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_campo.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'pipeline.campo'`.

- [ ] **Step 3: Implementar `pipeline/campo.py`**

```python
"""Ingesta del conjunto de prueba de campo.

Estas fotos son la única medición honesta del sistema: nunca entran a
entrenamiento ni a validación. Se colocan a mano en
`datos/campo_crudo/<Orden>/<Familia>/` y este módulo las valida contra la
ontología y verifica que ninguna coincida con una imagen de entrenamiento.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

from pipeline import imagenes
from pipeline.curacion import COLUMNAS_CURADO
from pipeline.ontologia import Ontologia, cargar_ontologia

SIN_FAMILIA = "_sin_familia"

# Los tres splits contra los que hay que comprobar toda foto de campo. El
# diseño (§7) dice que estas fotos "nunca entran a entrenamiento ni a
# validación"; comprobar solo contra `train` dejaba pasar dos tercios del
# riesgo, y una foto de campo que ya está en validación invalida por igual la
# comparación entre la métrica de validación y la de campo, que es
# precisamente el resultado que el informe debe explicar.
SPLITS_DE_REFERENCIA = ("train", "val", "test")

# Códigos de salida del módulo, pensados para encadenar `campo.py` en un
# script: cualquier valor distinto de cero significa que el conjunto de campo
# resultante no es de fiar, o directamente no se produjo.
SALIDA_OK = 0
SALIDA_COLISIONES = 1  # hay fotos de campo que también están en los splits
SALIDA_RECHAZOS = 2  # se entregaron archivos que no pudieron ingerirse
SALIDA_FALTA_REFERENCIA = 3  # no se pudo verificar la fuga: no se escribe nada


class ErrorReferencias(Exception):
    """Faltan los splits contra los que verificar la fuga."""
# WEBP se acepta porque Pillow lo decodifica de forma nativa, sin depender de
# ningún complemento adicional. HEIC (el formato por defecto de iPhone desde
# iOS 11) queda deliberadamente fuera: Pillow no lo lee sin un plugin externo,
# y no se añaden dependencias nuevas en esta ronda. Una foto en ese formato
# debe convertirse antes de entregarse, y por eso produce un error explícito
# más abajo en vez de desaparecer en silencio.
EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp"}

# Archivos que el propio sistema operativo siembra en las carpetas (miniaturas
# de Windows, metadatos de macOS) sin que nadie los haya "entregado": no son
# fotos y se ignoran sin generar error. Los ocultos (que empiezan por punto,
# como .DS_Store o un .gitkeep de control de versiones) quedan cubiertos por
# la segunda condición de `_es_metadato_de_sistema`.
NOMBRES_IGNORADOS = {"thumbs.db", ".ds_store"}


def _es_metadato_de_sistema(ruta: Path) -> bool:
    """True si el archivo es basura del sistema operativo, no una entrega."""
    return ruta.name.lower() in NOMBRES_IGNORADOS or ruta.name.startswith(".")


def ingerir(raiz_campo: Path, onto: Ontologia) -> tuple[list[dict], list[str]]:
    """Recorre las carpetas y produce filas de manifiesto, o errores.

    Ningún archivo entregado desaparece sin dejar constancia: una extensión
    no reconocida (p. ej. .heic de iPhone o .webp mal escrito) se reporta
    como error explícito en vez de omitirse en silencio, porque el conjunto
    de campo es la única medición honesta del sistema y perder fotos sin
    que nadie se entere invalidaría esa medición sin avisar.
    """
    raiz_campo = Path(raiz_campo)
    ordenes = set(onto.nombres_ordenes())
    familias = set(onto.nombres_familias())
    filas: list[dict] = []
    errores: list[str] = []

    for ruta in sorted(raiz_campo.rglob("*")):
        if not ruta.is_file() or _es_metadato_de_sistema(ruta):
            continue
        relativo = ruta.relative_to(raiz_campo)
        if len(relativo.parts) != 3:
            errores.append(
                f"{relativo}: se esperaba la estructura <Orden>/<Familia>/<archivo>"
            )
            continue

        if ruta.suffix.lower() not in EXTENSIONES:
            formatos = ", ".join(sorted(EXTENSIONES))
            errores.append(
                f"{relativo}: extensión '{ruta.suffix}' no reconocida; "
                f"convertir a uno de estos formatos antes de ingerir: {formatos}"
            )
            continue

        orden, carpeta_familia, _ = relativo.parts
        if orden not in ordenes:
            errores.append(f"{relativo}: orden '{orden}' no existe en la ontología")
            continue

        familia = "" if carpeta_familia == SIN_FAMILIA else carpeta_familia
        if familia:
            if familia not in familias:
                errores.append(f"{relativo}: familia '{familia}' no existe en la ontología")
                continue
            if onto.orden_de_familia(familia) != orden:
                errores.append(f"{relativo}: familia '{familia}' no pertenece a '{orden}'")
                continue

        try:
            with Image.open(ruta) as img:
                huella = imagenes.hash_perceptual(img.convert("RGB"))
        except Exception:
            errores.append(f"{relativo}: archivo ilegible")
            continue

        fila = {c: "" for c in COLUMNAS_CURADO}
        fila.update(
            archivo=str(relativo).replace("\\", "/"),
            obs_id="",
            observador="campo",
            orden=orden,
            familia=familia,
            fuente="campo",
            hash=huella,
        )
        filas.append(fila)

    return filas, errores


def cargar_referencias(directorio_splits: Path) -> dict[str, list[dict]]:
    """Lee los tres splits contra los que se verifica la fuga.

    Si falta alguno lanza `ErrorReferencias` en vez de devolver lo que haya.
    La verificación anti-fuga es el único guardián del conjunto de campo -"la
    única medición honesta del sistema", según el diseño-, así que no puede
    fallar en abierto: un `--splits` con un typo, o correr este módulo antes
    que `splits.py`, tiene que ser un error ruidoso y no una corrida que
    informa éxito sin haber comprobado nada.
    """
    directorio_splits = Path(directorio_splits)
    faltantes = [
        split
        for split in SPLITS_DE_REFERENCIA
        if not (directorio_splits / f"{split}.csv").is_file()
    ]
    if faltantes:
        nombres = ", ".join(f"{s}.csv" for s in faltantes)
        raise ErrorReferencias(
            f"no se puede verificar la fuga: falta(n) {nombres} en {directorio_splits}. "
            "Ejecutar primero pipeline/splits.py, o corregir --splits."
        )

    referencias: dict[str, list[dict]] = {}
    for split in SPLITS_DE_REFERENCIA:
        with (directorio_splits / f"{split}.csv").open(encoding="utf-8", newline="") as f:
            referencias[split] = list(csv.DictReader(f))
    return referencias


def detectar_colisiones(
    filas_campo: list[dict],
    filas_referencia: list[dict],
    *,
    umbral: int = 3,
    etiqueta: str = "entrenamiento",
) -> list[str]:
    """Avisa si una foto de campo coincide con una del split de referencia."""
    indice: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for fila in filas_referencia:
        huella = fila.get("hash", "")
        if huella:
            for banda in imagenes.bandas(huella):
                indice[banda].append((huella, fila["archivo"]))

    colisiones: list[str] = []
    for fila in filas_campo:
        huella = fila.get("hash", "")
        if not huella:
            continue
        candidatas = {c for banda in imagenes.bandas(huella) for c in indice[banda]}
        for otra, archivo in candidatas:
            if imagenes.distancia(huella, otra) <= umbral:
                colisiones.append(
                    f"{fila['archivo']} coincide con la imagen de {etiqueta} {archivo}"
                )
                break
    return colisiones


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada. Devuelve el código de salida (ver constantes `SALIDA_*`)."""
    parser = argparse.ArgumentParser(description="Ingesta del conjunto de prueba de campo")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--campo", default="datos/campo_crudo")
    parser.add_argument(
        "--splits",
        default="datos/splits",
        help="directorio con train.csv, val.csv y test.csv; los tres son obligatorios",
    )
    parser.add_argument("--salida", default=None, help="por defecto <splits>/campo.csv")
    args = parser.parse_args(argv)

    onto = cargar_ontologia(Path(args.ontologia))
    filas, errores = ingerir(Path(args.campo), onto)
    for error in errores:
        print(f"  ! {error}")

    # La verificación va ANTES de escribir nada: si no se puede comprobar la
    # fuga, no se produce un conjunto de campo que alguien pueda usar creyendo
    # que fue verificado.
    try:
        referencias = cargar_referencias(Path(args.splits))
    except ErrorReferencias as error:
        print(f"  !! ERROR: {error}")
        print("No se escribió campo.csv.")
        return SALIDA_FALTA_REFERENCIA

    colisiones: list[str] = []
    for split, filas_split in referencias.items():
        colisiones += detectar_colisiones(filas, filas_split, etiqueta=split)
    for colision in colisiones:
        print(f"  !! COLISIÓN: {colision}")
    if colisiones:
        print(
            f"{len(colisiones)} coincidencias entre fotos de campo y los splits "
            f"({', '.join(SPLITS_DE_REFERENCIA)}). Quitarlas antes de evaluar: "
            "invalidan la medición."
        )

    salida = Path(args.salida) if args.salida else Path(args.splits) / "campo.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"{len(filas)} fotos de campo en {salida} ({len(errores)} descartadas)")

    # Las colisiones pesan más que los rechazos: un rechazo deja fotos fuera,
    # una colisión contamina las que sí entraron.
    if colisiones:
        return SALIDA_COLISIONES
    if errores:
        return SALIDA_RECHAZOS
    return SALIDA_OK


if __name__ == "__main__":
    sys.exit(main())
```

**Por qué la verificación no puede fallar en abierto:** la versión original de este bloque tenía `if ruta_train.exists(): ...` sin `else`. Con esa forma, un `--train` con un typo -o correr `campo.py` antes que `splits.py`- hacía que `ruta_train.exists()` fuera `False`, el bloque completo se saltara en silencio, y el programa igual imprimiera `"N fotos de campo en ... (0 descartadas)"` y terminara con código `0`: éxito, sin haber comparado una sola imagen contra entrenamiento. Es exactamente el defecto que esta tarea existe para evitar (el conjunto de campo es "la única medición honesta del sistema"), y quien reimplantara este bloque tal cual lo reintroducía. La versión real (`cargar_referencias` + `try/except ErrorReferencias`) falla con `SALIDA_FALTA_REFERENCIA` y no escribe `campo.csv` si falta cualquiera de los tres splits, en vez de continuar como si la comprobación hubiera pasado.

- [ ] **Step 4: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_campo.py -v
```

Esperado: PASS, 10 pruebas.

- [ ] **Step 5: Correr la suite completa**

```powershell
.venv\Scripts\python -m pytest -v
```

Esperado: PASS en las 129 pruebas de las nueve tareas.

- [ ] **Step 6: Commit**

```powershell
git add pipeline/campo.py tests/test_campo.py
git commit -m "feat: ingesta del conjunto de prueba de campo con deteccion de colisiones"
```

---

## Estado al terminar el plan

Cuando las nueve tareas estén cerradas, el repositorio produce, de forma reproducible y desde una sola línea de comandos por etapa:

- `docs/censo_disponibilidad.md` — la tabla con la que la Facultad decide las clases.
- `datos/crudo/manifiesto.csv` — cada imagen con su observación, observador y licencia.
- `datos/curado/manifiesto_curado.csv` + `docs/reporte_curacion.md`.
- `datos/splits/{train,val,test}.csv` + `docs/reporte_splits.md` — sin fugas, con la regla de admisión aplicada.
- `datos/splits/campo.csv` — el conjunto de evaluación independiente.
- `bd/bd_insectos.sqlite` — la base biológica validada contra la ontología.

Eso es exactamente lo que consume el **Plan 02 (Modelo)**: `train.csv` y `val.csv` para entrenar, `test.csv` y `campo.csv` para evaluar, `clases.yaml` para los índices y la matriz de enmascaramiento.
