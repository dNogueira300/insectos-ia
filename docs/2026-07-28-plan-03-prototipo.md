# Plan 03 — Prototipo web (Semanas 12–14)

> **Para trabajadores agénticos:** SUB-SKILL REQUERIDA: usar `superpowers:subagent-driven-development` (recomendado) o `superpowers:executing-plans` para implementar este plan tarea por tarea. Los pasos usan sintaxis de casilla (`- [ ]`) para seguimiento.

**Goal:** Un prototipo web donde alguien sube la foto de un insecto y obtiene el orden, la familia y la ficha biológica asociada, con la incertidumbre expresada honestamente.

**Architecture:** Backend FastAPI que carga `insectos.onnx` con onnxruntime y reutiliza `pipeline/inferencia.py` para el enmascaramiento jerárquico. Sin PyTorch en el despliegue. El preprocesamiento se replica en Pillow + numpy y se verifica contra torchvision con una prueba de paridad. Frontend React + Vite que consume cuatro endpoints. La ficha biológica sale de `bd/bd_insectos.sqlite` **después** de la predicción: el modelo dice qué es, la base de datos dice qué significa.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, onnxruntime, numpy, Pillow, pytest + httpx. Node 24, React 19, Vite, Vitest + Testing Library.

**Depende de:** Planes 01 y 02 completos. Consume `modelo/<corrida>/insectos.onnx`, `modelo/<corrida>/etiquetas.json`, `bd/bd_insectos.sqlite` y `pipeline/inferencia.py`.

## Global Constraints

Aplican las de los planes anteriores, más:

- **El backend no importa torch ni el pipeline de datos.** Sus dependencias son: fastapi, uvicorn, onnxruntime, numpy, pillow, pyyaml, python-multipart. Una prueba lo verifica.
- **Interfaz en español**, incluidos mensajes de error visibles.
- **Ninguna prueba del backend carga el modelo real.** Se usa un ONNX diminuto generado en el momento, o un servicio falso.
- **El frontend nunca decide taxonomía.** No replica umbrales ni la matriz de pertenencia: solo muestra lo que el backend responde. Si el backend dice `familia_incierta: true`, el frontend lo comunica.
- **Toda respuesta de la API usa nombres en español** (`orden`, `familia`, `confianza_orden`, …), consistentes con `pipeline.inferencia.Prediccion`.

## Adenda 2026-09-23: el modelo vigente es la v4 (288 px)

El plan se escribió pensando en un modelo a 224 px guardado en `modelo/insectos.onnx`. El Plan 02 terminó con cuatro corridas, y la vigente es `v4_convnext_t_288`: ConvNeXt-Tiny a **288 px**, guardada en `modelo/v4_convnext_t_288/`. Cambios respecto de la versión original:

- **La resolución sale del ONNX, no de una constante.** El exportador fija alto y ancho y deja libre solo el lote (`imagen: [lote, 3, 288, 288]`). El servicio lee `lado` de ahí y prepara la foto a ese tamaño. Con otra corrida no hay que tocar código, y el backend no puede preprocesar a un tamaño distinto del de entrenamiento.
- **El lado corto se calcula como en el pipeline:** `round(lado / PROPORCION_RECORTE)`, con `PROPORCION_RECORTE = 224/256`. Da 256 para 224 y 329 para 288. Una prueba verifica que la proporción coincide con `pipeline.datos_torch`, y la paridad se prueba a 224 y a 288.
- **El modelo se busca en `modelo/<corrida>/`.** `app_produccion` usa `CORRIDA_VIGENTE = "v4_convnext_t_288"`, y la variable de entorno `MODELO_DIR` puede apuntar a otra carpeta. `iniciar.bat` fija la misma carpeta.
- **`/salud` informa también `lado`**, para ver desde la interfaz con qué resolución se está sirviendo.
- **Umbral:** `UMBRAL_FAMILIA` ya vale 0.7. El servicio lo importa de `pipeline.inferencia`, sin copiarlo.

## Estructura de archivos

```
insectos-ia/
├─ backend/
│   requirements.txt       T1  dependencias mínimas de despliegue
│   preproceso.py          T1  PIL + numpy, paridad con torchvision
│   servicio.py            T2  carga ONNX, predice, aplica enmascaramiento
│   fichas.py              T3  consultas a bd_insectos.sqlite
│   app.py                 T4  FastAPI: /salud /clases /predecir /taxon
├─ frontend/
│   package.json           T5
│   vite.config.js         T5
│   src/
│     api.js               T5  cliente HTTP
│     App.jsx              T6  composición de la pantalla
│     componentes/
│       SubirFoto.jsx      T6  selección y previsualización
│       Resultado.jsx      T6  orden, familia, confianzas, incertidumbre
│       Ficha.jsx          T7  datos biológicos de la BD
│       Explorador.jsx     T7  navegación de la base de datos
│     estilos.css          T6
│   pruebas/
│     api.test.js          T5
│     Resultado.test.jsx   T6
│     Ficha.test.jsx       T7
├─ tests/
│   test_preproceso.py     T1
│   test_servicio.py       T2
│   test_fichas.py         T3
│   test_app.py            T4
└─ iniciar.bat             T8  arranque de un clic
```

---

## Task 1: Preprocesamiento con paridad verificada

**Files:**
- Create: `backend/__init__.py`, `backend/preproceso.py`, `backend/requirements.txt`
- Test: `tests/test_preproceso.py`

**Interfaces:**
- Consumes: nada
- Produces:
  - `LADO: int = 224`, `PROPORCION_RECORTE: float = 224 / 256`, `MEDIA`, `DESVIACION`
  - `lado_redimension(lado: int) -> int` — lado corto antes del recorte: 256 para 224, 329 para 288
  - `redimensionar_lado_corto(img: Image.Image, corto: int) -> Image.Image`
  - `recortar_centro(img: Image.Image, lado: int = LADO) -> Image.Image`
  - `preparar(img: Image.Image, lado: int = LADO) -> np.ndarray` — devuelve `(1, 3, lado, lado)` float32
  - `desde_bytes(datos: bytes, lado: int = LADO) -> np.ndarray`

**El error clásico que esta tarea previene.** Si el preprocesamiento del backend difiere del de evaluación aunque sea un poco —otro método de interpolación, redondeo distinto en el recorte, normalización omitida— el modelo desplegado da resultados peores que los del informe y nadie entiende por qué. La prueba de paridad compara píxel a píxel contra `transformaciones_evaluacion()` del Plan 02. Como ambas rutas pasan por Pillow, la coincidencia debe ser prácticamente exacta.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_preproceso.py`:

```python
import io

import numpy as np
import pytest
from PIL import Image

from backend.preproceso import (
    LADO,
    PROPORCION_RECORTE,
    desde_bytes,
    lado_redimension,
    preparar,
    recortar_centro,
    redimensionar_lado_corto,
)


def imagen(ancho=400, alto=300, semilla=1):
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(12, 16, 3), dtype=np.uint8)
    return Image.fromarray(base).resize((ancho, alto), Image.BICUBIC)


def test_redimensionar_lleva_el_lado_corto_al_objetivo():
    salida = redimensionar_lado_corto(imagen(400, 300), 256)
    assert min(salida.size) == 256


def test_redimensionar_conserva_la_proporcion():
    entrada = imagen(400, 300)
    salida = redimensionar_lado_corto(entrada, 256)
    proporcion_entrada = entrada.width / entrada.height
    proporcion_salida = salida.width / salida.height
    assert proporcion_salida == pytest.approx(proporcion_entrada, abs=0.01)


def test_redimensionar_funciona_con_imagen_vertical():
    salida = redimensionar_lado_corto(imagen(300, 500), 256)
    assert salida.width == 256


def test_recortar_centro_da_el_lado_pedido():
    assert recortar_centro(imagen(400, 300), 224).size == (224, 224)


def test_lado_redimension_da_256_para_224_y_329_para_288():
    assert lado_redimension(224) == 256
    assert lado_redimension(288) == 329


def test_preparar_devuelve_la_forma_del_modelo():
    tensor = preparar(imagen())
    assert tensor.shape == (1, 3, LADO, LADO)
    assert tensor.dtype == np.float32


def test_preparar_acepta_otra_resolucion():
    assert preparar(imagen(), lado=288).shape == (1, 3, 288, 288)


def test_preparar_normaliza_fuera_del_rango_cero_uno():
    tensor = preparar(imagen())
    assert tensor.min() < 0.0


def test_preparar_convierte_escala_de_grises_a_tres_canales():
    tensor = preparar(Image.new("L", (400, 300), color=120))
    assert tensor.shape == (1, 3, LADO, LADO)


def test_desde_bytes_acepta_un_jpeg():
    buffer = io.BytesIO()
    imagen().save(buffer, "JPEG")
    assert desde_bytes(buffer.getvalue()).shape == (1, 3, LADO, LADO)


def test_desde_bytes_respeta_la_resolucion_pedida():
    buffer = io.BytesIO()
    imagen().save(buffer, "JPEG")
    assert desde_bytes(buffer.getvalue(), lado=288).shape == (1, 3, 288, 288)


def test_desde_bytes_rechaza_contenido_invalido():
    with pytest.raises(ValueError):
        desde_bytes(b"esto no es una imagen")


def test_la_proporcion_de_recorte_es_la_del_pipeline():
    pytest.importorskip("torch")
    from pipeline import datos_torch

    assert PROPORCION_RECORTE == datos_torch.PROPORCION_RECORTE


@pytest.mark.parametrize("lado", [224, 288])
def test_paridad_con_la_transformacion_de_evaluacion(lado):
    """El backend debe preprocesar exactamente igual que la evaluación."""
    pytest.importorskip("torch")
    from pipeline.datos_torch import transformaciones_evaluacion

    entrada = imagen(500, 380, semilla=7)
    del_backend = preparar(entrada, lado=lado)[0]
    del_pipeline = transformaciones_evaluacion(lado)(entrada).numpy()

    assert del_backend.shape == del_pipeline.shape
    assert np.abs(del_backend - del_pipeline).max() < 1e-5


@pytest.mark.parametrize("lado", [224, 288])
def test_paridad_tambien_en_imagen_vertical(lado):
    pytest.importorskip("torch")
    from pipeline.datos_torch import transformaciones_evaluacion

    entrada = imagen(280, 640, semilla=9)
    diferencia = np.abs(
        preparar(entrada, lado=lado)[0] - transformaciones_evaluacion(lado)(entrada).numpy()
    ).max()
    assert diferencia < 1e-5


def test_el_backend_no_importa_torch():
    """El despliegue no debe arrastrar PyTorch."""
    import backend.preproceso as modulo

    fuente = modulo.__file__
    with open(fuente, encoding="utf-8") as f:
        texto = f.read()
    assert "import torch" not in texto
    assert "torchvision" not in texto
```

- [ ] **Step 2: Crear `backend/requirements.txt`**

```text
fastapi>=0.115
uvicorn[standard]>=0.32
onnxruntime>=1.20
numpy>=2.1
pillow>=11.0
pyyaml>=6.0
python-multipart>=0.0.20
```

Instalar:

```powershell
.venv\Scripts\python -m pip install -r backend\requirements.txt
```

- [ ] **Step 3: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_preproceso.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'backend'`.

- [ ] **Step 4: Implementar `backend/preproceso.py`** (y `backend/__init__.py` vacío)

```python
"""Preprocesamiento de imágenes para inferencia.

Replica exactamente `transformaciones_evaluacion(lado)` del pipeline de
entrenamiento: redimensiona el lado corto a `lado / PROPORCION_RECORTE`,
recorta el centro a `lado`, escala a [0,1] y normaliza con las estadísticas
de ImageNet. Usa Pillow, igual que torchvision, para que la coincidencia sea
exacta y no aproximada. El `lado` lo decide el modelo (ver `servicio.py`).
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

LADO = 224
# La misma proporción que `pipeline.datos_torch`: 224 → 256, 288 → 329.
PROPORCION_RECORTE = 224 / 256
MEDIA = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
DESVIACION = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)


def lado_redimension(lado: int) -> int:
    """Lado corto al que se redimensiona antes del recorte central."""
    return round(lado / PROPORCION_RECORTE)


def redimensionar_lado_corto(img: Image.Image, corto: int) -> Image.Image:
    """Lleva el lado corto a `corto` conservando la proporción.

    Reproduce el cálculo de torchvision.transforms.Resize con un entero:
    el lado largo se trunca, no se redondea.
    """
    ancho, alto = img.size
    if min(ancho, alto) == corto:
        return img
    if ancho < alto:
        nuevo = (corto, int(corto * alto / ancho))
    else:
        nuevo = (int(corto * ancho / alto), corto)
    return img.resize(nuevo, Image.BILINEAR)


def recortar_centro(img: Image.Image, lado: int = LADO) -> Image.Image:
    ancho, alto = img.size
    izquierda = int(round((ancho - lado) / 2.0))
    arriba = int(round((alto - lado) / 2.0))
    return img.crop((izquierda, arriba, izquierda + lado, arriba + lado))


def preparar(img: Image.Image, lado: int = LADO) -> np.ndarray:
    """Imagen PIL → tensor (1, 3, lado, lado) listo para onnxruntime."""
    img = recortar_centro(
        redimensionar_lado_corto(img.convert("RGB"), lado_redimension(lado)), lado
    )
    arreglo = np.asarray(img, dtype=np.float32) / 255.0   # alto, ancho, canal
    arreglo = arreglo.transpose(2, 0, 1)                  # canal, alto, ancho
    arreglo = (arreglo - MEDIA) / DESVIACION
    return arreglo[np.newaxis, ...].astype(np.float32)


def desde_bytes(datos: bytes, lado: int = LADO) -> np.ndarray:
    try:
        with Image.open(io.BytesIO(datos)) as img:
            return preparar(img, lado)
    except Exception as error:
        raise ValueError("el archivo no es una imagen válida") from error
```

- [ ] **Step 5: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_preproceso.py -v
```

Esperado: PASS, 18 pruebas. Si las de paridad fallan por más de `1e-5`, el problema está en el cálculo del redimensionado — comparar `redimensionar_lado_corto(img, lado_redimension(lado)).size` contra `transforms.Resize(lado_redimension(lado))(img).size` antes de tocar nada más.

- [ ] **Step 6: Commit**

```powershell
git add backend/__init__.py backend/preproceso.py backend/requirements.txt tests/test_preproceso.py
git commit -m "feat: preprocesamiento del backend con paridad verificada contra torchvision"
```

---

## Task 2: Servicio de inferencia

**Files:**
- Create: `backend/servicio.py`
- Test: `tests/test_servicio.py`

**Interfaces:**
- Consumes: `backend.preproceso.desde_bytes`; `pipeline.inferencia.predecir`, `Prediccion`, `UMBRAL_FAMILIA`; `pipeline.etiquetas.cargar_espacio`, `EspacioEtiquetas`
- Produces:
  - `class ServicioInsectos` — `__init__(self, ruta_onnx: Path, ruta_etiquetas: Path, *, umbral: float = UMBRAL_FAMILIA)`, atributo `lado: int` leído de la entrada del ONNX, `predecir_bytes(self, datos: bytes) -> Prediccion`, `clases(self) -> dict`, `version(self) -> dict` (incluye `lado`)
  - `class ErrorImagen(ValueError)`

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_servicio.py`:

```python
import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from backend.servicio import ErrorImagen, ServicioInsectos
from pipeline.etiquetas import EspacioEtiquetas

ESPACIO = EspacioEtiquetas(
    ordenes=("OrdenA", "OrdenB"),
    familias=("FamA1", "FamA2", "FamB1"),
    matriz=((True, False), (True, False), (False, True)),
)


def exportar_diminuto(carpeta: Path, lado: int) -> tuple[Path, Path]:
    """Exporta un ONNX diminuto con dos salidas, sin entrenar nada.

    Como el exportador real, fija alto y ancho y deja libre solo el lote.
    """
    torch = pytest.importorskip("torch")

    class Diminuto(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.orden = torch.nn.Linear(3, 2)
            self.familia = torch.nn.Linear(3, 3)

        def forward(self, x):
            rasgos = x.mean(dim=(2, 3))
            return self.orden(rasgos), self.familia(rasgos)

    ruta_onnx = carpeta / f"m{lado}.onnx"
    torch.onnx.export(
        Diminuto(),
        torch.randn(1, 3, lado, lado),
        str(ruta_onnx),
        input_names=["imagen"],
        output_names=["logits_orden", "logits_familia"],
        dynamic_axes={"imagen": {0: "lote"}},
        opset_version=17,
    )
    ruta_etiquetas = carpeta / "etiquetas.json"
    ESPACIO.guardar(ruta_etiquetas)
    return ruta_onnx, ruta_etiquetas


@pytest.fixture
def modelo_falso(tmp_path: Path) -> tuple[Path, Path]:
    return exportar_diminuto(tmp_path, 224)


def bytes_imagen(lado=300):
    rng = np.random.default_rng(3)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(base).resize((lado, lado)).save(buffer, "JPEG")
    return buffer.getvalue()


def test_predecir_devuelve_orden_y_familia_del_espacio(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    prediccion = servicio.predecir_bytes(bytes_imagen())
    assert prediccion.orden in ESPACIO.ordenes
    assert prediccion.familia in ESPACIO.familias


def test_la_familia_siempre_pertenece_al_orden_predicho(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    prediccion = servicio.predecir_bytes(bytes_imagen())
    indice_familia = ESPACIO.familias.index(prediccion.familia)
    indice_orden = ESPACIO.ordenes.index(prediccion.orden)
    assert ESPACIO.matriz[indice_familia][indice_orden] is True


def test_las_confianzas_estan_entre_cero_y_uno(modelo_falso):
    prediccion = ServicioInsectos(*modelo_falso).predecir_bytes(bytes_imagen())
    assert 0.0 <= prediccion.confianza_orden <= 1.0
    assert 0.0 <= prediccion.confianza_familia <= 1.0


def test_umbral_alto_marca_la_familia_como_incierta(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso, umbral=1.1)
    assert servicio.predecir_bytes(bytes_imagen()).familia_incierta is True


def test_umbral_cero_nunca_marca_incertidumbre(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso, umbral=0.0)
    assert servicio.predecir_bytes(bytes_imagen()).familia_incierta is False


def test_imagen_invalida_lanza_error_de_imagen(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    with pytest.raises(ErrorImagen):
        servicio.predecir_bytes(b"no soy una imagen")


def test_clases_expone_la_ontologia_vigente(modelo_falso):
    clases = ServicioInsectos(*modelo_falso).clases()
    assert clases["ordenes"] == list(ESPACIO.ordenes)
    assert clases["familias"] == list(ESPACIO.familias)


def test_version_reporta_los_artefactos_cargados(modelo_falso):
    version = ServicioInsectos(*modelo_falso).version()
    assert version["n_ordenes"] == 2
    assert version["n_familias"] == 3
    assert "umbral_familia" in version


def test_el_servicio_toma_la_resolucion_del_modelo(tmp_path):
    """La v4 se entrenó a 288: el backend debe prepararle las fotos a 288.

    onnxruntime rechaza una entrada de otro tamaño, así que un servicio que
    preparara siempre a 224 fallaría aquí.
    """
    servicio = ServicioInsectos(*exportar_diminuto(tmp_path, 288))
    assert servicio.lado == 288
    assert servicio.predecir_bytes(bytes_imagen()).orden in ESPACIO.ordenes


def test_version_incluye_la_resolucion(modelo_falso):
    assert ServicioInsectos(*modelo_falso).version()["lado"] == 224


def test_el_modelo_se_carga_una_sola_vez(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    primera = servicio.sesion
    servicio.predecir_bytes(bytes_imagen())
    servicio.predecir_bytes(bytes_imagen())
    assert servicio.sesion is primera


def test_prediccion_es_determinista(modelo_falso):
    servicio = ServicioInsectos(*modelo_falso)
    datos = bytes_imagen()
    a = servicio.predecir_bytes(datos)
    b = servicio.predecir_bytes(datos)
    assert a == b
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_servicio.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'backend.servicio'`.

- [ ] **Step 3: Implementar `backend/servicio.py`**

```python
"""Servicio de inferencia sobre ONNX.

Sin PyTorch: solo onnxruntime, numpy y Pillow. El enmascaramiento jerárquico
se reutiliza tal cual de `pipeline.inferencia`, así el backend y la
evaluación toman exactamente la misma decisión.
"""
from __future__ import annotations

from pathlib import Path

import onnxruntime as ort

from backend.preproceso import desde_bytes
from pipeline.etiquetas import cargar_espacio
from pipeline.inferencia import UMBRAL_FAMILIA, Prediccion, predecir


class ErrorImagen(ValueError):
    """El archivo recibido no es una imagen que se pueda procesar."""


class ServicioInsectos:
    """Carga el modelo una vez y responde predicciones jerárquicas."""

    def __init__(
        self,
        ruta_onnx: Path,
        ruta_etiquetas: Path,
        *,
        umbral: float = UMBRAL_FAMILIA,
    ) -> None:
        self.ruta_onnx = Path(ruta_onnx)
        self.espacio = cargar_espacio(Path(ruta_etiquetas))
        self.umbral = umbral
        self.sesion = ort.InferenceSession(
            str(self.ruta_onnx), providers=["CPUExecutionProvider"]
        )
        entrada = self.sesion.get_inputs()[0]
        self.nombre_entrada = entrada.name
        # El exportador deja libre solo el lote: alto y ancho vienen fijos en el
        # ONNX. Leerlos de ahí impide preparar la foto a otro tamaño que el de
        # entrenamiento (la v4 usa 288, no 224).
        self.lado = int(entrada.shape[2])

    def predecir_bytes(self, datos: bytes) -> Prediccion:
        try:
            tensor = desde_bytes(datos, lado=self.lado)
        except ValueError as error:
            raise ErrorImagen(str(error)) from error

        logits_orden, logits_familia = self.sesion.run(None, {self.nombre_entrada: tensor})
        return predecir(
            logits_orden[0], logits_familia[0], self.espacio, umbral=self.umbral
        )

    def clases(self) -> dict:
        return {
            "ordenes": list(self.espacio.ordenes),
            "familias": list(self.espacio.familias),
            "matriz": [list(r) for r in self.espacio.matriz],
        }

    def version(self) -> dict:
        return {
            "modelo": self.ruta_onnx.name,
            "n_ordenes": len(self.espacio.ordenes),
            "n_familias": len(self.espacio.familias),
            "umbral_familia": self.umbral,
            "lado": self.lado,
        }
```

- [ ] **Step 4: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_servicio.py -v
```

Esperado: PASS, 12 pruebas.

- [ ] **Step 5: Commit**

```powershell
git add backend/servicio.py tests/test_servicio.py
git commit -m "feat: servicio de inferencia onnx reutilizando el enmascaramiento del pipeline"
```

---

## Task 3: Fichas biológicas desde SQLite

**Files:**
- Create: `backend/fichas.py`
- Test: `tests/test_fichas.py`

**Interfaces:**
- Consumes: `pipeline.bd.COLUMNAS_BD` (solo los nombres; no importa pandas)
- Produces:
  - `class RepositorioFichas` — `__init__(self, ruta_sqlite: Path)`, `por_taxon(self, orden: str, familia: str = "") -> list[dict]`, `por_id(self, identificador: str) -> dict | None`, `resumen_por_orden(self) -> list[dict]`, `disponible(self) -> bool`

**Diseño deliberado:** el repositorio funciona aunque la base de datos no exista. En Semana 12 es plausible que Agronomía aún no haya llenado el Excel; el prototipo debe seguir prediciendo y simplemente no mostrar ficha. Un backend que no arranca sin BD bloquea la demostración por una razón que no es técnica.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_fichas.py`:

```python
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
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_fichas.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'backend.fichas'`.

- [ ] **Step 3: Implementar `backend/fichas.py`**

```python
"""Acceso de solo lectura a la base de datos biológica.

Tolera que la base no exista: en las primeras semanas Agronomía puede no
haber llenado el Excel todavía, y el prototipo debe poder demostrarse igual.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from pipeline.bd import COLUMNAS_BD


class RepositorioFichas:
    def __init__(self, ruta_sqlite: Path) -> None:
        self.ruta = Path(ruta_sqlite)

    def disponible(self) -> bool:
        return self.ruta.exists()

    def _consultar(self, sql: str, parametros: tuple) -> list[dict]:
        if not self.disponible():
            return []
        conexion = sqlite3.connect(self.ruta)
        conexion.row_factory = sqlite3.Row
        try:
            return [dict(f) for f in conexion.execute(sql, parametros).fetchall()]
        except sqlite3.DatabaseError:
            return []
        finally:
            conexion.close()

    def por_taxon(self, orden: str, familia: str = "") -> list[dict]:
        columnas = ", ".join(COLUMNAS_BD)
        if familia:
            return self._consultar(
                f"SELECT {columnas} FROM insectos WHERE Orden = ? AND Familia = ? "
                "ORDER BY ID",
                (orden, familia),
            )
        return self._consultar(
            f"SELECT {columnas} FROM insectos WHERE Orden = ? ORDER BY ID", (orden,)
        )

    def por_id(self, identificador: str) -> dict | None:
        columnas = ", ".join(COLUMNAS_BD)
        filas = self._consultar(
            f"SELECT {columnas} FROM insectos WHERE ID = ?", (identificador,)
        )
        return filas[0] if filas else None

    def resumen_por_orden(self) -> list[dict]:
        return self._consultar(
            "SELECT Orden AS orden, COUNT(*) AS registros FROM insectos "
            "GROUP BY Orden ORDER BY Orden",
            (),
        )
```

- [ ] **Step 4: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_fichas.py -v
```

Esperado: PASS, 10 pruebas.

- [ ] **Step 5: Commit**

```powershell
git add backend/fichas.py tests/test_fichas.py
git commit -m "feat: repositorio de fichas biologicas tolerante a base ausente"
```

---

## Task 4: API FastAPI

**Files:**
- Create: `backend/app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `backend.servicio.ServicioInsectos`, `ErrorImagen`; `backend.fichas.RepositorioFichas`
- Produces:
  - `crear_app(servicio, repositorio) -> FastAPI` — fábrica que permite inyectar dobles en las pruebas
  - `app_produccion() -> FastAPI` — fábrica de la app real, invocada por uvicorn con `--factory`

> **Nada se construye al importar el módulo.** Si `app = crear_app(ServicioInsectos(...), ...)` viviera a nivel de módulo, importar `backend.app` en las pruebas cargaría el ONNX real y fallaría mientras el Plan 02 no esté terminado. La fábrica difiere esa carga al arranque del servidor.

| Endpoint | Respuesta |
| --- | --- |
| `GET /salud` | `{"estado": "ok", "modelo": ..., "n_ordenes": ..., "n_familias": ..., "umbral_familia": ..., "lado": ..., "bd_disponible": bool}` |
| `GET /clases` | `{"ordenes": [...], "familias": [...], "matriz": [[...]]}` |
| `POST /predecir` | `{"orden", "confianza_orden", "familia", "confianza_familia", "familia_incierta", "top_familias": [{"familia", "confianza"}], "fichas": [...]}` |
| `GET /taxon/{orden}` | `{"orden", "familia", "fichas": [...]}` — familia opcional por query |

- [ ] **Step 1: Instalar httpx para el cliente de pruebas**

```powershell
.venv\Scripts\python -m pip install httpx
```

Añadir `httpx>=0.28` al extra `dev` de `pyproject.toml`.

- [ ] **Step 2: Escribir las pruebas que fallan**

`tests/test_app.py`:

```python
import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app import crear_app
from backend.servicio import ErrorImagen
from pipeline.inferencia import Prediccion

PREDICCION = Prediccion(
    orden="Coleoptera",
    confianza_orden=0.93,
    familia="Curculionidae",
    confianza_familia=0.71,
    familia_incierta=False,
    top_familias=(("Curculionidae", 0.71), ("Chrysomelidae", 0.22)),
)


class ServicioFalso:
    def __init__(self, prediccion=PREDICCION, falla=False):
        self.prediccion = prediccion
        self.falla = falla

    def predecir_bytes(self, datos):
        if self.falla:
            raise ErrorImagen("el archivo no es una imagen válida")
        return self.prediccion

    def clases(self):
        return {
            "ordenes": ["Coleoptera", "Odonata"],
            "familias": ["Curculionidae"],
            "matriz": [[True, False]],
        }

    def version(self):
        return {
            "modelo": "insectos.onnx",
            "n_ordenes": 2,
            "n_familias": 1,
            "umbral_familia": 0.7,
            "lado": 288,
        }


class RepositorioFalso:
    def __init__(self, fichas=None, hay_base=True):
        self.fichas = fichas if fichas is not None else [{"ID": "INS-0001", "Nombre_comun": "gorgojo"}]
        self.hay_base = hay_base

    def disponible(self):
        return self.hay_base

    def por_taxon(self, orden, familia=""):
        return self.fichas

    def resumen_por_orden(self):
        return [{"orden": "Coleoptera", "registros": 1}]


def cliente(servicio=None, repositorio=None):
    return TestClient(crear_app(servicio or ServicioFalso(), repositorio or RepositorioFalso()))


def archivo_jpg():
    rng = np.random.default_rng(1)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(base).resize((300, 300)).save(buffer, "JPEG")
    buffer.seek(0)
    return {"archivo": ("insecto.jpg", buffer, "image/jpeg")}


def test_salud_responde_ok():
    respuesta = cliente().get("/salud")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["n_ordenes"] == 2
    assert cuerpo["bd_disponible"] is True


def test_salud_reporta_base_ausente():
    cuerpo = cliente(repositorio=RepositorioFalso(hay_base=False)).get("/salud").json()
    assert cuerpo["bd_disponible"] is False


def test_clases_devuelve_la_ontologia():
    cuerpo = cliente().get("/clases").json()
    assert cuerpo["ordenes"] == ["Coleoptera", "Odonata"]


def test_predecir_devuelve_la_jerarquia():
    cuerpo = cliente().post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["orden"] == "Coleoptera"
    assert cuerpo["familia"] == "Curculionidae"
    assert cuerpo["confianza_orden"] == pytest.approx(0.93)
    assert cuerpo["familia_incierta"] is False


def test_predecir_incluye_el_top_de_familias_con_nombres():
    cuerpo = cliente().post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["top_familias"][0] == {"familia": "Curculionidae", "confianza": pytest.approx(0.71)}


def test_predecir_adjunta_las_fichas_de_la_base():
    cuerpo = cliente().post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["fichas"][0]["Nombre_comun"] == "gorgojo"


def test_predecir_sin_base_devuelve_fichas_vacias():
    repositorio = RepositorioFalso(fichas=[], hay_base=False)
    cuerpo = cliente(repositorio=repositorio).post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["fichas"] == []
    assert cuerpo["orden"] == "Coleoptera"  # la predicción sigue funcionando


def test_predecir_con_archivo_invalido_da_400_en_espanol():
    respuesta = cliente(servicio=ServicioFalso(falla=True)).post("/predecir", files=archivo_jpg())
    assert respuesta.status_code == 400
    assert "imagen" in respuesta.json()["detail"].lower()


def test_predecir_sin_archivo_da_422():
    assert cliente().post("/predecir").status_code == 422


def test_familia_incierta_se_propaga_al_cliente():
    incierta = Prediccion(
        orden="Coleoptera",
        confianza_orden=0.88,
        familia="Curculionidae",
        confianza_familia=0.31,
        familia_incierta=True,
        top_familias=(("Curculionidae", 0.31), ("Chrysomelidae", 0.29)),
    )
    cuerpo = cliente(servicio=ServicioFalso(incierta)).post("/predecir", files=archivo_jpg()).json()
    assert cuerpo["familia_incierta"] is True


def test_taxon_devuelve_las_fichas_del_orden():
    cuerpo = cliente().get("/taxon/Coleoptera").json()
    assert cuerpo["orden"] == "Coleoptera"
    assert len(cuerpo["fichas"]) == 1


def test_taxon_acepta_familia_por_query():
    cuerpo = cliente().get("/taxon/Coleoptera", params={"familia": "Curculionidae"}).json()
    assert cuerpo["familia"] == "Curculionidae"


def test_cors_permite_al_frontend_de_desarrollo():
    respuesta = cliente().get("/salud", headers={"Origin": "http://localhost:5173"})
    assert respuesta.headers.get("access-control-allow-origin") is not None
```

- [ ] **Step 3: Correr las pruebas para verificar que fallan**

```powershell
.venv\Scripts\python -m pytest tests/test_app.py -v
```

Esperado: FAIL con `ModuleNotFoundError: No module named 'backend.app'`.

- [ ] **Step 4: Implementar `backend/app.py`**

```python
"""API del prototipo de identificación de insectos."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.fichas import RepositorioFichas
from backend.servicio import ErrorImagen, ServicioInsectos

RAIZ = Path(__file__).resolve().parent.parent
# Corrida que sirve el prototipo. Al registrar una mejor, cambiarla aquí y en
# iniciar.bat; MODELO_DIR permite apuntar a otra sin tocar código.
CORRIDA_VIGENTE = "v4_convnext_t_288"
ORIGENES = ["http://localhost:5173", "http://127.0.0.1:5173"]


def crear_app(servicio, repositorio) -> FastAPI:
    """Fábrica con dependencias inyectadas: las pruebas usan dobles."""
    app = FastAPI(
        title="Identificador de insectos amazónicos",
        description="Clasificación jerárquica orden → familia",
        version="1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGENES,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/salud")
    def salud() -> dict:
        return {
            "estado": "ok",
            **servicio.version(),
            "bd_disponible": repositorio.disponible(),
        }

    @app.get("/clases")
    def clases() -> dict:
        return servicio.clases()

    @app.post("/predecir")
    async def predecir(archivo: UploadFile = File(...)) -> dict:
        datos = await archivo.read()
        try:
            prediccion = servicio.predecir_bytes(datos)
        except ErrorImagen as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        return {
            "orden": prediccion.orden,
            "confianza_orden": prediccion.confianza_orden,
            "familia": prediccion.familia,
            "confianza_familia": prediccion.confianza_familia,
            "familia_incierta": prediccion.familia_incierta,
            "top_familias": [
                {"familia": nombre, "confianza": valor}
                for nombre, valor in prediccion.top_familias
            ],
            "fichas": repositorio.por_taxon(prediccion.orden, prediccion.familia),
        }

    @app.get("/taxon/{orden}")
    def taxon(orden: str, familia: str = "") -> dict:
        return {
            "orden": orden,
            "familia": familia,
            "fichas": repositorio.por_taxon(orden, familia),
        }

    @app.get("/resumen")
    def resumen() -> dict:
        return {"por_orden": repositorio.resumen_por_orden()}

    return app


def app_produccion() -> FastAPI:
    """Fábrica de la app real. Carga el modelo al arrancar, no al importar.

    Se usa con `uvicorn backend.app:app_produccion --factory`. Si esto se
    construyera a nivel de módulo, importar `backend.app` para probarlo
    fallaría mientras no exista el ONNX de la corrida.
    """
    carpeta = Path(os.environ.get("MODELO_DIR", RAIZ / "modelo" / CORRIDA_VIGENTE))
    return crear_app(
        ServicioInsectos(carpeta / "insectos.onnx", carpeta / "etiquetas.json"),
        RepositorioFichas(
            Path(os.environ.get("BD_SQLITE", RAIZ / "bd" / "bd_insectos.sqlite"))
        ),
    )
```

- [ ] **Step 5: Correr las pruebas para verificar que pasan**

```powershell
.venv\Scripts\python -m pytest tests/test_app.py -v
```

Esperado: PASS, 13 pruebas. Estas pruebas corren sin que exista el ONNX de la corrida: usan `crear_app` con dobles y nunca invocan `app_produccion()`.

- [ ] **Step 6: Levantar el servidor y probarlo a mano**

Requiere `modelo/v4_convnext_t_288/insectos.onnx` y `etiquetas.json`, copiados de la corrida (ver CLAUDE.md).

```powershell
.venv\Scripts\python -m uvicorn backend.app:app_produccion --factory --reload --port 8000
```

Abrir `http://127.0.0.1:8000/docs` y probar `/predecir` con una foto de `..\insectos-demo\ejemplos`.

- [ ] **Step 7: Commit**

```powershell
git add backend/app.py tests/test_app.py pyproject.toml
git commit -m "feat: api fastapi con prediccion jerarquica y fichas biologicas"
```

---

## Task 5: Andamiaje del frontend y cliente de la API

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.js`, `frontend/index.html`, `frontend/src/main.jsx`, `frontend/src/api.js`
- Test: `frontend/pruebas/api.test.js`

**Interfaces:**
- Consumes: la API de la Tarea 4
- Produces:
  - `BASE_API: string`
  - `obtenerSalud(): Promise<object>`
  - `obtenerClases(): Promise<object>`
  - `predecir(archivo: File): Promise<object>`
  - `obtenerTaxon(orden: string, familia?: string): Promise<object>`
  - `class ErrorApi extends Error` con propiedad `estado`

- [ ] **Step 1: Crear el proyecto Vite**

```powershell
cd D:\300\OTROS\XXX\DAN\IA\agro\insectos-ia
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

- [ ] **Step 2: Configurar Vitest en `frontend/vite.config.js`**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './pruebas/preparacion.js',
    include: ['pruebas/**/*.test.{js,jsx}'],
  },
})
```

`frontend/pruebas/preparacion.js`:

```javascript
import '@testing-library/jest-dom'
```

Añadir a `frontend/package.json`, dentro de `scripts`:

```json
"prueba": "vitest run"
```

- [ ] **Step 3: Escribir las pruebas que fallan**

`frontend/pruebas/api.test.js`:

```javascript
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ErrorApi, obtenerClases, obtenerSalud, obtenerTaxon, predecir } from '../src/api.js'

function respuesta(cuerpo, ok = true, estado = 200) {
  return Promise.resolve({ ok, status: estado, json: () => Promise.resolve(cuerpo) })
}

afterEach(() => vi.restoreAllMocks())

describe('cliente de la API', () => {
  it('obtiene el estado de salud', async () => {
    global.fetch = vi.fn(() => respuesta({ estado: 'ok' }))
    expect(await obtenerSalud()).toEqual({ estado: 'ok' })
  })

  it('obtiene las clases', async () => {
    global.fetch = vi.fn(() => respuesta({ ordenes: ['Coleoptera'] }))
    const clases = await obtenerClases()
    expect(clases.ordenes).toEqual(['Coleoptera'])
  })

  it('envía la imagen como multipart con el campo "archivo"', async () => {
    global.fetch = vi.fn(() => respuesta({ orden: 'Coleoptera' }))
    const archivo = new File(['x'], 'insecto.jpg', { type: 'image/jpeg' })
    await predecir(archivo)

    const [, opciones] = global.fetch.mock.calls[0]
    expect(opciones.method).toBe('POST')
    expect(opciones.body).toBeInstanceOf(FormData)
    expect(opciones.body.get('archivo')).toBe(archivo)
  })

  it('lanza ErrorApi con el estado cuando la respuesta falla', async () => {
    global.fetch = vi.fn(() => respuesta({ detail: 'el archivo no es una imagen válida' }, false, 400))
    const archivo = new File(['x'], 'malo.txt', { type: 'text/plain' })
    await expect(predecir(archivo)).rejects.toThrow(ErrorApi)
  })

  it('el mensaje del error viene del backend', async () => {
    global.fetch = vi.fn(() => respuesta({ detail: 'el archivo no es una imagen válida' }, false, 400))
    try {
      await predecir(new File(['x'], 'malo.txt'))
      throw new Error('debió lanzar')
    } catch (error) {
      expect(error.message).toContain('imagen')
      expect(error.estado).toBe(400)
    }
  })

  it('avisa cuando el servidor no responde', async () => {
    global.fetch = vi.fn(() => Promise.reject(new TypeError('Failed to fetch')))
    await expect(obtenerSalud()).rejects.toThrow(/servidor/i)
  })

  it('pasa la familia como parámetro de consulta', async () => {
    global.fetch = vi.fn(() => respuesta({ fichas: [] }))
    await obtenerTaxon('Coleoptera', 'Curculionidae')
    expect(global.fetch.mock.calls[0][0]).toContain('familia=Curculionidae')
  })

  it('omite la familia cuando no se pasa', async () => {
    global.fetch = vi.fn(() => respuesta({ fichas: [] }))
    await obtenerTaxon('Coleoptera')
    expect(global.fetch.mock.calls[0][0]).not.toContain('familia=')
  })
})
```

- [ ] **Step 4: Correr las pruebas para verificar que fallan**

```powershell
cd frontend
npm run prueba
```

Esperado: FAIL, no existe `src/api.js`.

- [ ] **Step 5: Implementar `frontend/src/api.js`**

```javascript
// Cliente HTTP del backend. Es el único lugar del frontend que sabe de rutas.
export const BASE_API = import.meta.env.VITE_API ?? 'http://127.0.0.1:8000'

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
  }
}

async function pedir(ruta, opciones = {}) {
  let respuesta
  try {
    respuesta = await fetch(`${BASE_API}${ruta}`, opciones)
  } catch {
    throw new ErrorApi('No se pudo conectar con el servidor. ¿Está encendido?', 0)
  }

  let cuerpo = {}
  try {
    cuerpo = await respuesta.json()
  } catch {
    cuerpo = {}
  }

  if (!respuesta.ok) {
    throw new ErrorApi(cuerpo.detail ?? 'Ocurrió un error inesperado.', respuesta.status)
  }
  return cuerpo
}

export function obtenerSalud() {
  return pedir('/salud')
}

export function obtenerClases() {
  return pedir('/clases')
}

export function predecir(archivo) {
  const cuerpo = new FormData()
  cuerpo.append('archivo', archivo)
  return pedir('/predecir', { method: 'POST', body: cuerpo })
}

export function obtenerTaxon(orden, familia = '') {
  const consulta = familia ? `?familia=${encodeURIComponent(familia)}` : ''
  return pedir(`/taxon/${encodeURIComponent(orden)}${consulta}`)
}
```

- [ ] **Step 6: Correr las pruebas para verificar que pasan**

```powershell
npm run prueba
```

Esperado: PASS, 8 pruebas.

- [ ] **Step 7: Commit**

```powershell
cd ..
git add frontend/package.json frontend/package-lock.json frontend/vite.config.js frontend/index.html frontend/src/api.js frontend/src/main.jsx frontend/pruebas
git commit -m "feat: andamiaje del frontend y cliente de la api"
```

---

## Task 6: Subida de foto y resultado jerárquico

**Files:**
- Create: `frontend/src/componentes/SubirFoto.jsx`, `frontend/src/componentes/Resultado.jsx`, `frontend/src/App.jsx`, `frontend/src/estilos.css`
- Test: `frontend/pruebas/Resultado.test.jsx`

**Interfaces:**
- Consumes: `../src/api.js`
- Produces:
  - `<SubirFoto alSeleccionar={(archivo) => void} ocupado={boolean} />`
  - `<Resultado prediccion={objeto|null} />`

**Requisito de honestidad de la interfaz.** Cuando `familia_incierta` es verdadero, la pantalla **no** muestra la familia como respuesta afirmativa: muestra el orden con su confianza y presenta las familias candidatas como opciones a revisar. Es la traducción visual de la degradación elegante del diseño (§3). Una interfaz que afirma "Curculionidae 31%" con la misma tipografía que "Curculionidae 94%" desinforma.

- [ ] **Step 1: Escribir las pruebas que fallan**

`frontend/pruebas/Resultado.test.jsx`:

```javascript
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Resultado from '../src/componentes/Resultado.jsx'

const CERTERO = {
  orden: 'Coleoptera',
  confianza_orden: 0.94,
  familia: 'Curculionidae',
  confianza_familia: 0.81,
  familia_incierta: false,
  top_familias: [
    { familia: 'Curculionidae', confianza: 0.81 },
    { familia: 'Chrysomelidae', confianza: 0.12 },
  ],
  fichas: [],
}

const INCIERTO = { ...CERTERO, confianza_familia: 0.31, familia_incierta: true }

describe('Resultado', () => {
  it('no muestra nada sin predicción', () => {
    const { container } = render(<Resultado prediccion={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('muestra el orden y su confianza en porcentaje', () => {
    render(<Resultado prediccion={CERTERO} />)
    expect(screen.getByText(/Coleoptera/)).toBeInTheDocument()
    expect(screen.getByText(/94\s*%/)).toBeInTheDocument()
  })

  it('muestra la familia cuando hay certeza', () => {
    render(<Resultado prediccion={CERTERO} />)
    expect(screen.getByText('Curculionidae')).toBeInTheDocument()
    expect(screen.getByText(/81\s*%/)).toBeInTheDocument()
  })

  it('avisa cuando la familia es incierta', () => {
    render(<Resultado prediccion={INCIERTO} />)
    expect(screen.getByText(/incierta|no se puede determinar/i)).toBeInTheDocument()
  })

  it('con familia incierta muestra las candidatas', () => {
    render(<Resultado prediccion={INCIERTO} />)
    expect(screen.getByText('Chrysomelidae')).toBeInTheDocument()
  })

  it('el orden se sigue mostrando aunque la familia sea incierta', () => {
    render(<Resultado prediccion={INCIERTO} />)
    expect(screen.getByText(/Coleoptera/)).toBeInTheDocument()
  })

  it('maneja un orden sin familias entrenadas', () => {
    render(
      <Resultado
        prediccion={{ ...CERTERO, familia: '', familia_incierta: true, top_familias: [] }}
      />,
    )
    expect(screen.getByText(/Coleoptera/)).toBeInTheDocument()
    expect(screen.queryByText('Curculionidae')).not.toBeInTheDocument()
  })

  it('marca visualmente el estado incierto', () => {
    const { container } = render(<Resultado prediccion={INCIERTO} />)
    expect(container.querySelector('.incierto')).not.toBeNull()
  })
})
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
cd frontend
npm run prueba
```

Esperado: FAIL, no existe `src/componentes/Resultado.jsx`.

- [ ] **Step 3: Implementar `frontend/src/componentes/Resultado.jsx`**

```jsx
const porcentaje = (valor) => `${Math.round(valor * 100)} %`

export default function Resultado({ prediccion }) {
  if (!prediccion) return null

  const { orden, confianza_orden, familia, confianza_familia, familia_incierta, top_familias } =
    prediccion

  return (
    <section className="resultado">
      <div className="nivel">
        <span className="etiqueta">Orden</span>
        <strong className="valor">{orden}</strong>
        <span className="confianza">{porcentaje(confianza_orden)}</span>
      </div>

      {familia_incierta ? (
        <div className="nivel incierto">
          <span className="etiqueta">Familia</span>
          <strong className="valor">No se puede determinar con certeza</strong>
          {top_familias.length > 0 && (
            <>
              <p className="ayuda">
                Candidatas dentro de {orden}, para revisar con un especialista:
              </p>
              <ul className="candidatas">
                {top_familias.map(({ familia: nombre, confianza }) => (
                  <li key={nombre}>
                    <span>{nombre}</span>
                    <span className="confianza">{porcentaje(confianza)}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      ) : (
        <div className="nivel">
          <span className="etiqueta">Familia</span>
          <strong className="valor">{familia}</strong>
          <span className="confianza">{porcentaje(confianza_familia)}</span>
        </div>
      )}
    </section>
  )
}
```

- [ ] **Step 4: Implementar `frontend/src/componentes/SubirFoto.jsx`**

```jsx
import { useState } from 'react'

export default function SubirFoto({ alSeleccionar, ocupado }) {
  const [vistaPrevia, setVistaPrevia] = useState(null)

  function manejar(evento) {
    const archivo = evento.target.files?.[0]
    if (!archivo) return
    setVistaPrevia(URL.createObjectURL(archivo))
    alSeleccionar(archivo)
  }

  return (
    <div className="subir">
      <label className="boton">
        {ocupado ? 'Identificando…' : 'Elegir foto del insecto'}
        <input type="file" accept="image/*" onChange={manejar} disabled={ocupado} hidden />
      </label>
      {vistaPrevia && <img className="vista-previa" src={vistaPrevia} alt="Foto seleccionada" />}
    </div>
  )
}
```

- [ ] **Step 5: Implementar `frontend/src/App.jsx`**

```jsx
import { useEffect, useState } from 'react'
import { obtenerSalud, predecir } from './api.js'
import Ficha from './componentes/Ficha.jsx'
import Resultado from './componentes/Resultado.jsx'
import SubirFoto from './componentes/SubirFoto.jsx'
import './estilos.css'

export default function App() {
  const [prediccion, setPrediccion] = useState(null)
  const [error, setError] = useState(null)
  const [ocupado, setOcupado] = useState(false)
  const [salud, setSalud] = useState(null)

  useEffect(() => {
    obtenerSalud().then(setSalud).catch((e) => setError(e.message))
  }, [])

  async function identificar(archivo) {
    setOcupado(true)
    setError(null)
    setPrediccion(null)
    try {
      setPrediccion(await predecir(archivo))
    } catch (e) {
      setError(e.message)
    } finally {
      setOcupado(false)
    }
  }

  return (
    <main className="app">
      <header>
        <h1>Identificador de insectos amazónicos</h1>
        <p className="subtitulo">Sube una foto y el sistema propone el orden y la familia.</p>
      </header>

      <SubirFoto alSeleccionar={identificar} ocupado={ocupado} />

      {error && <p className="error">{error}</p>}

      <Resultado prediccion={prediccion} />
      {prediccion && <Ficha fichas={prediccion.fichas} />}

      {salud && (
        <footer className="pie">
          Modelo con {salud.n_ordenes} órdenes y {salud.n_familias} familias
          {!salud.bd_disponible && ' · base de datos biológica aún no cargada'}
        </footer>
      )}
    </main>
  )
}
```

- [ ] **Step 6: Implementar `frontend/src/estilos.css`**

```css
:root {
  --tinta: #16281f;
  --papel: #f7f6f1;
  --acento: #2f6d4f;
  --aviso: #9a6b16;
  --borde: #dcd9cf;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--papel);
  color: var(--tinta);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}

.app { max-width: 46rem; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
.subtitulo { color: #5a6b61; margin-top: 0; }

.subir { margin: 2rem 0; }
.boton {
  display: inline-block;
  padding: 0.75rem 1.25rem;
  background: var(--acento);
  color: #fff;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 600;
}
.vista-previa {
  display: block;
  margin-top: 1rem;
  max-width: 20rem;
  width: 100%;
  border-radius: 0.5rem;
  border: 1px solid var(--borde);
}

.resultado { display: grid; gap: 0.75rem; }
.nivel {
  background: #fff;
  border: 1px solid var(--borde);
  border-left: 4px solid var(--acento);
  border-radius: 0.5rem;
  padding: 1rem;
}
.nivel.incierto { border-left-color: var(--aviso); }
.etiqueta { display: block; font-size: 0.8rem; text-transform: uppercase; color: #6b7a72; }
.valor { display: block; font-size: 1.3rem; margin: 0.15rem 0; }
.confianza { color: #5a6b61; font-variant-numeric: tabular-nums; }
.ayuda { font-size: 0.9rem; color: #6b7a72; margin-bottom: 0.35rem; }
.candidatas { list-style: none; padding: 0; margin: 0; }
.candidatas li { display: flex; justify-content: space-between; padding: 0.3rem 0; }

.error {
  background: #fdeceb;
  border: 1px solid #f0b4ae;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
}

.pie { margin-top: 3rem; font-size: 0.85rem; color: #6b7a72; }

table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
th, td { text-align: left; padding: 0.45rem 0.6rem; border-bottom: 1px solid var(--borde); }
```

- [ ] **Step 7: Correr las pruebas para verificar que pasan**

```powershell
npm run prueba
```

Esperado: PASS, 16 pruebas (8 de la Tarea 5 + 8 de esta). Fallará el import de `Ficha.jsx` en `App.jsx` hasta la Tarea 7; crear ese archivo con un componente que devuelva `null` y completarlo allí.

- [ ] **Step 8: Commit**

```powershell
cd ..
git add frontend/src frontend/pruebas
git commit -m "feat: subida de foto y resultado jerarquico con incertidumbre visible"
```

---

## Task 7: Ficha biológica y explorador de la base de datos

**Files:**
- Create: `frontend/src/componentes/Ficha.jsx`, `frontend/src/componentes/Explorador.jsx`
- Modify: `frontend/src/App.jsx` (añadir el explorador)
- Test: `frontend/pruebas/Ficha.test.jsx`

**Interfaces:**
- Consumes: `../src/api.js` (`obtenerTaxon`)
- Produces:
  - `<Ficha fichas={array} />`
  - `<Explorador />`

**Campos que se muestran, y en este orden:** `Nombre_comun`, `Nombre_cientifico`, `Cultivo_asociado`, `Tipo_de_dano`, `Importancia_economica`, `Hospedero`, `Localidad`, `Estado_biologico`, `Verificado_por`. Son los que le importan a alguien de agronomía; los de control interno (`ID`, `Archivo_imagen`, `Fuente`, `Observaciones`) no se muestran en la ficha.

- [ ] **Step 1: Escribir las pruebas que fallan**

`frontend/pruebas/Ficha.test.jsx`:

```javascript
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Ficha from '../src/componentes/Ficha.jsx'

const REGISTRO = {
  ID: 'INS-0001',
  Nombre_comun: 'gorgojo del plátano',
  Nombre_cientifico: 'Cosmopolites sordidus',
  Cultivo_asociado: 'plátano',
  Tipo_de_dano: 'perforación del cormo',
  Importancia_economica: 'plaga',
  Hospedero: 'Musa spp.',
  Localidad: 'Iquitos',
  Estado_biologico: 'adulto',
  Verificado_por: 'M. Ruiz',
  Archivo_imagen: 'x.jpg',
  Observaciones: 'nota interna',
}

describe('Ficha', () => {
  it('avisa cuando no hay registros', () => {
    render(<Ficha fichas={[]} />)
    expect(screen.getByText(/no hay registros/i)).toBeInTheDocument()
  })

  it('avisa igual si no le pasan nada', () => {
    render(<Ficha />)
    expect(screen.getByText(/no hay registros/i)).toBeInTheDocument()
  })

  it('muestra el nombre común y el científico', () => {
    render(<Ficha fichas={[REGISTRO]} />)
    expect(screen.getByText('gorgojo del plátano')).toBeInTheDocument()
    expect(screen.getByText('Cosmopolites sordidus')).toBeInTheDocument()
  })

  it('muestra el cultivo asociado y el tipo de daño', () => {
    render(<Ficha fichas={[REGISTRO]} />)
    expect(screen.getByText('plátano')).toBeInTheDocument()
    expect(screen.getByText('perforación del cormo')).toBeInTheDocument()
  })

  it('no muestra campos de control interno', () => {
    render(<Ficha fichas={[REGISTRO]} />)
    expect(screen.queryByText('nota interna')).not.toBeInTheDocument()
    expect(screen.queryByText('x.jpg')).not.toBeInTheDocument()
  })

  it('omite los campos vacíos', () => {
    render(<Ficha fichas={[{ ...REGISTRO, Localidad: '' }]} />)
    expect(screen.queryByText('Localidad')).not.toBeInTheDocument()
  })

  it('muestra varios registros', () => {
    render(<Ficha fichas={[REGISTRO, { ...REGISTRO, ID: 'INS-0002', Nombre_comun: 'otro' }]} />)
    expect(screen.getByText('gorgojo del plátano')).toBeInTheDocument()
    expect(screen.getByText('otro')).toBeInTheDocument()
  })

  it('destaca los registros marcados como plaga', () => {
    const { container } = render(<Ficha fichas={[REGISTRO]} />)
    expect(container.querySelector('.plaga')).not.toBeNull()
  })
})
```

- [ ] **Step 2: Correr las pruebas para verificar que fallan**

```powershell
cd frontend
npm run prueba
```

Esperado: FAIL en `Ficha.test.jsx` (el componente devuelve `null`).

- [ ] **Step 3: Implementar `frontend/src/componentes/Ficha.jsx`**

```jsx
// Campos visibles y su etiqueta, en el orden que le sirve a agronomía.
const CAMPOS = [
  ['Nombre_comun', 'Nombre común'],
  ['Nombre_cientifico', 'Nombre científico'],
  ['Cultivo_asociado', 'Cultivo asociado'],
  ['Tipo_de_dano', 'Tipo de daño'],
  ['Importancia_economica', 'Importancia económica'],
  ['Hospedero', 'Hospedero'],
  ['Localidad', 'Localidad'],
  ['Estado_biologico', 'Estado biológico'],
  ['Verificado_por', 'Verificado por'],
]

export default function Ficha({ fichas }) {
  if (!fichas || fichas.length === 0) {
    return (
      <section className="ficha">
        <p className="ayuda">
          No hay registros en la base de datos biológica para este taxón todavía.
        </p>
      </section>
    )
  }

  return (
    <section className="ficha">
      <h2>Información biológica</h2>
      {fichas.map((registro) => (
        <table
          key={registro.ID}
          className={registro.Importancia_economica === 'plaga' ? 'plaga' : undefined}
        >
          <tbody>
            {CAMPOS.filter(([clave]) => registro[clave]).map(([clave, etiqueta]) => (
              <tr key={clave}>
                <th scope="row">{etiqueta}</th>
                <td>{registro[clave]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ))}
    </section>
  )
}
```

- [ ] **Step 4: Implementar `frontend/src/componentes/Explorador.jsx`**

```jsx
import { useEffect, useState } from 'react'
import { obtenerClases, obtenerTaxon } from '../api.js'
import Ficha from './Ficha.jsx'

export default function Explorador() {
  const [ordenes, setOrdenes] = useState([])
  const [orden, setOrden] = useState('')
  const [fichas, setFichas] = useState([])

  useEffect(() => {
    obtenerClases()
      .then((clases) => setOrdenes(clases.ordenes))
      .catch(() => setOrdenes([]))
  }, [])

  useEffect(() => {
    if (!orden) return
    obtenerTaxon(orden)
      .then((datos) => setFichas(datos.fichas))
      .catch(() => setFichas([]))
  }, [orden])

  if (ordenes.length === 0) return null

  return (
    <section className="explorador">
      <h2>Explorar la base de datos</h2>
      <select value={orden} onChange={(e) => setOrden(e.target.value)}>
        <option value="">Elegir un orden…</option>
        {ordenes.map((nombre) => (
          <option key={nombre} value={nombre}>
            {nombre}
          </option>
        ))}
      </select>
      {orden && <Ficha fichas={fichas} />}
    </section>
  )
}
```

- [ ] **Step 5: Añadir el explorador a `frontend/src/App.jsx`**

Importar el componente junto a los demás:

```jsx
import Explorador from './componentes/Explorador.jsx'
```

y colocarlo entre `<Ficha …/>` y el `<footer>`:

```jsx
      <Explorador />
```

- [ ] **Step 6: Correr las pruebas para verificar que pasan**

```powershell
npm run prueba
```

Esperado: PASS, 24 pruebas.

- [ ] **Step 7: Ver la aplicación completa**

En una terminal:

```powershell
.venv\Scripts\python -m uvicorn backend.app:app_produccion --factory --port 8000
```

En otra:

```powershell
cd frontend
npm run dev
```

Abrir `http://localhost:5173`, subir una foto de `..\insectos-demo\ejemplos` y verificar que aparecen orden, familia y ficha.

- [ ] **Step 8: Commit**

```powershell
cd ..
git add frontend/src frontend/pruebas
git commit -m "feat: ficha biologica y explorador de la base de datos"
```

---

## Task 8: Arranque de un clic y documentación de despliegue

**Files:**
- Create: `iniciar.bat`
- Modify: `README.md`
- Test: verificación manual (esta tarea no tiene pruebas automatizadas: orquesta procesos)

**Interfaces:**
- Consumes: todo lo anterior
- Produces: `iniciar.bat` que levanta backend y frontend y abre el navegador

**Por qué importa.** La demo anterior se presentó con un `.bat` de un clic, y funcionó. En una sustentación nadie quiere abrir dos terminales y recordar comandos.

- [ ] **Step 1: Construir el frontend para producción**

```powershell
cd frontend
npm run build
cd ..
```

Esperado: `frontend/dist/`.

- [ ] **Step 2: Servir el frontend construido desde FastAPI**

Añadir al final de `crear_app` en `backend/app.py`, justo antes de `return app`:

```python
    # Sirve el frontend construido, si existe. En desarrollo se usa Vite (5173)
    # y este bloque simplemente no se activa.
    dist = RAIZ / "frontend" / "dist"
    if dist.exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")
```

- [ ] **Step 3: Verificar que las pruebas del backend siguen pasando**

```powershell
.venv\Scripts\python -m pytest tests/test_app.py -v
```

Esperado: PASS, 13 pruebas. El montaje estático no debe interferir con los endpoints, porque se monta en `/` **después** de declararlos.

- [ ] **Step 4: Crear `iniciar.bat`**

```bat
@echo off
REM Arranque de un clic del prototipo de identificacion de insectos.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno virtual...
    py -3.12 -m venv .venv
    .venv\Scripts\python -m pip install --upgrade pip
    .venv\Scripts\python -m pip install -r backend\requirements.txt
)

REM Corrida que sirve el prototipo: la misma que CORRIDA_VIGENTE en backend\app.py.
set "MODELO_DIR=modelo\v4_convnext_t_288"

if not exist "%MODELO_DIR%\insectos.onnx" (
    echo.
    echo ERROR: falta %MODELO_DIR%\insectos.onnx
    echo Copia ahi insectos.onnx y etiquetas.json de la corrida ^(ver CLAUDE.md^).
    echo.
    pause
    exit /b 1
)

echo Iniciando el servidor en http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
.venv\Scripts\python -m uvicorn backend.app:app_produccion --factory --port 8000
```

- [ ] **Step 5: Probar el arranque de un clic**

Cerrar todas las terminales, doble clic en `iniciar.bat`. Esperado: se abre el navegador, carga la interfaz, se puede subir una foto y obtener resultado. Probar también **renombrando temporalmente** `modelo/v4_convnext_t_288/insectos.onnx` para confirmar que el mensaje de error es claro y no un rastro de excepción de Python.

- [ ] **Step 6: Ampliar `README.md`**

Añadir al final:

```markdown
## Ejecutar el prototipo

Doble clic en `iniciar.bat`, o a mano:

```powershell
.venv\Scripts\python -m uvicorn backend.app:app_produccion --factory --port 8000
```

Abrir http://127.0.0.1:8000

### Desarrollo del frontend

```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173, con recarga en caliente
npm run prueba   # pruebas del frontend
```

### Artefactos que el prototipo necesita

| Archivo | Lo produce |
| --- | --- |
| `modelo/v4_convnext_t_288/insectos.onnx` | Cuaderno de Colab, paso 7 (Plan 02); no se versiona |
| `modelo/v4_convnext_t_288/etiquetas.json` | Cuaderno de Colab, paso 6 (Plan 02) |
| `bd/bd_insectos.sqlite` | `python -m pipeline.bd` (Plan 01) |

Sin la base de datos el sistema predice igual, pero no muestra ficha biológica.

## Pruebas

```powershell
.venv\Scripts\python -m pytest        # backend y pipeline
cd frontend && npm run prueba          # frontend
```
```

- [ ] **Step 7: Correr la suite completa de los tres planes**

```powershell
.venv\Scripts\python -m pytest -v
cd frontend
npm run prueba
cd ..
```

Esperado: 201 pruebas de Python (81 + 75 + 45) y 24 de JavaScript.

- [ ] **Step 8: Commit**

```powershell
git add iniciar.bat README.md backend/app.py
git commit -m "feat: arranque de un clic y documentacion de despliegue"
```

---

## Estado al terminar los tres planes

Un repositorio que, desde la ontología de clases, produce y sirve el sistema completo:

```
clases.yaml → censo → descarga → curación → splits → entrenamiento
            → insectos.onnx → API → interfaz web → ficha biológica
```

Con los tres productos que exigen los documentos del proyecto cubiertos: banco de imágenes (`datos/curado/`), base de datos biológica (`bd/bd_insectos.sqlite`) y prototipo web de consulta, más el informe de métricas medido contra fotos de campo.

## Lo que queda fuera, a propósito

- **App móvil nativa y modo offline.** La hoja de alcance los dejó sujetos a decisión de la Facultad. La interfaz web es responsiva y funciona en el navegador de un teléfono, que cubre el caso de uso sin abrir un proyecto nuevo.
- **Autenticación y multiusuario.** El prototipo es de consulta pública; no hay datos personales ni operaciones de escritura.
- **Despliegue en la nube.** El sistema corre en una laptop con `iniciar.bat`. Si la Facultad quiere una URL pública, es una tarea posterior de infraestructura, no de desarrollo.
- **Identificación de plagas por cultivo.** Fase 2, proyecto distinto (§2 del diseño).
