# Rediseño del frontend INSECTIA: plan de implementación

> **Para trabajadores agénticos:** SUB-SKILL REQUERIDA: usar superpowers:subagent-driven-development (recomendado) o superpowers:executing-plans para implementar este plan tarea por tarea. Los pasos usan casillas (`- [ ]`) para el seguimiento.

**Goal:** reemplazar el prototipo de una sola pantalla por la interfaz de INSECTIA, con dos páginas (presentación en `/` e identificación en `/identificar/`), la marca del usuario, un catálogo de familias con fotos reales y todos los estados del flujo de identificación.

**Architecture:**
- Dos entradas HTML de Vite comparten componentes en `frontend/src/compartido/`.
- Dos scripts de `pipeline/` generan el contenido estático que el frontend lee de `frontend/public/`:
  - `marca_web.py`: logo, símbolo, favicon y manifiesto, a partir de la hoja de marca;
  - `catalogo_web.py`: fotos y datos del catálogo, y la demostración con resultados reales del modelo.
- La API no cambia. FastAPI ya sirve `frontend/dist`, y con él también `/identificar/`.

**Tech Stack:** React 19, Vite 8, Vitest 5 y Testing Library; `@fontsource` (Lexend y Atkinson Hyperlegible Next); Python 3.12, Pillow 12, NumPy, PyYAML, onnxruntime y pytest.

**Spec:** `docs/superpowers/specs/2026-09-24-frontend-insectia-design.md`. Contexto de producto: `PRODUCT.md`.

## Global Constraints

- **Todo en español:** código, nombres, comentarios, textos visibles y commits. Los commits terminan con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Nunca nombres taxonómicos literales en `pipeline/*.py`.** Salen de `ontologia/clases.yaml`, y `tests/test_ontologia.py::test_ningun_modulo_escribe_nombres_de_clase_literales` lo verifica.
- **Las pruebas de Python no usan red ni pesos preentrenados, y cada una tarda menos de 5 s.** Se corren con `.venv\Scripts\python -m pytest`.
- **Las pruebas del frontend se corren desde `frontend/`** con `npm run prueba`.
- **Se trabaja sobre `main`,** como indica `CLAUDE.md`.
- **Paleta de la marca:** Verde Amazónico #0B5E3B, Verde Selva #4CAF50, Verde Lima #A3D977, Azul Petróleo #0F3D3E, Amarillo Amazonía #F4B400, Gris Oscuro #2E2E2E.
- **Contraste WCAG AA:** texto ≥ 4.5:1 y texto grande ≥ 3:1. Verde Selva, Verde Lima y Amarillo nunca van como texto sobre fondo claro.
- **La confianza nunca se comunica solo con color:** siempre lleva el porcentaje escrito y, en la familia, la etiqueta "Afirmada" o "Revisar con especialista".
- **Zonas táctiles de al menos 44 × 44 px,** foco visible y `prefers-reduced-motion` respetado.
- **No se inventan cifras ni capacidades:** no hay especie, SENASA, IIAP, manejo integrado de plagas ni GPS. Las cifras salen de `modelo/<corrida>/evaluacion.json` y de `docs/desempeno_por_clase_v4.md`, a través del script.
- **Toda foto mostrada lleva su crédito y licencia.**
- **No se incluyen nombres de personas en la interfaz,** por decisión del usuario.
- **El frontend no decide taxonomía ni umbrales:** muestra lo que dicen la API y `catalogo.json`.
- **Sin dependencias de internet en tiempo de ejecución:** las fuentes van locales con `@fontsource`.
- **Fuera de alcance:** cambiar la API o el modelo, usuarios y sesiones, modo sin conexión, especie, mapas de calor y PDF.

## Review Focus

1. **`/identificar` sin barra final** (un enlace escrito a mano): tiene que llegar a la página, no a un 404. La prueba va en la tarea 4.
2. **`catalogo.json` que no carga** (el script no se corrió, o el servidor está caído): la portada tiene que funcionar y el catálogo tiene que decir qué pasó. La prueba va en la tarea 7.
3. **Foto sin atribución en el CSV:** la tarjeta muestra "Autor no registrado" y la licencia, nunca un crédito vacío. La prueba va en la tarea 3.
4. **Importancia escrita a mano en la base** ("Plaga", "Benéfico - polinizador", con mayúsculas y tildes): el chip tiene que reconocerla. Hoy `Ficha.jsx` compara con `'plaga'` exacto y nunca marca una plaga real. La prueba va en la tarea 5.
5. **Foto de ejemplo que no carga** (archivo ausente o servidor caído): mensaje claro y "Reintentar", nunca una pantalla colgada en "Identificando…". La prueba va en la tarea 6.

## Ajustes a la especificación, decididos al planificar

- **Panel de fichas:** es un `div` con `role="dialog"` y `aria-modal`, en lugar de `<dialog>`. jsdom no implementa `showModal`, y el comportamiento es el mismo: se cierra con Escape y con el fondo, el foco va al botón Cerrar al abrir y vuelve al botón que lo abrió al cerrar.
- **Logo y símbolo:** se exportan solo a 2x (96 px y 256 px de alto), y el navegador los reduce. La especificación pedía 1x y 2x; una sola versión alcanza para una cabecera de 44 px y reduce archivos.
- **`orden_nombre_comun`:** no se repite en cada clase. Va una vez por orden, en la lista `ordenes` de `catalogo.json`.

La marca "provisional" (las 5 familias de Hemiptera y Coccinellidae) hoy existe solo como comentario en `clases.yaml`. Como `pipeline/` no puede tener nombres escritos en el código, la tarea 1 agrega el campo `provisional: true` a esas familias y a la clase `Familia`. No cambia ninguna clase ni el orden de las etiquetas, así que el modelo sigue siendo válido.

---

## Estructura de archivos

```
ontologia/clases.yaml                       T1  campo provisional en 6 familias
pipeline/ontologia.py                       T1  Familia.provisional
pipeline/marca_web.py                       T2  logo, símbolo, favicon y manifiesto
pipeline/catalogo_web.py                    T3  catalogo.json, fotos y demostracion.json
frontend/catalogo_preferencias.yaml         T3  fotos fijadas a mano
frontend/public/
  favicon.ico, manifest.webmanifest         T2
  marca/*.webp|png                          T2
  catalogo/catalogo.json                    T3
  catalogo/demostracion.json                T3
  catalogo/fotos/*.webp                     T3
  catalogo/demo/*.webp                      T3
frontend/index.html                         T4  entrada de la presentación
frontend/identificar/index.html             T4  entrada de la identificación
frontend/vite.config.js                     T4  dos entradas
frontend/src/compartido/
  base.css                                  T4  fuentes, tokens y componentes base
  api.js                                    T4  (movido desde src/api.js)
  datos.js                                  T4  cargarCatalogo, cargarDemostracion, archivoDesdeRuta
  Cabecera.jsx, Pie.jsx                     T4
  importancia.js                            T5  clasificarImportancia
  BarraConfianza.jsx                        T5
  Ficha.jsx, Resultado.jsx                  T5  (movidos y rediseñados)
frontend/src/paginas/identificar/
  main.jsx                                  T4 (mínimo) → T6
  Identificar.jsx                           T4 (mínimo) → T6
  ZonaFoto.jsx, Consejos.jsx, Ejemplos.jsx  T6
  identificar.css                           T6
frontend/src/paginas/inicio/
  main.jsx                                  T4 (mínimo) → T7
  Inicio.jsx                                T4 (mínimo) → T7
  Portada.jsx, ComoFunciona.jsx, Desempeno.jsx,
  Catalogo.jsx, TarjetaClase.jsx, PanelFichas.jsx   T7
  inicio.css                                T7
frontend/pruebas/                           una prueba por componente (ver cada tarea)
tests/test_marca_web.py                     T2
tests/test_catalogo_web.py                  T3
tests/test_ontologia.py, tests/test_app.py  T1, T4
```

**Se borran:**
- en la tarea 4: `frontend/src/App.jsx`, `frontend/src/main.jsx`, `frontend/src/estilos.css`, `frontend/src/componentes/Explorador.jsx`, `frontend/pruebas/Explorador.test.jsx` y `frontend/public/favicon.svg`;
- en la tarea 5: `frontend/src/componentes/Ficha.jsx` y `Resultado.jsx`;
- en la tarea 6: `frontend/src/componentes/SubirFoto.jsx` y `frontend/pruebas/SubirFoto.test.jsx`.

---

## Task 1: Campo `provisional` en la ontología

**Files:**
- Modify: `ontologia/clases.yaml` (familias de Hemiptera y Coccinellidae)
- Modify: `pipeline/ontologia.py:24-30` (clase `Familia`) y `:132-138` (construcción)
- Test: `tests/test_ontologia.py`

**Interfaces:**
- Produces: `Familia.provisional: bool` (por defecto `False`), que lee `catalogo_web.py` en la tarea 3.

- [ ] **Step 1: Escribir las pruebas que fallan**

Agregar al final de `tests/test_ontologia.py`:

```python
YAML_CON_PROVISIONAL = """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: A
    inat_taxon_id: 1
    familias:
      - {nombre: A1, inat_taxon_id: 11, provisional: true}
      - {nombre: A2, inat_taxon_id: 12}
"""


def test_familia_provisional_se_lee_del_yaml(tmp_path: Path):
    ruta = tmp_path / "clases.yaml"
    ruta.write_text(YAML_CON_PROVISIONAL, encoding="utf-8")
    familias = cargar_ontologia(ruta).ordenes[0].familias
    assert familias[0].provisional is True
    assert familias[1].provisional is False


def test_la_ontologia_real_marca_seis_familias_provisionales():
    """Las 5 de Hemiptera y Coccinellidae, pendientes de confirmar con la Facultad."""
    onto = cargar_ontologia(Path("ontologia/clases.yaml"))
    provisionales = [f for o in onto.ordenes for f in o.familias if f.provisional]
    assert len(provisionales) == 6
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run: `.venv\Scripts\python -m pytest tests/test_ontologia.py -q -k provisional`
Expected: 2 failed, con `AttributeError: 'Familia' object has no attribute 'provisional'`.

- [ ] **Step 3: Implementar**

En `pipeline/ontologia.py`, dentro de `class Familia`, después de `importancia: str = ""`:

```python
    # Entra al sistema pendiente de confirmación de la entomóloga. Solo informa
    # a la interfaz: no cambia la clase ni el orden de las etiquetas.
    provisional: bool = False
```

En la construcción de `Familia(...)` (hoy `importancia=fam.get("importancia", ""),`), agregar la línea siguiente:

```python
                    provisional=bool(fam.get("provisional", False)),
```

En `ontologia/clases.yaml`:
- Agregar `, provisional: true` antes de la `}` en estas 6 líneas: Pentatomidae, Coreidae, Reduviidae, Cicadellidae y Aphididae (bajo Hemiptera) y Coccinellidae (bajo Coleoptera). Por ejemplo:

```yaml
      - {nombre: Pentatomidae, inat_taxon_id: 47742, nombre_comun: chinches hediondas, provisional: true}  # ficha
```

- Agregar al comentario de cabecera, después de la línea que menciona Coccinellidae:

```yaml
#   El campo `provisional: true` marca esas familias para la interfaz; no cambia
#   las clases ni el orden de las etiquetas, así que no invalida el modelo.
```

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run: `.venv\Scripts\python -m pytest tests/test_ontologia.py -q`
Expected: todas pasan.

Run: `.venv\Scripts\python -c "from pathlib import Path; from pipeline.ontologia import cargar_ontologia; from pipeline.etiquetas import cargar_espacio; o=cargar_ontologia(Path('ontologia/clases.yaml')); e=cargar_espacio(Path('modelo/v4_convnext_t_288/etiquetas.json')); print(o.nombres_familias()==list(e.familias) or sorted(o.nombres_familias())==sorted(e.familias))"`
Expected: `True`. Las clases no cambiaron.

- [ ] **Step 5: Commit**

```bash
git add ontologia/clases.yaml pipeline/ontologia.py tests/test_ontologia.py
git commit -m "Ontología: marcar las familias provisionales como dato" -m "La interfaz necesita mostrar qué familias siguen pendientes de confirmar con la Facultad. Hasta ahora eso vivía solo en comentarios del YAML, y pipeline/ no puede tener nombres de clase escritos en el código. No cambia clases ni etiquetas." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 2: Recursos de marca (`pipeline/marca_web.py`)

**Files:**
- Create: `pipeline/marca_web.py`
- Test: `tests/test_marca_web.py`
- Create (generados y versionados): `frontend/public/favicon.ico`, `frontend/public/manifest.webmanifest`, `frontend/public/marca/{logo-horizontal.webp, logo-horizontal.png, simbolo.webp, simbolo.png, simbolo-claro.webp, apple-touch-icon.png, icon-192.png, icon-512.png}`

**Interfaces:**
- Produces:
  - `quitar_fondo(img: Image.Image, fondo: np.ndarray | None = None) -> Image.Image` (RGBA)
  - `aclarar_oscuros(img: Image.Image) -> Image.Image`
  - `generar(hoja: Path, publico: Path, caja_simbolo=..., caja_palabra=...) -> list[Path]`
  - Rutas públicas que usa el frontend (tareas 4 a 7): `/marca/logo-horizontal.webp`, `/marca/simbolo.webp`, `/marca/simbolo-claro.webp`, `/favicon.ico`, `/marca/apple-touch-icon.png`, `/marca/icon-192.png` y `/manifest.webmanifest`.

**Por qué no se usan `logo_1.png` ni `favicon.png`:** en ellos, el 94 % y el 99.8 % de los píxeles son semitransparentes, restos de un recorte de fondo, y se ven desteñidos sobre la página. `imagen_1.png` (la hoja de marca) tiene el logo sobre un fondo plano de (252, 252, 250).

**Cajas medidas en `imagen_1.png`:**
- símbolo: x 337–818, y 119–549;
- letras "INSECTIA": x 144–1013, y 577–707;
- bajada: desde y 742.

Se usan con 8 px de margen.

**Aclarado para fondo oscuro:** las partes Azul Petróleo del símbolo (el insecto y el encuadre) son de un verde azulado con G ≈ B, por ejemplo (0, 56, 56). Las hojas son verdes, con G mucho mayor que B, por ejemplo (16, 112, 56). El criterio "G − B < 16, G < 100 y R < 50" separa ambas.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_marca_web.py`:

```python
import json

import numpy as np
from PIL import Image

from pipeline.marca_web import aclarar_oscuros, generar, quitar_fondo

FONDO = (252, 252, 250)
PETROLEO = (0, 56, 56)
VERDE = (16, 112, 56)


def hoja_sintetica(ruta):
    """Una hoja de marca diminuta: fondo plano, un 'símbolo' y una 'palabra'."""
    img = Image.new("RGB", (300, 260), FONDO)
    a = np.asarray(img).copy()
    a[20:120, 100:200] = PETROLEO        # símbolo, parte oscura
    a[60:120, 100:140] = VERDE           # símbolo, hoja verde
    a[150:190, 40:260] = PETROLEO        # palabra
    Image.fromarray(a).save(ruta)
    return (90, 10, 210, 130), (30, 140, 270, 200)


def test_quitar_fondo_deja_el_fondo_transparente_y_el_dibujo_opaco():
    img = Image.new("RGB", (40, 40), FONDO)
    a = np.asarray(img).copy()
    a[10:30, 10:30] = PETROLEO
    salida = np.asarray(quitar_fondo(Image.fromarray(a)))
    assert salida[0, 0, 3] == 0
    assert salida[20, 20, 3] == 255
    assert tuple(salida[20, 20, :3]) == PETROLEO


def test_quitar_fondo_deja_semitransparente_solo_el_borde_tenue():
    """Un píxel apenas teñido (el borde más externo) queda a medias; uno con
    tinta clara pero saturada, como el verde lima de las alas, queda opaco."""
    tenue = tuple(round(0.05 * p + 0.95 * f) for p, f in zip(PETROLEO, FONDO))
    lima = (163, 217, 119)
    img = Image.new("RGB", (30, 30), FONDO)
    a = np.asarray(img).copy()
    a[5:15, 5:15] = tenue
    a[16:26, 16:26] = lima
    salida = np.asarray(quitar_fondo(Image.fromarray(a)))
    assert 0 < salida[10, 10, 3] < 255
    assert salida[20, 20, 3] == 255


def test_aclarar_oscuros_cambia_el_petroleo_y_respeta_el_verde():
    rgba = np.zeros((1, 2, 4), dtype=np.uint8)
    rgba[0, 0] = (*PETROLEO, 255)
    rgba[0, 1] = (*VERDE, 255)
    salida = np.asarray(aclarar_oscuros(Image.fromarray(rgba, "RGBA")))
    assert tuple(salida[0, 0, :3]) == (255, 255, 255)
    assert tuple(salida[0, 1, :3]) == VERDE


def test_generar_escribe_todos_los_archivos(tmp_path):
    hoja = tmp_path / "hoja.png"
    caja_simbolo, caja_palabra = hoja_sintetica(hoja)
    publico = tmp_path / "public"
    rutas = generar(hoja, publico, caja_simbolo, caja_palabra)
    nombres = {r.relative_to(publico).as_posix() for r in rutas}
    assert {
        "favicon.ico", "manifest.webmanifest",
        "marca/logo-horizontal.webp", "marca/logo-horizontal.png",
        "marca/simbolo.webp", "marca/simbolo.png", "marca/simbolo-claro.webp",
        "marca/apple-touch-icon.png", "marca/icon-192.png", "marca/icon-512.png",
    } <= nombres
    assert all(r.exists() for r in rutas)
    with Image.open(publico / "marca" / "icon-512.png") as icono:
        assert icono.size == (512, 512)
    with Image.open(publico / "marca" / "logo-horizontal.png") as logo:
        assert logo.height == 96 and logo.width > logo.height
        assert logo.getchannel("A").getextrema()[0] == 0   # tiene transparencia real
    with Image.open(publico / "favicon.ico") as ico:
        assert {(16, 16), (32, 32), (48, 48)} <= set(ico.info["sizes"])
    manifiesto = json.loads((publico / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifiesto["name"] == "INSECTIA"
    assert manifiesto["start_url"] == "/identificar/"
    assert {i["sizes"] for i in manifiesto["icons"]} == {"192x192", "512x512"}
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run: `.venv\Scripts\python -m pytest tests/test_marca_web.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'pipeline.marca_web'`.

- [ ] **Step 3: Implementar `pipeline/marca_web.py`**

```python
"""Recursos de marca para la web, a partir de la hoja de marca.

`logo_1.png` y `favicon.png` traen el fondo mal quitado: casi todo el dibujo
quedó semitransparente y se ve desteñido sobre la página. La hoja de marca
(`imagen_1.png`) tiene el logo sobre un fondo plano casi blanco. De ahí se
recorta y se quita el fondo según la distancia de cada píxel a ese color.

    python -m pipeline.marca_web --hoja ../imagenes_web/imagen_1.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# Cajas (x0, y0, x1, y1) medidas en imagen_1.png, con 8 px de margen.
CAJA_SIMBOLO = (329, 111, 827, 558)
CAJA_PALABRA = (136, 569, 1022, 716)

# Distancia L1 (suma de las diferencias RGB) al color de fondo: por debajo de
# DISTANCIA_FONDO el píxel es fondo; por encima de DISTANCIA_TINTA es dibujo
# opaco; entre ambas es un borde mezclado.
DISTANCIA_FONDO = 8
DISTANCIA_TINTA = 60

PETROLEO = (15, 61, 62, 255)
ALTO_LOGO = 96        # 2x para una cabecera de 48 px
ALTO_SIMBOLO = 256


def color_de_fondo(img: Image.Image) -> np.ndarray:
    """Mediana de las cuatro esquinas del recorte: el fondo plano de la hoja."""
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    esquinas = np.concatenate([a[:8, :8], a[:8, -8:], a[-8:, :8], a[-8:, -8:]])
    return np.median(esquinas.reshape(-1, 3), axis=0)


def quitar_fondo(img: Image.Image, fondo: np.ndarray | None = None) -> Image.Image:
    rgb = np.asarray(img.convert("RGB"), dtype=np.float64)
    if fondo is None:
        fondo = color_de_fondo(img)
    distancia = np.abs(rgb - fondo).sum(axis=2)
    # Solo el borde más tenue (distancia entre 8 y 60) queda semitransparente;
    # todo lo demás es dibujo opaco. Así el logo conserva sus colores exactos y
    # el antialias de la hoja, que tras reducir a la mitad queda bajo un píxel.
    alfa = np.clip(
        (distancia - DISTANCIA_FONDO) / (DISTANCIA_TINTA - DISTANCIA_FONDO), 0.0, 1.0
    )
    color = np.where(alfa[..., None] > 0, rgb, 0.0)
    rgba = np.dstack([color, alfa * 255]).round().astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def recortar_a_tinta(img: Image.Image) -> Image.Image:
    caja = img.getchannel("A").getbbox()
    return img.crop(caja) if caja else img


def aclarar_oscuros(img: Image.Image) -> Image.Image:
    """Vuelve blancas las partes Azul Petróleo, para usar el símbolo sobre ese color.

    El petróleo es un verde azulado (G ≈ B); las hojas son verdes (G mucho mayor
    que B). Separarlos por el tono deja las hojas intactas.
    """
    rgba = np.asarray(img.convert("RGBA")).astype(np.int32)
    r, g, b, a = rgba[..., 0], rgba[..., 1], rgba[..., 2], rgba[..., 3]
    petroleo = (g - b < 16) & (g < 100) & (r < 50) & (a > 0)
    rgba[petroleo, :3] = 255
    return Image.fromarray(rgba.astype(np.uint8), "RGBA")


def a_altura(img: Image.Image, alto: int) -> Image.Image:
    ancho = round(img.width * alto / img.height)
    return img.resize((ancho, alto), Image.LANCZOS)


def logo_horizontal(simbolo: Image.Image, palabra: Image.Image) -> Image.Image:
    """Símbolo a la izquierda y "INSECTIA" a la derecha, para la cabecera."""
    alto = simbolo.height
    palabra = a_altura(palabra, round(alto * 0.42))
    hueco = round(alto * 0.12)
    lienzo = Image.new("RGBA", (simbolo.width + hueco + palabra.width, alto), (0, 0, 0, 0))
    lienzo.alpha_composite(simbolo, (0, 0))
    lienzo.alpha_composite(palabra, (simbolo.width + hueco, (alto - palabra.height) // 2))
    return lienzo


def icono(simbolo_claro: Image.Image, lado: int) -> Image.Image:
    """El símbolo aclarado sobre un cuadrado redondeado Azul Petróleo."""
    lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    ImageDraw.Draw(lienzo).rounded_rectangle(
        (0, 0, lado - 1, lado - 1), radius=round(lado * 0.22), fill=PETROLEO
    )
    interior = round(lado * 0.78)
    simbolo = simbolo_claro.copy()
    simbolo.thumbnail((interior, interior), Image.LANCZOS)
    lienzo.alpha_composite(simbolo, ((lado - simbolo.width) // 2, (lado - simbolo.height) // 2))
    return lienzo


def _guardar(img: Image.Image, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.suffix == ".webp":
        img.save(ruta, "WEBP", quality=90, method=6)
    else:
        img.save(ruta, optimize=True)


def generar(
    hoja: Path,
    publico: Path,
    caja_simbolo: tuple[int, int, int, int] = CAJA_SIMBOLO,
    caja_palabra: tuple[int, int, int, int] = CAJA_PALABRA,
) -> list[Path]:
    with Image.open(hoja) as original:
        simbolo = recortar_a_tinta(quitar_fondo(original.crop(caja_simbolo)))
        palabra = recortar_a_tinta(quitar_fondo(original.crop(caja_palabra)))
    claro = aclarar_oscuros(simbolo)
    horizontal = a_altura(logo_horizontal(simbolo, palabra), ALTO_LOGO)

    marca = Path(publico) / "marca"
    salidas = {
        marca / "logo-horizontal.webp": horizontal,
        marca / "logo-horizontal.png": horizontal,
        marca / "simbolo.webp": a_altura(simbolo, ALTO_SIMBOLO),
        marca / "simbolo.png": a_altura(simbolo, ALTO_SIMBOLO),
        marca / "simbolo-claro.webp": a_altura(claro, ALTO_SIMBOLO),
        marca / "apple-touch-icon.png": icono(claro, 180),
        marca / "icon-192.png": icono(claro, 192),
        marca / "icon-512.png": icono(claro, 512),
    }
    for ruta, img in salidas.items():
        _guardar(img, ruta)

    ico = Path(publico) / "favicon.ico"
    icono(claro, 256).save(ico, sizes=[(16, 16), (32, 32), (48, 48)])

    manifiesto = Path(publico) / "manifest.webmanifest"
    manifiesto.write_text(
        json.dumps(
            {
                "name": "INSECTIA",
                "short_name": "INSECTIA",
                "description": "Identificación de órdenes y familias de insectos de la Amazonía peruana",
                "lang": "es",
                "start_url": "/identificar/",
                "display": "standalone",
                "background_color": "#f6f8f5",
                "theme_color": "#0f3d3e",
                "icons": [
                    {"src": "/marca/icon-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "/marca/icon-512.png", "sizes": "512x512", "type": "image/png"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return [*salidas, ico, manifiesto]


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera los recursos de marca para la web")
    parser.add_argument("--hoja", required=True, help="imagen_1.png, la hoja de marca")
    parser.add_argument("--publico", default="frontend/public")
    args = parser.parse_args()
    for ruta in generar(Path(args.hoja), Path(args.publico)):
        print(f"{ruta}  {ruta.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run: `.venv\Scripts\python -m pytest tests/test_marca_web.py tests/test_ontologia.py -q`
Expected: todas pasan, incluida la de nombres literales.

- [ ] **Step 5: Generar con la hoja real y revisar a ojo**

Run: `.venv\Scripts\python -m pipeline.marca_web --hoja ../imagenes_web/imagen_1.png`
Expected: 10 rutas. Cada `.webp` o `.png` de `marca/` pesa menos de 60 KB, y `icon-512.png` menos de 120 KB.

Abrir con la herramienta Read `frontend/public/marca/logo-horizontal.png`, `simbolo-claro.webp` e `icon-512.png`, y confirmar tres cosas:
- el logo no tiene halo claro alrededor;
- en el símbolo claro, el insecto y el encuadre son blancos y las hojas siguen verdes;
- el ícono se lee sobre el cuadrado petróleo.

Si queda halo, subir `DISTANCIA_FONDO` a 12 y regenerar.

Run: `.venv\Scripts\python -c "from PIL import Image; import numpy as np; a=np.asarray(Image.open('frontend/public/marca/logo-horizontal.png'))[...,3]; print('opaco', round((a==255).mean(),3), 'transparente', round((a==0).mean(),3), 'semi', round(((a>0)&(a<255)).mean(),3))"`
Expected: `semi` por debajo de 0.08, solo bordes. El `logo_1.png` original tenía 0.52.

- [ ] **Step 6: Commit**

```bash
git rm frontend/public/favicon.svg
git add pipeline/marca_web.py tests/test_marca_web.py frontend/public/favicon.ico frontend/public/manifest.webmanifest frontend/public/marca
git commit -m "Marca: logo, símbolo y favicon limpios a partir de la hoja de marca" -m "logo_1.png y favicon.png tenían el 94 % y el 99.8 % de los píxeles semitransparentes por un recorte de fondo defectuoso. Se recorta de imagen_1.png, que tiene fondo plano, y se quita el fondo por distancia a ese color. El favicon lleva el símbolo con el petróleo aclarado sobre un cuadrado petróleo." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 3: Catálogo y demostración (`pipeline/catalogo_web.py`)

**Files:**
- Create: `pipeline/catalogo_web.py`
- Create: `frontend/catalogo_preferencias.yaml`
- Test: `tests/test_catalogo_web.py`
- Create (generados y versionados): `frontend/public/catalogo/catalogo.json`, `frontend/public/catalogo/demostracion.json`, `frontend/public/catalogo/fotos/*.webp` (44) y `frontend/public/catalogo/demo/*.webp` (4)

**Interfaces:**
- Consumes: `cargar_ontologia(ruta) -> Ontologia` (con `Familia.provisional`, de la tarea 1); `backend.servicio.ServicioInsectos(ruta_onnx, ruta_etiquetas).predecir_bytes(bytes) -> Prediccion`; `backend.app.CORRIDA_VIGENTE`; `pipeline.inferencia.UMBRAL_FAMILIA`.
- Produces: `catalogo.json` y `demostracion.json`, con estas formas (las leen las tareas 6 y 7):

```json
{
  "corrida": "v4_convnext_t_288",
  "metricas": {"n_prueba": 5165, "exactitud_familia": 0.9216, "top3_familia": 0.958,
               "f1_orden": 0.935, "f1_familia": 0.921, "umbral": 0.7,
               "responde": 0.94, "acierta_cuando_responde": 0.955},
  "ordenes": [{"nombre": "…", "nombre_comun": "…", "tiene_familias": true}],
  "clases": [{"id": "familia-…", "tipo": "familia", "nombre": "…", "nombre_comun": "…",
              "orden": "…", "provisional": false, "f1": 0.92, "fotos_entrenamiento": 610,
              "foto": {"archivo": "/catalogo/fotos/familia-….webp", "ancho": 640, "alto": 480,
                       "credito": "(c) …", "licencia": "cc-by", "url_origen": "https://…"}}]
}
```

```json
{
  "principal": Ejemplo, "incierto": Ejemplo, "ejemplos": [Ejemplo, Ejemplo, Ejemplo, Ejemplo],
}
```

Cada `Ejemplo` tiene esta forma:

```json
{"archivo": "/catalogo/demo/<id>.webp", "credito": "…", "licencia": "…", "url_origen": "…",
 "real": {"orden": "…", "familia": "…"},
 "prediccion": {"orden": "…", "confianza_orden": 0.99, "familia": "…", "confianza_familia": 0.98,
                "familia_incierta": false, "top_familias": [{"familia": "…", "confianza": 0.98}]}}
```

- Para las clases de tipo `orden`, `id` es `orden-<Nombre>`, `orden` es el propio nombre y `f1` es el F1 de orden.
- `ejemplos` trae 3 afirmados de órdenes distintos y después el incierto.

- [ ] **Step 1: Escribir las pruebas que fallan**

`tests/test_catalogo_web.py`:

```python
from pathlib import Path

import pytest
from PIL import Image

from pipeline.catalogo_web import (
    clases_del_catalogo,
    credito,
    elegir_demostracion,
    elegir_foto,
    leer_desempeno,
    optimizar_foto,
    rango_licencia,
    verificar_origen,
)
from pipeline.ontologia import cargar_ontologia

YAML = """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: OrdA
    inat_taxon_id: 1
    nombre_comun: los A
    familias:
      - {nombre: FamA1, inat_taxon_id: 11, nombre_comun: uno}
      - {nombre: FamA2, inat_taxon_id: 12, provisional: true}
  - nombre: OrdB
    inat_taxon_id: 2
    familias:
      - {nombre: FamB1, inat_taxon_id: 21}
  - nombre: OrdC
    inat_taxon_id: 3
    nombre_comun: los C
    familias: []
"""

DESEMPENO = """# Desempeño por clase — prueba

## Órdenes

| Clase | F1 | Imágenes | Confusión principal |
| --- | ---: | ---: | --- |
| OrdA | 0.91 | 100 | OrdB (3) |
| OrdC | 0.87 | 50 | OrdA (2) |

## Familias

| Clase | F1 | Imágenes | Confusión principal |
| --- | ---: | ---: | --- |
| FamA1 | 0.95 | 40 | FamA2 (1) |
| FamA2 | 0.80 | 30 | — |

## Cobertura contra confianza (familias)

| Umbral | Responde | Acierta cuando responde |
| --- | ---: | ---: |
| 0.0 | 100% | 92.1% |
| 0.7 | 94% | 95.5% |
"""


@pytest.fixture
def onto(tmp_path: Path):
    ruta = tmp_path / "clases.yaml"
    ruta.write_text(YAML, encoding="utf-8")
    return cargar_ontologia(ruta)


def fila(archivo, orden, familia="", licencia="cc-by-nc", atribucion="(c) Ana"):
    return {"archivo": archivo, "orden": orden, "familia": familia, "licencia": licencia,
            "atribucion": atribucion, "url": f"https://x/{archivo}"}


def test_rango_licencia_prefiere_las_libres():
    assert rango_licencia("cc0") < rango_licencia("CC-BY") < rango_licencia("cc-by-sa")
    assert rango_licencia("cc-by-sa") < rango_licencia("cc-by-nc") == rango_licencia("")


def test_credito_sin_atribucion_no_queda_vacio():
    assert credito(fila("a.jpg", "OrdA", atribucion="  ")) == "Autor no registrado"
    assert credito(fila("a.jpg", "OrdA")) == "(c) Ana"


def test_leer_desempeno_toma_f1_y_cobertura():
    datos = leer_desempeno(DESEMPENO)
    assert datos["ordenes"] == {"OrdA": 0.91, "OrdC": 0.87}
    assert datos["familias"] == {"FamA1": 0.95, "FamA2": 0.80}
    assert datos["cobertura"][0.7] == pytest.approx((0.94, 0.955))


def test_elegir_foto_prefiere_licencia_libre_y_despues_la_mas_grande():
    filas = [
        fila("chica_libre.jpg", "OrdA", "FamA1", "cc0"),
        fila("grande_libre.jpg", "OrdA", "FamA1", "cc0"),
        fila("enorme_nc.jpg", "OrdA", "FamA1", "cc-by-nc"),
    ]
    areas = {"chica_libre.jpg": 100, "grande_libre.jpg": 900, "enorme_nc.jpg": 10_000}
    assert elegir_foto(filas, areas.__getitem__)["archivo"] == "grande_libre.jpg"


def test_clases_del_catalogo_incluye_familias_y_ordenes_sin_familias(onto):
    conteos = {"FamA1": 7, "FamA2": 3, "FamB1": 5, "orden:OrdC": 9}
    clases = clases_del_catalogo(onto, leer_desempeno(DESEMPENO), conteos)
    assert [c["id"] for c in clases] == ["familia-FamA1", "familia-FamA2", "familia-FamB1", "orden-OrdC"]
    a2 = clases[1]
    assert a2["provisional"] is True and a2["orden"] == "OrdA" and a2["f1"] == 0.80
    c = clases[3]
    assert c["tipo"] == "orden" and c["orden"] == "OrdC" and c["f1"] == 0.87
    assert c["nombre_comun"] == "los C" and c["fotos_entrenamiento"] == 9
    assert clases[2]["f1"] is None      # sin fila en el informe: no se inventa


def test_optimizar_foto_reduce_a_webp(tmp_path: Path):
    origen = tmp_path / "grande.jpg"
    Image.new("RGB", (1600, 1200), (40, 120, 60)).save(origen)
    destino = tmp_path / "salida" / "x.webp"
    ancho, alto = optimizar_foto(origen, destino)
    assert (ancho, alto) == (640, 480)
    with Image.open(destino) as img:
        assert img.format == "WEBP"


def pred(orden, familia, conf=0.97, incierta=False):
    return {"orden": orden, "confianza_orden": 0.99, "familia": familia, "confianza_familia": conf,
            "familia_incierta": incierta, "top_familias": [{"familia": familia, "confianza": conf}]}


def test_elegir_demostracion_da_tres_afirmados_de_ordenes_distintos_y_un_incierto():
    entradas = [
        ({"tipo": "familia", "nombre": "FamA1", "orden": "OrdA"}, [fila("a1.jpg", "OrdA", "FamA1")]),
        ({"tipo": "familia", "nombre": "FamA2", "orden": "OrdA"}, [fila("a2.jpg", "OrdA", "FamA2")]),
        ({"tipo": "familia", "nombre": "FamB1", "orden": "OrdB"}, [fila("b1.jpg", "OrdB", "FamB1")]),
        ({"tipo": "familia", "nombre": "FamD1", "orden": "OrdD"}, [fila("d1.jpg", "OrdD", "FamD1")]),
        ({"tipo": "familia", "nombre": "FamE1", "orden": "OrdE"}, [fila("e1.jpg", "OrdE", "FamE1")]),
    ]
    respuestas = {
        "a1.jpg": pred("OrdA", "FamA1"),
        "a2.jpg": pred("OrdA", "FamA1", 0.4, True),        # incierta, orden correcto
        "b1.jpg": pred("OrdB", "FamB1"),
        "d1.jpg": pred("OrdD", "FamD1", 0.75),             # afirmada pero bajo 0.9: no sirve
        "e1.jpg": pred("OrdE", "FamE1"),
    }
    demo = elegir_demostracion(entradas, lambda f: respuestas[f["archivo"]], fijadas={})
    assert [f["archivo"] for f, _ in demo["afirmados"]] == ["a1.jpg", "b1.jpg", "e1.jpg"]
    assert demo["incierto"][0]["archivo"] == "a2.jpg"
    assert demo["principal"][0]["archivo"] == "a1.jpg"


def test_elegir_demostracion_respeta_la_foto_fijada():
    entradas = [
        ({"tipo": "familia", "nombre": "FamA1", "orden": "OrdA"},
         [fila("a1.jpg", "OrdA", "FamA1"), fila("a1b.jpg", "OrdA", "FamA1")]),
        ({"tipo": "familia", "nombre": "FamA2", "orden": "OrdA"}, [fila("a2.jpg", "OrdA", "FamA2")]),
    ]
    respuestas = {"a1.jpg": pred("OrdA", "FamA1"), "a1b.jpg": pred("OrdA", "FamA1"),
                  "a2.jpg": pred("OrdA", "FamA1", 0.4, True)}
    demo = elegir_demostracion(entradas, lambda f: respuestas[f["archivo"]],
                               fijadas={"principal": "a1b.jpg"}, cantidad_afirmados=1)
    assert demo["principal"][0]["archivo"] == "a1b.jpg"


def test_verificar_origen_rechaza_fotos_que_no_son_de_prueba():
    verificar_origen(["t1.jpg"], {"t1.jpg", "t2.jpg"})
    with pytest.raises(ValueError, match="entrenamiento"):
        verificar_origen(["x.jpg"], {"t1.jpg"})
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run: `.venv\Scripts\python -m pytest tests/test_catalogo_web.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'pipeline.catalogo_web'`.

- [ ] **Step 3: Implementar `pipeline/catalogo_web.py`**

```python
"""Contenido estático del catálogo y de la demostración de la web.

La portada y la herramienta muestran fotos y cifras: aquí se eligen y se
calculan, para que ninguna se escriba a mano.

- Catálogo: una foto por familia (y por orden sin familias) del conjunto de
  entrenamiento, prefiriendo licencias libres y fotos grandes, con su F1 de la
  corrida vigente y su crédito.
- Demostración: fotos del conjunto de PRUEBA, que el modelo nunca vio, pasadas
  por el mismo ONNX y el mismo servicio que usa el backend.

    python -m pipeline.catalogo_web
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageOps

from pipeline.inferencia import UMBRAL_FAMILIA
from pipeline.ontologia import Ontologia, cargar_ontologia

RANGO_LICENCIA = {"cc0": 0, "cc-by": 1, "cc-by-sa": 2}
LADO_FOTO = 640
CALIDAD_WEBP = 80
CONFIANZA_DEMO = 0.9          # familia afirmada con holgura, para la portada
CANDIDATAS_POR_CLASE = 3
MAXIMO_INFERENCIAS = 200


def rango_licencia(licencia: str) -> int:
    return RANGO_LICENCIA.get((licencia or "").strip().lower(), len(RANGO_LICENCIA))


def credito(fila: dict) -> str:
    return (fila.get("atribucion") or "").strip() or "Autor no registrado"


def leer_desempeno(texto: str) -> dict:
    """F1 por clase y tabla de cobertura del informe de `pipeline.desempeno`."""
    datos: dict = {"ordenes": {}, "familias": {}, "cobertura": {}}
    seccion = None
    for linea in texto.splitlines():
        if linea.startswith("## "):
            titulo = linea[3:].lower()
            seccion = (
                "ordenes" if titulo.startswith("órdenes")
                else "familias" if titulo.startswith("familias")
                else "cobertura" if titulo.startswith("cobertura")
                else None
            )
            continue
        if seccion in ("ordenes", "familias"):
            m = re.match(r"\|\s*(\w+)\s*\|\s*([0-9.]+)\s*\|", linea)
            if m:
                datos[seccion][m.group(1)] = float(m.group(2))
        elif seccion == "cobertura":
            m = re.match(r"\|\s*([0-9.]+)\s*\|\s*([0-9.]+)%\s*\|\s*([0-9.]+)%\s*\|", linea)
            if m:
                datos["cobertura"][float(m.group(1))] = (
                    float(m.group(2)) / 100, float(m.group(3)) / 100
                )
    return datos


def clave_de(fila: dict) -> str:
    return fila["familia"] or f"orden:{fila['orden']}"


def clases_del_catalogo(onto: Ontologia, desempeno: dict, conteos: dict) -> list[dict]:
    clases = []
    for orden in onto.ordenes:
        if orden.familias:
            for familia in orden.familias:
                clases.append({
                    "id": f"familia-{familia.nombre}", "tipo": "familia",
                    "nombre": familia.nombre, "nombre_comun": familia.nombre_comun,
                    "orden": orden.nombre, "provisional": familia.provisional,
                    "f1": desempeno["familias"].get(familia.nombre),
                    "fotos_entrenamiento": conteos.get(familia.nombre, 0),
                })
        else:
            clases.append({
                "id": f"orden-{orden.nombre}", "tipo": "orden",
                "nombre": orden.nombre, "nombre_comun": orden.nombre_comun,
                "orden": orden.nombre, "provisional": False,
                "f1": desempeno["ordenes"].get(orden.nombre),
                "fotos_entrenamiento": conteos.get(f"orden:{orden.nombre}", 0),
            })
    return clases


def candidatas_de(filas: list[dict], clase: dict) -> list[dict]:
    if clase["tipo"] == "familia":
        return [f for f in filas if f["familia"] == clase["nombre"]]
    return [f for f in filas if f["orden"] == clase["nombre"] and not f["familia"]]


def elegir_foto(candidatas: list[dict], area_de: Callable[[str], int]) -> dict:
    """La de licencia más libre; entre esas, la de más píxeles."""
    mejor = min(rango_licencia(f["licencia"]) for f in candidatas)
    grupo = sorted(
        (f for f in candidatas if rango_licencia(f["licencia"]) == mejor),
        key=lambda f: f["archivo"],
    )
    return max(grupo, key=lambda f: area_de(f["archivo"]))


def ordenar_para_demo(candidatas: list[dict]) -> list[dict]:
    return sorted(candidatas, key=lambda f: (rango_licencia(f["licencia"]), f["archivo"]))


def optimizar_foto(origen: Path, destino: Path, lado: int = LADO_FOTO) -> tuple[int, int]:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(origen) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((lado, lado), Image.LANCZOS)
        img.save(destino, "WEBP", quality=CALIDAD_WEBP, method=6)
        return img.size


def elegir_demostracion(
    entradas: list[tuple[dict, list[dict]]],
    predecir: Callable[[dict], dict],
    fijadas: dict,
    cantidad_afirmados: int = 3,
) -> dict:
    """Afirmados de órdenes distintos, un incierto real y la foto de portada.

    `entradas` son (clase, filas de PRUEBA ordenadas); `predecir` pasa una fila
    por el modelo. `fijadas` permite elegir a mano 'principal' e 'incierto'.
    """
    por_archivo = {f["archivo"]: f for _, filas in entradas for f in filas}
    inferencias = 0

    def consultar(fila: dict) -> dict:
        nonlocal inferencias
        inferencias += 1
        if inferencias > MAXIMO_INFERENCIAS:
            raise RuntimeError("demasiadas inferencias buscando la demostración")
        return predecir(fila)

    afirmados: list[tuple[dict, dict]] = []
    if fijadas.get("principal"):
        fila = por_archivo[fijadas["principal"]]
        afirmados.append((fila, consultar(fila)))
    ordenes_usados = {f["orden"] for f, _ in afirmados}
    for clase, filas in entradas:
        if len(afirmados) >= cantidad_afirmados:
            break
        if clase["tipo"] != "familia" or clase["orden"] in ordenes_usados:
            continue
        for fila in filas[:CANDIDATAS_POR_CLASE]:
            p = consultar(fila)
            if (p["familia"] == clase["nombre"] and not p["familia_incierta"]
                    and p["confianza_familia"] >= CONFIANZA_DEMO):
                afirmados.append((fila, p))
                ordenes_usados.add(clase["orden"])
                break

    incierto = None
    if fijadas.get("incierto"):
        fila = por_archivo[fijadas["incierto"]]
        incierto = (fila, consultar(fila))
    else:
        for clase, filas in entradas:
            if clase["tipo"] != "familia":
                continue
            for fila in filas[:CANDIDATAS_POR_CLASE]:
                p = consultar(fila)
                if p["orden"] == clase["orden"] and p["familia_incierta"]:
                    incierto = (fila, p)
                    break
            if incierto:
                break
    if not afirmados or incierto is None:
        raise RuntimeError("no se encontró una demostración completa")
    return {"principal": afirmados[0], "afirmados": afirmados, "incierto": incierto}


def verificar_origen(archivos: list[str], archivos_prueba: set[str]) -> None:
    ajenos = [a for a in archivos if a not in archivos_prueba]
    if ajenos:
        raise ValueError(
            f"la demostración usaría fotos de entrenamiento o validación: {ajenos}"
        )


def prediccion_a_dict(prediccion) -> dict:
    """La misma forma que devuelve /predecir (backend/app.py), sin las fichas."""
    return {
        "orden": prediccion.orden,
        "confianza_orden": prediccion.confianza_orden,
        "familia": prediccion.familia,
        "confianza_familia": prediccion.confianza_familia,
        "familia_incierta": prediccion.familia_incierta,
        "top_familias": [
            {"familia": nombre, "confianza": valor} for nombre, valor in prediccion.top_familias
        ],
    }


def hoja_de_contactos(clases: list[dict], publico: Path, destino: Path) -> None:
    """Todas las fotos del catálogo en una sola imagen, para revisarlas de un vistazo."""
    lado, columnas = 200, 8
    filas_hoja = (len(clases) + columnas - 1) // columnas
    hoja = Image.new("RGB", (columnas * lado, filas_hoja * (lado + 24)), (246, 248, 245))
    dibujo = ImageDraw.Draw(hoja)
    for i, clase in enumerate(clases):
        x, y = (i % columnas) * lado, (i // columnas) * (lado + 24)
        with Image.open(publico / clase["foto"]["archivo"].lstrip("/")) as img:
            miniatura = ImageOps.fit(img.convert("RGB"), (lado - 8, lado - 8))
        hoja.paste(miniatura, (x + 4, y + 4))
        dibujo.text((x + 6, y + lado), clase["id"], fill=(46, 46, 46))
    destino.parent.mkdir(parents=True, exist_ok=True)
    hoja.save(destino, quality=85)


def _leer_csv(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _ejemplo(fila: dict, prediccion: dict, archivo_publico: str) -> dict:
    return {
        "archivo": archivo_publico, "credito": credito(fila), "licencia": fila["licencia"],
        "url_origen": fila.get("url", ""),
        "real": {"orden": fila["orden"], "familia": fila["familia"]},
        "prediccion": prediccion,
    }


def main() -> None:
    from backend.app import CORRIDA_VIGENTE
    from backend.servicio import ServicioInsectos

    parser = argparse.ArgumentParser(description="Genera el catálogo y la demostración de la web")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--splits", default="datos/splits")
    parser.add_argument("--curado", default="datos/curado")
    parser.add_argument("--corrida", default=f"modelo/{CORRIDA_VIGENTE}")
    parser.add_argument("--desempeno", required=True,
                        help="informe por clase de la corrida, p. ej. docs/desempeno_por_clase_v4.md")
    parser.add_argument("--preferencias", default="frontend/catalogo_preferencias.yaml")
    parser.add_argument("--publico", default="frontend/public")
    parser.add_argument("--contactos", default="datos/catalogo_contactos.jpg")
    args = parser.parse_args()

    corrida, curado, publico = Path(args.corrida), Path(args.curado), Path(args.publico)
    onto = cargar_ontologia(Path(args.ontologia))
    desempeno = leer_desempeno(Path(args.desempeno).read_text(encoding="utf-8"))
    evaluacion = json.loads((corrida / "evaluacion.json").read_text(encoding="utf-8"))["test"]
    preferencias = yaml.safe_load(Path(args.preferencias).read_text(encoding="utf-8")) or {}
    fijadas_catalogo = preferencias.get("catalogo") or {}
    fijadas_demo = preferencias.get("demostracion") or {}

    train = _leer_csv(Path(args.splits) / "train.csv")
    prueba = _leer_csv(Path(args.splits) / "test.csv")
    conteos = Counter(clave_de(f) for f in train)
    clases = clases_del_catalogo(onto, desempeno, conteos)

    def area(archivo: str) -> int:
        with Image.open(curado / archivo) as img:
            return img.width * img.height

    por_archivo_train = {f["archivo"]: f for f in train}
    for clase in clases:
        fijada = fijadas_catalogo.get(clase["id"])
        fila = por_archivo_train[fijada] if fijada else elegir_foto(candidatas_de(train, clase), area)
        destino = publico / "catalogo" / "fotos" / f"{clase['id']}.webp"
        ancho, alto = optimizar_foto(curado / fila["archivo"], destino)
        clase["foto"] = {
            "archivo": f"/catalogo/fotos/{clase['id']}.webp", "ancho": ancho, "alto": alto,
            "credito": credito(fila), "licencia": fila["licencia"], "url_origen": fila.get("url", ""),
        }
        print(f"{clase['id']}: {fila['archivo']} ({fila['licencia']})")

    servicio = ServicioInsectos(corrida / "insectos.onnx", corrida / "etiquetas.json")
    demo_dir = publico / "catalogo" / "demo"

    def predecir(fila: dict) -> dict:
        # Se predice sobre el mismo WebP que se publica: el que el visitante envía.
        destino = demo_dir / (Path(fila["archivo"]).stem + ".webp")
        if not destino.exists():
            optimizar_foto(curado / fila["archivo"], destino)
        return prediccion_a_dict(servicio.predecir_bytes(destino.read_bytes()))

    entradas = [(c, ordenar_para_demo(candidatas_de(prueba, c))) for c in clases]
    demo = elegir_demostracion(entradas, predecir, fijadas_demo)
    usados = [demo["incierto"], *demo["afirmados"]]
    verificar_origen([f["archivo"] for f, _ in usados], {f["archivo"] for f in prueba})

    def publico_de(fila: dict) -> str:
        return f"/catalogo/demo/{Path(fila['archivo']).stem}.webp"

    principal, incierto = demo["principal"], demo["incierto"]
    demostracion = {
        "principal": _ejemplo(principal[0], principal[1], publico_de(principal[0])),
        "incierto": _ejemplo(incierto[0], incierto[1], publico_de(incierto[0])),
        "ejemplos": [_ejemplo(f, p, publico_de(f)) for f, p in [*demo["afirmados"], incierto]],
    }
    # Quedan en demo/ solo las fotos usadas; las probadas y descartadas se borran.
    conservar = {Path(e["archivo"]).name for e in demostracion["ejemplos"]}
    for sobrante in demo_dir.glob("*.webp"):
        if sobrante.name not in conservar:
            sobrante.unlink()

    responde, acierta = desempeno["cobertura"][UMBRAL_FAMILIA]
    catalogo = {
        "corrida": corrida.name,
        "metricas": {
            "n_prueba": evaluacion["n"],
            "exactitud_familia": evaluacion["exactitud_familia"],
            "top3_familia": evaluacion["top3_familia"],
            "f1_orden": evaluacion["macro_f1_orden"],
            "f1_familia": evaluacion["macro_f1_familia"],
            "umbral": UMBRAL_FAMILIA,
            "responde": responde,
            "acierta_cuando_responde": acierta,
        },
        "ordenes": [
            {"nombre": o.nombre, "nombre_comun": o.nombre_comun, "tiene_familias": bool(o.familias)}
            for o in onto.ordenes
        ],
        "clases": clases,
    }
    salida = publico / "catalogo"
    (salida / "catalogo.json").write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (salida / "demostracion.json").write_text(
        json.dumps(demostracion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    hoja_de_contactos(clases, publico, Path(args.contactos))
    print(f"Catálogo: {len(clases)} clases. Hoja de contactos en {args.contactos}")


if __name__ == "__main__":
    main()
```

`frontend/catalogo_preferencias.yaml`:

```yaml
# Fotos elegidas a mano para la web. Se usan al correr:
#   python -m pipeline.catalogo_web --desempeno docs/desempeno_por_clase_v4.md
#
# catalogo: id de la clase (familia-<Nombre> u orden-<Nombre>) -> archivo de
#   datos/splits/train.csv (columna "archivo").
# demostracion: "principal" e "incierto" -> archivo de datos/splits/test.csv.
#   Solo se aceptan fotos de prueba: el modelo no las vio al entrenar.
catalogo: {}
demostracion: {}
```

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run: `.venv\Scripts\python -m pytest tests/test_catalogo_web.py tests/test_ontologia.py -q`
Expected: todas pasan, incluida la de nombres literales. Cada prueba tarda menos de 5 s.

- [ ] **Step 5: Generar con los datos reales**

Run: `.venv\Scripts\python -m pipeline.catalogo_web --desempeno docs/desempeno_por_clase_v4.md`
Expected:
- 44 líneas `<id>: <archivo> (<licencia>)`;
- `Catálogo: 44 clases`;
- sin excepciones.

Tarda unos minutos: lee los tamaños de las fotos y corre el modelo sobre pocas decenas de fotos de prueba. Si la PC se queda sin memoria, cerrar programas y reintentar. Solo carga un modelo.

Run: `.venv\Scripts\python -c "import json; c=json.load(open('frontend/public/catalogo/catalogo.json',encoding='utf-8')); d=json.load(open('frontend/public/catalogo/demostracion.json',encoding='utf-8')); print(len(c['clases']), c['metricas']); print(d['principal']['real'], d['principal']['prediccion']['familia'], d['incierto']['prediccion']['familia_incierta'], len(d['ejemplos']))"`
Expected:
- `44`;
- métricas con `exactitud_familia` 0.9216, `responde` 0.94 y `acierta_cuando_responde` 0.955;
- `principal` con la familia real igual a la predicha;
- `True` para el incierto;
- `4` ejemplos.

Run: `du -sh frontend/public/catalogo`
Expected: menos de 3.5 MB en total.

- [ ] **Step 6: Revisar la hoja de contactos y fijar reemplazos**

Abrir `datos/catalogo_contactos.jpg` con la herramienta Read. Una foto no sirve si:
- no se ve el insecto (montículo, nido, paisaje o solo daño en la planta);
- el insecto es diminuto en el cuadro;
- tiene texto o marcas superpuestas;
- está muy borrosa.

Para cada foto que no sirva, buscar otra de la misma clase en `datos/splits/train.csv` que se vea bien. Hay que abrir un par de candidatas con Read desde `datos/curado/`. Agregarla en `frontend/catalogo_preferencias.yaml`, por ejemplo `catalogo: {familia-Termitidae: "Isoptera/Termitidae/123.jpg"}`, y volver a correr el paso 5. Revisar también las 4 fotos de `frontend/public/catalogo/demo/`, con el mismo criterio.

Registrar en el ledger cada reemplazo, con el motivo.

- [ ] **Step 7: Commit**

```bash
git add pipeline/catalogo_web.py tests/test_catalogo_web.py frontend/catalogo_preferencias.yaml frontend/public/catalogo
git commit -m "Catálogo web: fotos, F1 y demostración generados desde los datos" -m "Una foto por familia (y por orden sin familias) del conjunto de entrenamiento, con licencia libre si existe y su crédito; el F1 de la corrida vigente; y una demostración con fotos de PRUEBA pasadas por el mismo modelo y servicio que el backend. Ninguna cifra de la web se escribe a mano." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 4: Base del frontend: dos páginas, fuentes, tokens, cabecera y pie

**Files:**
- Modify: `frontend/package.json` (dependencias de fuentes), `frontend/vite.config.js`, `frontend/index.html`
- Create: `frontend/identificar/index.html`, `frontend/src/compartido/{base.css, datos.js, Cabecera.jsx, Pie.jsx}`, `frontend/src/paginas/inicio/{main.jsx, Inicio.jsx}`, `frontend/src/paginas/identificar/{main.jsx, Identificar.jsx}`
- Move: `frontend/src/api.js` → `frontend/src/compartido/api.js`
- Delete: `frontend/src/App.jsx`, `frontend/src/main.jsx`, `frontend/src/estilos.css`, `frontend/src/componentes/Explorador.jsx`, `frontend/pruebas/Explorador.test.jsx`
- Test: `frontend/pruebas/contraste.test.js`, `frontend/pruebas/Cabecera.test.jsx`, `frontend/pruebas/datos.test.js`, `frontend/pruebas/api.test.js` (ruta del import), `tests/test_app.py`

**Interfaces:**
- Consumes: rutas de la tarea 2 (`/marca/*`, `/favicon.ico` y `/manifest.webmanifest`) y de la tarea 3 (`/catalogo/*.json`).
- Produces:
  - `Cabecera({ pagina: 'inicio' | 'identificar' })` y `Pie({ corrida?: string })`;
  - `cargarCatalogo(): Promise<object>`, `cargarDemostracion(): Promise<object>` y `archivoDesdeRuta(ruta: string, nombre: string): Promise<File>`, todos de `src/compartido/datos.js`;
  - clases CSS globales de `base.css`: `.contenedor`, `.boton` (con `--principal`, `--secundario`, `--claro`, `--contorno` y `--chico`), `.chip` (con `--plaga`, `--benefico` y `--provisional`), `.credito`, `.ayuda`, `.aviso` y `.aviso--error`, `.marco` (esquinas de encuadre), `.cientifico` y `.visualmente-oculto`, más los tokens `--*` listados abajo;
  - `api.js` sin cambios de interfaz, solo de ubicación.

- [ ] **Step 1: Instalar las fuentes**

Run (en `frontend/`): `npm install @fontsource/lexend@^5.3.0 @fontsource/atkinson-hyperlegible-next@^5.3.0`
Expected: las dos quedan en `dependencies` de `package.json`.

- [ ] **Step 2: Escribir las pruebas que fallan**

`frontend/pruebas/contraste.test.js`:

```javascript
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const css = readFileSync(new URL('../src/compartido/base.css', import.meta.url), 'utf8')

function token(nombre) {
  if (nombre.startsWith('#')) return nombre
  const hallado = css.match(new RegExp(`--${nombre}:\\s*(#[0-9a-fA-F]{6})`))
  if (!hallado) throw new Error(`falta el token --${nombre}`)
  return hallado[1]
}

function luminancia(hex) {
  const canales = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
  const [r, g, b] = canales.map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contraste(a, b) {
  const [claro, oscuro] = [luminancia(a), luminancia(b)].sort((x, y) => y - x)
  return (claro + 0.05) / (oscuro + 0.05)
}

// [texto, fondo]: todos deben llegar a 4.5:1 (WCAG AA, texto normal).
const PARES = [
  ['gris', 'fondo'],
  ['gris', 'superficie'],
  ['texto-suave', 'fondo'],
  ['texto-suave', 'superficie'],
  ['petroleo', 'fondo'],
  ['verde-amazonico', 'fondo'],
  ['verde-amazonico', 'superficie'],
  ['verde-amazonico', 'selva-fondo'],
  ['ambar-texto', 'ambar-fondo'],
  ['ambar-texto', 'superficie'],
  ['gris', 'amarillo'],
  ['gris', 'ambar-fondo'],
  ['#ffffff', 'verde-amazonico'],
  ['#ffffff', 'petroleo'],
  ['texto-sobre-petroleo', 'petroleo'],
  ['verde-lima', 'petroleo'],
  ['petroleo', 'verde-lima'],
  ['error-texto', 'error-fondo'],
]

describe('contraste de los tokens de color', () => {
  it.each(PARES)('%s sobre %s llega a 4.5:1', (texto, fondo) => {
    expect(contraste(token(texto), token(fondo))).toBeGreaterThanOrEqual(4.5)
  })
})
```

`frontend/pruebas/Cabecera.test.jsx`:

```javascript
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Cabecera from '../src/compartido/Cabecera.jsx'
import Pie from '../src/compartido/Pie.jsx'

describe('Cabecera', () => {
  it('enlaza al inicio, al catálogo y a la herramienta', () => {
    render(<Cabecera pagina="inicio" />)
    expect(screen.getByRole('link', { name: /INSECTIA, inicio/ })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Catálogo' })).toHaveAttribute('href', '/#catalogo')
    expect(screen.getByRole('link', { name: 'Identificar un insecto' })).toHaveAttribute('href', '/identificar/')
  })

  it('marca la página actual', () => {
    render(<Cabecera pagina="identificar" />)
    expect(screen.getByRole('link', { name: 'Identificar un insecto' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('link', { name: 'Inicio' })).not.toHaveAttribute('aria-current')
  })
})

describe('Pie', () => {
  it('da el crédito de las fotos y no nombra personas', () => {
    render(<Pie corrida="v4_convnext_t_288" />)
    expect(screen.getByText(/Fotos: iNaturalist/)).toBeInTheDocument()
    expect(screen.getByText(/v4_convnext_t_288/)).toBeInTheDocument()
    expect(screen.queryByText(/Dra\.|Dr\./)).not.toBeInTheDocument()
  })
})
```

`frontend/pruebas/datos.test.js`:

```javascript
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  RUTA_CATALOGO,
  archivoDesdeRuta,
  cargarCatalogo,
  cargarDemostracion,
} from '../src/compartido/datos.js'

afterEach(() => vi.restoreAllMocks())

describe('datos estáticos', () => {
  it('lee el catálogo desde public/, no desde la API', async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ clases: [] }) }))
    await cargarCatalogo()
    expect(global.fetch).toHaveBeenCalledWith(RUTA_CATALOGO)
    expect(RUTA_CATALOGO).toBe('/catalogo/catalogo.json')
  })

  it('explica cuando el catálogo no existe', async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: false, status: 404 }))
    await expect(cargarDemostracion()).rejects.toThrow(/no se encontró/i)
  })

  it('explica cuando el servidor no responde', async () => {
    global.fetch = vi.fn(() => Promise.reject(new TypeError('Failed to fetch')))
    await expect(cargarCatalogo()).rejects.toThrow(/servidor/i)
  })

  it('convierte una foto de ejemplo en un File', async () => {
    const blob = new Blob(['x'], { type: 'image/webp' })
    global.fetch = vi.fn(() => Promise.resolve({ ok: true, blob: () => Promise.resolve(blob) }))
    const archivo = await archivoDesdeRuta('/catalogo/demo/a.webp', 'a.webp')
    expect(archivo).toBeInstanceOf(File)
    expect(archivo.name).toBe('a.webp')
    expect(archivo.type).toBe('image/webp')
  })

  it('avisa cuando la foto de ejemplo no carga', async () => {
    global.fetch = vi.fn(() => Promise.resolve({ ok: false, status: 404 }))
    await expect(archivoDesdeRuta('/catalogo/demo/x.webp', 'x.webp')).rejects.toThrow(/foto de ejemplo/i)
  })
})
```

Agregar al final de `tests/test_app.py`:

```python
def test_la_pagina_de_identificacion_se_sirve_con_y_sin_barra(tmp_path, monkeypatch):
    """Vite genera frontend/dist/identificar/index.html: /identificar/ debe servirlo,
    y /identificar (escrito a mano) debe llegar ahí en vez de dar 404."""
    import backend.app as modulo

    pagina = tmp_path / "frontend" / "dist" / "identificar"
    pagina.mkdir(parents=True)
    (pagina / "index.html").write_text("<p>pagina de identificacion</p>", encoding="utf-8")
    (tmp_path / "frontend" / "dist" / "index.html").write_text("<p>inicio</p>", encoding="utf-8")
    monkeypatch.setattr(modulo, "RAIZ", tmp_path)

    c = cliente()
    assert "identificacion" in c.get("/identificar/").text
    sin_barra = c.get("/identificar")
    assert sin_barra.status_code == 200 and "identificacion" in sin_barra.text
    assert c.get("/salud").json()["estado"] == "ok"   # la API sigue por encima
```

En `frontend/pruebas/api.test.js`, cambiar las dos rutas de import `'../src/api.js'` por `'../src/compartido/api.js'`.

- [ ] **Step 3: Correr las pruebas y verificar que fallan**

Run (en `frontend/`): `npm run prueba`
Expected: FAIL en `contraste.test.js`, `Cabecera.test.jsx`, `datos.test.js` y `api.test.js`, porque faltan los archivos.

Run: `.venv\Scripts\python -m pytest tests/test_app.py -q -k barra`
Expected: PASS o FAIL. Si pasa, es porque `StaticFiles(html=True)` ya resuelve la redirección. En ese caso la prueba queda como protección contra regresiones, y se anota en el ledger que pasó sin cambios de código.

- [ ] **Step 4: Mover `api.js` y borrar lo viejo**

```bash
git mv frontend/src/api.js frontend/src/compartido/api.js
git rm frontend/src/App.jsx frontend/src/main.jsx frontend/src/estilos.css frontend/src/componentes/Explorador.jsx frontend/pruebas/Explorador.test.jsx
```

El explorador de la base vuelve como parte del catálogo en la tarea 7.

- [ ] **Step 5: Implementar `frontend/src/compartido/base.css`**

```css
/* Fuentes locales: la sustentación puede ser sin internet. */
@import '@fontsource/lexend/500.css';
@import '@fontsource/lexend/700.css';
@import '@fontsource/atkinson-hyperlegible-next/400.css';
@import '@fontsource/atkinson-hyperlegible-next/400-italic.css';
@import '@fontsource/atkinson-hyperlegible-next/700.css';

:root {
  /* Paleta de la marca (PRODUCT.md). */
  --verde-amazonico: #0b5e3b;
  --verde-selva: #4caf50;
  --verde-lima: #a3d977;
  --petroleo: #0f3d3e;
  --amarillo: #f4b400;
  --gris: #2e2e2e;

  /* Derivados, con contraste verificado en pruebas/contraste.test.js. */
  --fondo: #f6f8f5;
  --superficie: #ffffff;
  --texto-suave: #4e5a55;
  --texto-sobre-petroleo: #d6e4e0;
  --ambar-texto: #7a5a00;
  --ambar-fondo: #fff6d6;
  --selva-fondo: #e8f5e9;
  --error-texto: #7a1c14;
  --error-fondo: #fdecea;
  --pista: #e3e8e2;
  --borde: rgba(46, 46, 46, 0.12);

  --fuente-titulo: 'Lexend', system-ui, sans-serif;
  --fuente-texto: 'Atkinson Hyperlegible Next', system-ui, sans-serif;

  --radio: 8px;
  --radio-grande: 16px;
  --radio-pastilla: 9999px;

  --espacio-1: 4px;
  --espacio-2: 8px;
  --espacio-3: 12px;
  --espacio-4: 16px;
  --espacio-5: 24px;
  --espacio-6: 32px;
  --espacio-7: 48px;
  --espacio-8: 72px;

  --sombra: 0 1px 2px rgba(15, 61, 62, 0.06), 0 2px 8px rgba(15, 61, 62, 0.04);
  --curva-salida: cubic-bezier(0.25, 1, 0.5, 1);
  --ancho-max: 1200px;

  /* Escala de capas. */
  --z-cabecera: 10;
  --z-fondo-panel: 20;
  --z-saltar: 40;
}

*, *::before, *::after { box-sizing: border-box; }

html {
  -webkit-text-size-adjust: 100%;
  scroll-padding-top: 88px;
}

body {
  margin: 0;
  background: var(--fondo);
  color: var(--gris);
  font-family: var(--fuente-texto);
  font-size: 1.0625rem;
  line-height: 1.55;
}

img { display: block; max-width: 100%; }

h1, h2, h3, h4 {
  margin: 0 0 var(--espacio-3);
  font-family: var(--fuente-titulo);
  color: var(--petroleo);
  line-height: 1.15;
  letter-spacing: -0.01em;
  text-wrap: balance;
}
h1 { font-size: clamp(2rem, 1.3rem + 3vw, 3.5rem); font-weight: 700; letter-spacing: -0.02em; }
h2 { font-size: clamp(1.6rem, 1.2rem + 1.6vw, 2.25rem); font-weight: 700; }
h3 { font-size: 1.25rem; font-weight: 500; }
h4 { font-size: 1.125rem; font-weight: 500; }

p { margin: 0 0 var(--espacio-3); max-width: 70ch; text-wrap: pretty; }
a { color: var(--verde-amazonico); text-underline-offset: 0.15em; }

.cientifico { font-family: var(--fuente-texto); font-style: italic; }
.ayuda { color: var(--texto-suave); }
.credito { font-size: 0.8125rem; color: var(--texto-suave); margin: 0; }

.contenedor { width: min(100% - 2rem, var(--ancho-max)); margin-inline: auto; }

.visualmente-oculto {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.saltar {
  position: absolute;
  left: var(--espacio-4);
  top: -100px;
  z-index: var(--z-saltar);
  background: var(--petroleo);
  color: #fff;
  padding: var(--espacio-2) var(--espacio-4);
  border-radius: var(--radio);
}
.saltar:focus { top: var(--espacio-2); }

/* Foco: contorno Verde Amazónico (visible sobre claro) más halo Lima (visible sobre petróleo). */
:focus-visible,
.boton:has(input:focus-visible) {
  outline: 2px solid var(--verde-amazonico);
  outline-offset: 2px;
  box-shadow: 0 0 0 5px var(--verde-lima);
}

/* Botones */
.boton {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--espacio-2);
  min-height: 44px;
  padding: 0 var(--espacio-5);
  border: 1.5px solid transparent;
  border-radius: var(--radio);
  font-family: var(--fuente-texto);
  font-size: 1rem;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 200ms var(--curva-salida), transform 120ms var(--curva-salida);
}
.boton:active { transform: scale(0.98); }
.boton:disabled,
.boton:has(input:disabled) { opacity: 0.55; cursor: not-allowed; }
.boton--principal { background: var(--verde-amazonico); color: #fff; }
.boton--principal:hover { background: var(--petroleo); }
.boton--secundario { background: var(--superficie); color: var(--verde-amazonico); border-color: var(--verde-amazonico); }
.boton--secundario:hover { background: var(--selva-fondo); }
.boton--claro { background: var(--verde-lima); color: var(--petroleo); }
.boton--claro:hover { background: #b6e38f; }
.boton--contorno { background: transparent; color: #fff; border-color: rgba(255, 255, 255, 0.75); }
.boton--contorno:hover { background: rgba(255, 255, 255, 0.08); }
.boton--chico { padding: 0 var(--espacio-4); font-size: 0.9375rem; }

/* Chips de estado: pastilla, siempre con texto. */
.chip {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  min-height: 28px;
  padding: 2px var(--espacio-3);
  border-radius: var(--radio-pastilla);
  font-size: 0.875rem;
  font-weight: 700;
}
.chip--plaga { background: var(--amarillo); color: var(--gris); }
.chip--benefico { background: var(--selva-fondo); color: var(--verde-amazonico); border: 1px solid var(--verde-amazonico); }
.chip--provisional { background: var(--ambar-fondo); color: var(--ambar-texto); }

.aviso {
  padding: var(--espacio-4);
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  background: var(--superficie);
}
.aviso--error { background: var(--error-fondo); border-color: #d9a39e; color: var(--error-texto); }
.aviso--error p { margin-bottom: var(--espacio-3); }

/* Esquinas de encuadre, tomadas del logo. */
.marco { position: relative; padding: 10px; }
.marco::before {
  --largo: 28px;
  --grosor: 4px;
  --color: var(--petroleo);
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(var(--color) 0 0) 0 0 / var(--largo) var(--grosor),
    linear-gradient(var(--color) 0 0) 0 0 / var(--grosor) var(--largo),
    linear-gradient(var(--color) 0 0) 100% 0 / var(--largo) var(--grosor),
    linear-gradient(var(--color) 0 0) 100% 0 / var(--grosor) var(--largo),
    linear-gradient(var(--color) 0 0) 0 100% / var(--largo) var(--grosor),
    linear-gradient(var(--color) 0 0) 0 100% / var(--grosor) var(--largo),
    linear-gradient(var(--color) 0 0) 100% 100% / var(--largo) var(--grosor),
    linear-gradient(var(--color) 0 0) 100% 100% / var(--grosor) var(--largo);
  background-repeat: no-repeat;
}
.marco > img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; border-radius: var(--radio); }

/* Cabecera */
.cabecera {
  position: sticky;
  top: 0;
  z-index: var(--z-cabecera);
  background: rgba(246, 248, 245, 0.97);
  border-bottom: 1px solid var(--borde);
}
.cabecera__fila { display: flex; align-items: center; justify-content: space-between; gap: var(--espacio-4); min-height: 68px; }
.cabecera__marca { display: flex; align-items: center; min-height: 44px; }
.cabecera__logo { height: 44px; width: auto; }
.cabecera__simbolo { display: none; height: 40px; width: auto; }
.cabecera__nav { display: flex; align-items: center; gap: var(--espacio-2); }
.cabecera__enlace {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 var(--espacio-3);
  border-radius: var(--radio);
  color: var(--petroleo);
  font-weight: 700;
  text-decoration: none;
}
.cabecera__enlace:hover { background: var(--selva-fondo); }
.cabecera__enlace[aria-current='page'] { text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 6px; }
@media (max-width: 640px) {
  .cabecera__logo, .cabecera__enlace { display: none; }
  .cabecera__simbolo { display: block; }
}

/* Pie */
.pie { margin-top: var(--espacio-8); padding-block: var(--espacio-7); background: var(--petroleo); color: var(--texto-sobre-petroleo); }
.pie a { color: var(--verde-lima); }
.pie__fila { display: flex; flex-wrap: wrap; justify-content: space-between; gap: var(--espacio-6); }
.pie__simbolo { height: 48px; width: auto; margin-bottom: var(--espacio-3); }
.pie__marca { margin-bottom: var(--espacio-2); font-family: var(--fuente-titulo); font-size: 1.5rem; font-weight: 700; color: #fff; }
.pie__datos { display: grid; gap: var(--espacio-2); margin: 0; padding: 0; list-style: none; }

@keyframes aparecer { from { opacity: 0; transform: translateY(8px); } }
@keyframes llenar { from { transform: scaleX(0); } }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 1ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 1ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 6: Implementar `datos.js`, `Cabecera.jsx` y `Pie.jsx`**

`frontend/src/compartido/datos.js`:

```javascript
// Contenido generado por pipeline/catalogo_web.py y servido como archivo estático
// junto a la página. No pasa por la API: mismo origen en producción y en Vite.
export const RUTA_CATALOGO = '/catalogo/catalogo.json'
export const RUTA_DEMOSTRACION = '/catalogo/demostracion.json'

async function leerJson(ruta) {
  let respuesta
  try {
    respuesta = await fetch(ruta)
  } catch {
    throw new Error('No se pudo cargar el contenido. ¿Está encendido el servidor?')
  }
  if (!respuesta.ok) throw new Error('No se encontró el contenido del catálogo.')
  return respuesta.json()
}

export const cargarCatalogo = () => leerJson(RUTA_CATALOGO)
export const cargarDemostracion = () => leerJson(RUTA_DEMOSTRACION)

// Convierte una foto de ejemplo publicada en un File, para enviarla a /predecir.
export async function archivoDesdeRuta(ruta, nombre) {
  let respuesta
  try {
    respuesta = await fetch(ruta)
  } catch {
    throw new Error('No se pudo cargar la foto de ejemplo.')
  }
  if (!respuesta.ok) throw new Error('No se pudo cargar la foto de ejemplo.')
  const blob = await respuesta.blob()
  return new File([blob], nombre, { type: blob.type || 'image/webp' })
}
```

`frontend/src/compartido/Cabecera.jsx`:

```javascript
export default function Cabecera({ pagina }) {
  return (
    <header className="cabecera">
      <div className="contenedor cabecera__fila">
        <a className="cabecera__marca" href="/" aria-label="INSECTIA, inicio">
          <img className="cabecera__logo" src="/marca/logo-horizontal.webp" alt="" />
          <img className="cabecera__simbolo" src="/marca/simbolo.webp" alt="" />
        </a>
        <nav className="cabecera__nav" aria-label="Principal">
          <a
            className="cabecera__enlace"
            href="/"
            aria-current={pagina === 'inicio' ? 'page' : undefined}
          >
            Inicio
          </a>
          <a className="cabecera__enlace" href="/#catalogo">
            Catálogo
          </a>
          <a
            className="boton boton--principal"
            href="/identificar/"
            aria-current={pagina === 'identificar' ? 'page' : undefined}
          >
            Identificar un insecto
          </a>
        </nav>
      </div>
    </header>
  )
}
```

`frontend/src/compartido/Pie.jsx`:

```javascript
export default function Pie({ corrida }) {
  return (
    <footer className="pie">
      <div className="contenedor pie__fila">
        <div>
          <img className="pie__simbolo" src="/marca/simbolo-claro.webp" alt="" />
          <p className="pie__marca">INSECTIA</p>
          <p>
            Universidad Nacional de la Amazonía Peruana · Facultad de Agronomía · Proyecto
            Formativo INAAM–FISI
          </p>
        </div>
        <ul className="pie__datos">
          <li>Fotos: iNaturalist, con el crédito de cada autor.</li>
          {corrida && <li>Modelo: {corrida}</li>}
          <li>
            <a href="/identificar/">Identificar un insecto</a>
          </li>
        </ul>
      </div>
    </footer>
  )
}
```

- [ ] **Step 7: Páginas mínimas y configuración de Vite**

`frontend/index.html` (reemplazo completo):

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>INSECTIA · Identificación de insectos de la Amazonía peruana</title>
    <meta name="description" content="Identifica el orden y la familia de un insecto de importancia económica de la Amazonía peruana a partir de una foto." />
    <meta name="theme-color" content="#0f3d3e" />
    <link rel="icon" href="/favicon.ico" sizes="48x48" />
    <link rel="icon" href="/marca/icon-192.png" type="image/png" sizes="192x192" />
    <link rel="apple-touch-icon" href="/marca/apple-touch-icon.png" />
    <link rel="manifest" href="/manifest.webmanifest" />
  </head>
  <body>
    <a class="saltar" href="#contenido">Saltar al contenido</a>
    <div id="root"></div>
    <script type="module" src="/src/paginas/inicio/main.jsx"></script>
  </body>
</html>
```

`frontend/identificar/index.html`:

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Identificar un insecto · INSECTIA</title>
    <meta name="description" content="Sube la foto de un insecto y obtén su orden y su familia, con la seguridad del modelo." />
    <meta name="theme-color" content="#0f3d3e" />
    <link rel="icon" href="/favicon.ico" sizes="48x48" />
    <link rel="icon" href="/marca/icon-192.png" type="image/png" sizes="192x192" />
    <link rel="apple-touch-icon" href="/marca/apple-touch-icon.png" />
    <link rel="manifest" href="/manifest.webmanifest" />
  </head>
  <body>
    <a class="saltar" href="#contenido">Saltar al contenido</a>
    <div id="root"></div>
    <script type="module" src="/src/paginas/identificar/main.jsx"></script>
  </body>
</html>
```

`frontend/src/paginas/inicio/main.jsx`:

```javascript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../compartido/base.css'
import Inicio from './Inicio.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Inicio />
  </StrictMode>,
)
```

`frontend/src/paginas/inicio/Inicio.jsx` (mínimo; la tarea 7 lo completa):

```javascript
import Cabecera from '../../compartido/Cabecera.jsx'
import Pie from '../../compartido/Pie.jsx'

export default function Inicio() {
  return (
    <>
      <Cabecera pagina="inicio" />
      <main id="contenido" className="contenedor">
        <h1>Identifica el orden y la familia de un insecto con una foto</h1>
        <a className="boton boton--principal" href="/identificar/">
          Identificar un insecto
        </a>
      </main>
      <Pie />
    </>
  )
}
```

`frontend/src/paginas/identificar/main.jsx`:

```javascript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../compartido/base.css'
import Identificar from './Identificar.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Identificar />
  </StrictMode>,
)
```

`frontend/src/paginas/identificar/Identificar.jsx` (mínimo; la tarea 6 lo completa):

```javascript
import Cabecera from '../../compartido/Cabecera.jsx'
import Pie from '../../compartido/Pie.jsx'

export default function Identificar() {
  return (
    <>
      <Cabecera pagina="identificar" />
      <main id="contenido" className="contenedor">
        <h1>Identificar un insecto</h1>
      </main>
      <Pie />
    </>
  )
}
```

`frontend/vite.config.js` (reemplazo completo):

```javascript
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const raiz = (ruta) => fileURLToPath(new URL(ruta, import.meta.url))

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  build: {
    // Dos páginas: FastAPI sirve dist/index.html en / y dist/identificar/index.html
    // en /identificar/, sin enrutador del lado del cliente.
    rollupOptions: {
      input: {
        inicio: raiz('./index.html'),
        identificar: raiz('./identificar/index.html'),
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './pruebas/preparacion.js',
    include: ['pruebas/**/*.test.{js,jsx}'],
  },
})
```

- [ ] **Step 8: Correr las pruebas y verificar que pasan**

Run (en `frontend/`): `npm run prueba`
Expected: pasan todas, las nuevas y las que quedan: `api`, `Ficha`, `Resultado` y `SubirFoto` siguen probando los componentes de `src/componentes/`.

Run (en `frontend/`): `npm run build`
Expected: existen `dist/index.html` y `dist/identificar/index.html`, sin errores. Si Vite 8 advierte que `rollupOptions` es obsoleto, renombrar la clave a `rolldownOptions`, volver a construir y registrar la decisión en el ledger.

Run: `.venv\Scripts\python -m pytest tests/test_app.py -q`
Expected: todas pasan.

- [ ] **Step 9: Commit**

```bash
git add -A frontend tests/test_app.py
git commit -m "Frontend: dos páginas, fuentes locales, tokens de la marca, cabecera y pie" -m "La presentación (/) y la identificación (/identificar/) son dos entradas de Vite que FastAPI sirve sin enrutador. Los colores derivados de la paleta tienen su contraste verificado en una prueba. Las fuentes van locales para funcionar sin internet." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 5: Componentes de resultado: barra de confianza, importancia, ficha y resultado

**Files:**
- Create: `frontend/src/compartido/importancia.js`, `frontend/src/compartido/BarraConfianza.jsx`
- Move and rewrite: `frontend/src/componentes/Ficha.jsx` → `frontend/src/compartido/Ficha.jsx`; `frontend/src/componentes/Resultado.jsx` → `frontend/src/compartido/Resultado.jsx`
- Modify: `frontend/src/compartido/base.css` (estilos de barra, ficha y resultado, al final)
- Test: `frontend/pruebas/importancia.test.js`, `frontend/pruebas/BarraConfianza.test.jsx`, `frontend/pruebas/Ficha.test.jsx` (reescrita), `frontend/pruebas/Resultado.test.jsx` (reescrita)

**Interfaces:**
- Consumes: clases de `base.css` (tarea 4).
- Produces:
  - `clasificarImportancia(texto?: string): 'plaga' | 'benefico' | null`
  - `porcentaje(valor: number): string`, que da `"94 %"`
  - `BarraConfianza({ titulo: string, valor: number, estado?: 'neutra' | 'afirmada' | 'incierta' | 'candidata' })`
  - `Ficha({ fichas?: object[], titulo?: string, vacio?: string })`
  - `Resultado({ prediccion: object | null, conEnlace?: boolean = true })`, donde `prediccion` tiene la forma de `/predecir` (con `fichas` opcional)

- [ ] **Step 1: Escribir las pruebas que fallan**

`frontend/pruebas/importancia.test.js`:

```javascript
import { describe, expect, it } from 'vitest'
import { clasificarImportancia } from '../src/compartido/importancia.js'

describe('clasificarImportancia', () => {
  it('reconoce la plaga escrita a mano en la base', () => {
    expect(clasificarImportancia('Plaga')).toBe('plaga')
    expect(clasificarImportancia(' plaga secundaria ')).toBe('plaga')
  })

  it('reconoce lo benéfico con o sin tilde', () => {
    expect(clasificarImportancia('Benéfico - polinizador')).toBe('benefico')
    expect(clasificarImportancia('BENEFICO - depredador')).toBe('benefico')
  })

  it('no deduce nada que la ficha no diga', () => {
    expect(clasificarImportancia('')).toBeNull()
    expect(clasificarImportancia(undefined)).toBeNull()
    expect(clasificarImportancia('Sin importancia conocida')).toBeNull()
  })
})
```

`frontend/pruebas/BarraConfianza.test.jsx`:

```javascript
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import BarraConfianza, { porcentaje } from '../src/compartido/BarraConfianza.jsx'

describe('BarraConfianza', () => {
  it('siempre escribe el porcentaje', () => {
    render(<BarraConfianza titulo="Seguridad en el orden" valor={0.914} />)
    expect(screen.getByText('91 %')).toBeInTheDocument()
    expect(screen.getByText('Seguridad en el orden')).toBeInTheDocument()
  })

  it('una familia afirmada lo dice con texto, no solo con color', () => {
    render(<BarraConfianza titulo="Familia" valor={0.98} estado="afirmada" />)
    expect(screen.getByText('Afirmada')).toBeInTheDocument()
  })

  it('una familia incierta pide revisar con un especialista', () => {
    render(<BarraConfianza titulo="Familia" valor={0.53} estado="incierta" />)
    expect(screen.getByText('Revisar con especialista')).toBeInTheDocument()
  })

  it('las candidatas no repiten la etiqueta', () => {
    render(<BarraConfianza titulo="Gomphidae" valor={0.53} estado="candidata" />)
    expect(screen.queryByText('Revisar con especialista')).not.toBeInTheDocument()
  })

  it('redondea el porcentaje', () => {
    expect(porcentaje(0.9555)).toBe('96 %')
  })
})
```

`frontend/pruebas/Ficha.test.jsx` (reemplazo completo):

```javascript
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Ficha from '../src/compartido/Ficha.jsx'

const REGISTRO = {
  ID: 'INS-0001',
  Nombre_comun: 'gorgojo del plátano',
  Nombre_cientifico: 'Cosmopolites sordidus',
  Cultivo_asociado: 'plátano',
  Tipo_de_dano: 'perforación del cormo',
  Importancia_economica: 'Plaga',
  Hospedero: 'Musa spp.',
  Localidad: 'Iquitos',
  Estado_biologico: 'adulto',
  Verificado_por: '(pendiente)',
  Archivo_imagen: 'x.jpg',
  Observaciones: 'nota interna',
}

describe('Ficha', () => {
  it('avisa cuando no hay registros, con el texto que se le pase', () => {
    render(<Ficha fichas={[]} vacio="Aún no hay fichas de esta familia en la base." />)
    expect(screen.getByText('Aún no hay fichas de esta familia en la base.')).toBeInTheDocument()
  })

  it('avisa igual si no le pasan nada', () => {
    render(<Ficha />)
    expect(screen.getByText(/no hay registros/i)).toBeInTheDocument()
  })

  it('muestra los datos que le sirven a agronomía', () => {
    render(<Ficha fichas={[REGISTRO]} />)
    expect(screen.getByText('gorgojo del plátano')).toBeInTheDocument()
    expect(screen.getByText('Cosmopolites sordidus')).toBeInTheDocument()
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

  it('marca como plaga lo que la base escribe "Plaga", con mayúscula', () => {
    const { container } = render(<Ficha fichas={[REGISTRO]} />)
    expect(container.querySelector('.chip--plaga')).toHaveTextContent('Plaga')
  })

  it('marca lo benéfico con su detalle', () => {
    render(<Ficha fichas={[{ ...REGISTRO, Importancia_economica: 'Benéfico - polinizador' }]} />)
    expect(screen.getByText('Benéfico - polinizador')).toHaveClass('chip--benefico')
  })

  it('una importancia no reconocida se muestra como dato, sin chip', () => {
    const { container } = render(<Ficha fichas={[{ ...REGISTRO, Importancia_economica: 'Variable' }]} />)
    expect(container.querySelector('.chip')).toBeNull()
    expect(screen.getByText('Variable')).toBeInTheDocument()
  })

  it('acepta un título que aclara de qué taxón son los registros', () => {
    render(<Ficha fichas={[REGISTRO]} titulo="Registros del orden Coleoptera en la base" />)
    expect(screen.getByRole('heading', { name: 'Registros del orden Coleoptera en la base' })).toBeInTheDocument()
  })
})
```

`frontend/pruebas/Resultado.test.jsx` (reemplazo completo):

```javascript
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import Resultado from '../src/compartido/Resultado.jsx'

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
const SIN_FAMILIAS = { ...CERTERO, orden: 'Mantodea', familia: '', familia_incierta: true, top_familias: [] }

describe('Resultado', () => {
  it('no muestra nada sin predicción', () => {
    const { container } = render(<Resultado prediccion={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('muestra la ruta orden → familia y ambas confianzas', () => {
    render(<Resultado prediccion={CERTERO} />)
    expect(screen.getByText('Coleoptera')).toBeInTheDocument()
    expect(screen.getByText('Curculionidae')).toBeInTheDocument()
    expect(screen.getByText('94 %')).toBeInTheDocument()
    expect(screen.getByText('81 %')).toBeInTheDocument()
    expect(screen.getByText('Afirmada')).toBeInTheDocument()
  })

  it('enlaza la familia afirmada con su tarjeta del catálogo', () => {
    render(<Resultado prediccion={CERTERO} />)
    expect(screen.getByRole('link', { name: 'Ver esta familia en el catálogo' })).toHaveAttribute('href', '/#familia-Curculionidae')
  })

  it('con familia incierta no la afirma y muestra las candidatas', () => {
    render(<Resultado prediccion={INCIERTO} />)
    expect(screen.getByText(/no se puede determinar la familia/i)).toBeInTheDocument()
    expect(screen.getByText('Chrysomelidae')).toBeInTheDocument()
    expect(screen.queryByText('Afirmada')).not.toBeInTheDocument()
  })

  it('con familia incierta sigue mostrando el orden y enlaza al orden', () => {
    render(<Resultado prediccion={INCIERTO} />)
    expect(screen.getByText('Coleoptera')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ver este orden en el catálogo' })).toHaveAttribute('href', '/#orden-Coleoptera')
  })

  it('un orden sin familias no se presenta como duda', () => {
    render(<Resultado prediccion={SIN_FAMILIAS} />)
    expect(screen.getByText(/no se clasifica por familia/i)).toBeInTheDocument()
    expect(screen.queryByText(/no se puede determinar/i)).not.toBeInTheDocument()
  })

  it('muestra el chip de plaga solo si la ficha lo dice y la familia está afirmada', () => {
    const conFicha = { ...CERTERO, fichas: [{ ID: '1', Importancia_economica: 'Plaga' }] }
    const { rerender, container } = render(<Resultado prediccion={conFicha} />)
    expect(container.querySelector('.chip--plaga')).not.toBeNull()
    rerender(<Resultado prediccion={{ ...conFicha, familia_incierta: true }} />)
    expect(container.querySelector('.chip--plaga')).toBeNull()
  })

  it('en la portada va sin enlace', () => {
    render(<Resultado prediccion={CERTERO} conEnlace={false} />)
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run (en `frontend/`): `npm run prueba`
Expected: FAIL en `importancia`, `BarraConfianza`, `Ficha` y `Resultado`, porque los archivos de `src/compartido/` todavía no existen.

- [ ] **Step 3: Implementar**

```bash
git rm frontend/src/componentes/Ficha.jsx frontend/src/componentes/Resultado.jsx
```

`frontend/src/compartido/importancia.js`:

```javascript
// La base escribe la importancia a mano ("Plaga", "Benéfico - polinizador"). Se
// normaliza solo para elegir el estilo del chip: el texto que se muestra es el
// de la ficha, y si no se reconoce no se deduce nada.
export function clasificarImportancia(texto) {
  const limpio = (texto ?? '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
  if (limpio.startsWith('plaga')) return 'plaga'
  if (limpio.startsWith('benefico')) return 'benefico'
  return null
}
```

`frontend/src/compartido/BarraConfianza.jsx`:

```javascript
export const porcentaje = (valor) => `${Math.round(valor * 100)} %`

const ETIQUETAS = { afirmada: 'Afirmada', incierta: 'Revisar con especialista' }

// La confianza nunca depende solo del color: el porcentaje, y en la familia la
// etiqueta, van escritos. La barra es un refuerzo visual (aria-hidden).
export default function BarraConfianza({ titulo, valor, estado = 'neutra' }) {
  const etiqueta = ETIQUETAS[estado]
  return (
    <div className={`barra barra--${estado}`}>
      <div className="barra__encabezado">
        <span className="barra__titulo">{titulo}</span>
        <span className="barra__valor">{porcentaje(valor)}</span>
      </div>
      <div className="barra__pista" aria-hidden="true">
        <div className="barra__relleno" style={{ '--valor': valor }} />
      </div>
      {etiqueta && <span className="barra__etiqueta">{etiqueta}</span>}
    </div>
  )
}
```

`frontend/src/compartido/Ficha.jsx`:

```javascript
import { clasificarImportancia } from './importancia.js'

// Campos visibles y su etiqueta, en el orden que le sirve a agronomía. Los de
// control interno (ID, Archivo_imagen, Fuente, Observaciones) no se muestran.
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

export default function Ficha({
  fichas,
  titulo = 'Información biológica',
  vacio = 'No hay registros en la base de datos biológica para este taxón todavía.',
}) {
  if (!fichas || fichas.length === 0) {
    return (
      <section className="ficha">
        <p className="ayuda">{vacio}</p>
      </section>
    )
  }

  return (
    <section className="ficha">
      <h2 className="ficha__titulo">{titulo}</h2>
      {fichas.map((registro) => {
        const tipo = clasificarImportancia(registro.Importancia_economica)
        // Si hay chip, la importancia ya se lee ahí: no se repite en la lista.
        const campos = CAMPOS.filter(
          ([clave]) => registro[clave] && !(tipo && clave === 'Importancia_economica'),
        )
        return (
          <article key={registro.ID} className="ficha__registro">
            {tipo && <span className={`chip chip--${tipo}`}>{registro.Importancia_economica}</span>}
            <dl className="ficha__datos">
              {campos.map(([clave, etiqueta]) => (
                <div key={clave} className="ficha__dato">
                  <dt>{etiqueta}</dt>
                  <dd className={clave === 'Nombre_cientifico' ? 'cientifico' : undefined}>
                    {registro[clave]}
                  </dd>
                </div>
              ))}
            </dl>
          </article>
        )
      })}
    </section>
  )
}
```

`frontend/src/compartido/Resultado.jsx`:

```javascript
import BarraConfianza from './BarraConfianza.jsx'
import { clasificarImportancia } from './importancia.js'

export default function Resultado({ prediccion, conEnlace = true }) {
  if (!prediccion) return null

  const {
    orden,
    confianza_orden,
    familia,
    confianza_familia,
    familia_incierta,
    top_familias,
    fichas = [],
  } = prediccion
  // El backend devuelve familia vacía cuando el orden no tiene familias en el
  // sistema: no es una duda del modelo y no se muestra como tal.
  const sinFamilias = !familia && top_familias.length === 0
  const afirmada = !sinFamilias && !familia_incierta
  // Chip solo si la familia está afirmada y su ficha dice la importancia.
  const importancia = afirmada
    ? fichas.map((f) => f.Importancia_economica).find((t) => clasificarImportancia(t))
    : undefined

  return (
    <section className="resultado" aria-live="polite">
      <p className="resultado__ruta">
        <span className="resultado__nivel">Orden</span>
        <strong>{orden}</strong>
        {afirmada && (
          <>
            <span className="resultado__flecha" aria-hidden="true">
              →
            </span>
            <span className="resultado__nivel">Familia</span>
            <strong>{familia}</strong>
          </>
        )}
      </p>

      {importancia && (
        <span className={`chip chip--${clasificarImportancia(importancia)}`}>{importancia}</span>
      )}

      <BarraConfianza titulo="Seguridad en el orden" valor={confianza_orden} />

      {sinFamilias && (
        <p className="resultado__nota">Este orden no se clasifica por familia en el sistema.</p>
      )}

      {afirmada && (
        <BarraConfianza titulo="Seguridad en la familia" valor={confianza_familia} estado="afirmada" />
      )}

      {!sinFamilias && familia_incierta && (
        <div className="resultado__incierto">
          <BarraConfianza titulo="Seguridad en la familia" valor={confianza_familia} estado="incierta" />
          <p className="resultado__aviso">
            <strong>No se puede determinar la familia con certeza.</strong> Candidatas dentro de{' '}
            {orden}, para revisar con un especialista:
          </p>
          <ul className="resultado__candidatas">
            {top_familias.map(({ familia: nombre, confianza }) => (
              <li key={nombre}>
                <BarraConfianza titulo={nombre} valor={confianza} estado="candidata" />
              </li>
            ))}
          </ul>
        </div>
      )}

      {conEnlace && (
        <a className="resultado__enlace" href={afirmada ? `/#familia-${familia}` : `/#orden-${orden}`}>
          {afirmada ? 'Ver esta familia en el catálogo' : 'Ver este orden en el catálogo'}
        </a>
      )}
    </section>
  )
}
```

Agregar al final de `frontend/src/compartido/base.css`:

```css
/* Barra de confianza */
.barra { display: grid; gap: var(--espacio-1); }
.barra__encabezado { display: flex; justify-content: space-between; gap: var(--espacio-3); font-weight: 700; }
.barra__valor { font-variant-numeric: tabular-nums; }
.barra__pista { height: 10px; overflow: hidden; border-radius: var(--radio-pastilla); background: var(--pista); }
.barra__relleno {
  height: 100%;
  background: var(--petroleo);
  transform-origin: left;
  transform: scaleX(var(--valor));
  animation: llenar 600ms var(--curva-salida);
}
.barra--afirmada .barra__relleno { background: var(--verde-selva); }
.barra--incierta .barra__relleno,
.barra--candidata .barra__relleno { background: var(--amarillo); }
.barra__etiqueta { font-size: 0.875rem; font-weight: 700; }
.barra--afirmada .barra__etiqueta { color: var(--verde-amazonico); }
.barra--incierta .barra__etiqueta { color: var(--ambar-texto); }
.barra--candidata .barra__titulo { font-family: var(--fuente-texto); font-style: italic; font-weight: 400; }

/* Resultado */
.resultado {
  display: grid;
  gap: var(--espacio-4);
  padding: var(--espacio-5);
  border: 1px solid var(--borde);
  border-radius: var(--radio-grande);
  background: var(--superficie);
  box-shadow: var(--sombra);
  color: var(--gris);
  animation: aparecer 320ms var(--curva-salida);
}
.resultado__ruta {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--espacio-2);
  margin: 0;
  font-family: var(--fuente-titulo);
  font-size: 1.375rem;
  color: var(--petroleo);
}
.resultado__ruta strong { overflow-wrap: anywhere; }
.resultado__nivel { font-family: var(--fuente-texto); font-size: 0.875rem; font-weight: 700; color: var(--texto-suave); }
.resultado__flecha { color: var(--verde-amazonico); }
.resultado__nota { margin: 0; color: var(--texto-suave); }
.resultado__incierto { display: grid; gap: var(--espacio-3); padding: var(--espacio-4); border-radius: var(--radio); background: var(--ambar-fondo); }
.resultado__aviso { margin: 0; }
.resultado__candidatas { display: grid; gap: var(--espacio-3); margin: 0; padding: 0; list-style: none; }
.resultado__enlace { font-weight: 700; }

/* Ficha biológica */
.ficha { margin-top: var(--espacio-5); }
.ficha__titulo { font-size: 1.25rem; }
.ficha__registro {
  display: grid;
  gap: var(--espacio-3);
  margin-bottom: var(--espacio-3);
  padding: var(--espacio-4);
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  background: var(--superficie);
}
.ficha__datos { display: grid; grid-template-columns: minmax(8rem, max-content) 1fr; gap: var(--espacio-2) var(--espacio-4); margin: 0; }
.ficha__dato { display: contents; }
.ficha__datos dt { font-weight: 700; color: var(--texto-suave); }
.ficha__datos dd { margin: 0; }
@media (max-width: 480px) {
  .ficha__datos { grid-template-columns: 1fr; gap: 0; }
  .ficha__datos dd { margin-bottom: var(--espacio-2); }
}
```

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run (en `frontend/`): `npm run prueba`
Expected: pasan todas. `SubirFoto.test.jsx` sigue pasando porque no depende de lo movido.

- [ ] **Step 5: Commit**

```bash
git add -A frontend
git commit -m "Frontend: barra de confianza, ficha y resultado rediseñados" -m "La confianza siempre lleva número y etiqueta. El chip de plaga o benéfico sale de lo que dice la ficha, normalizando mayúsculas y tildes: antes se comparaba con 'plaga' exacto y la base escribe 'Plaga', así que nunca se marcaba." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 6: Página de identificación

**Files:**
- Create: `frontend/src/paginas/identificar/{ZonaFoto.jsx, Consejos.jsx, Ejemplos.jsx, identificar.css}`
- Modify (reemplazo completo): `frontend/src/paginas/identificar/Identificar.jsx`, `frontend/src/paginas/identificar/main.jsx`
- Delete: `frontend/src/componentes/SubirFoto.jsx`, `frontend/pruebas/SubirFoto.test.jsx`
- Test: `frontend/pruebas/ZonaFoto.test.jsx`, `frontend/pruebas/Identificar.test.jsx`

**Interfaces:**
- Consumes:
  - `predecir(archivo)` de `compartido/api.js`;
  - `cargarDemostracion()` y `archivoDesdeRuta(ruta, nombre)` de `compartido/datos.js`;
  - `Resultado`, `Ficha`, `Cabecera` y `Pie`;
  - `demostracion.json` (tarea 3), con `ejemplos[]`, donde cada uno tiene `{archivo, credito, licencia, real: {orden, familia}}`.
- Produces:
  - `ZonaFoto({ alSeleccionar(archivo: File), ocupado: boolean, vistaPrevia: string | null })`
  - `Consejos({ abierto: boolean })`
  - `Ejemplos({ ejemplos, alElegir(ejemplo), ocupado })`

- [ ] **Step 1: Escribir las pruebas que fallan**

`frontend/pruebas/ZonaFoto.test.jsx`:

```javascript
import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ZonaFoto from '../src/paginas/identificar/ZonaFoto.jsx'

const foto = () => new File(['x'], 'insecto.jpg', { type: 'image/jpeg' })
const entradas = (container) => container.querySelectorAll('input[type="file"]')

afterEach(() => {
  vi.restoreAllMocks()
  delete window.matchMedia
})

describe('ZonaFoto', () => {
  it('entrega el archivo elegido', () => {
    const alSeleccionar = vi.fn()
    const { container } = render(<ZonaFoto alSeleccionar={alSeleccionar} ocupado={false} vistaPrevia={null} />)
    const archivo = foto()
    fireEvent.change(entradas(container)[0], { target: { files: [archivo] } })
    expect(alSeleccionar).toHaveBeenCalledWith(archivo)
  })

  it('acepta solo los formatos que el backend admite', () => {
    const { container } = render(<ZonaFoto alSeleccionar={vi.fn()} ocupado={false} vistaPrevia={null} />)
    expect(entradas(container)[0]).toHaveAttribute('accept', 'image/jpeg,image/png,image/webp')
  })

  it('deja listo un selector nuevo para poder elegir otra vez la misma foto', () => {
    const { container } = render(<ZonaFoto alSeleccionar={vi.fn()} ocupado={false} vistaPrevia={null} />)
    const antes = entradas(container)[0]
    fireEvent.change(antes, { target: { files: [foto()] } })
    expect(entradas(container)[0]).not.toBe(antes)
  })

  it('acepta una foto arrastrada', () => {
    const alSeleccionar = vi.fn()
    render(<ZonaFoto alSeleccionar={alSeleccionar} ocupado={false} vistaPrevia={null} />)
    const archivo = foto()
    fireEvent.drop(screen.getByText(/arrastra una foto/i), { dataTransfer: { files: [archivo] } })
    expect(alSeleccionar).toHaveBeenCalledWith(archivo)
  })

  it('no acepta fotos mientras identifica', () => {
    const alSeleccionar = vi.fn()
    const { container } = render(<ZonaFoto alSeleccionar={alSeleccionar} ocupado vistaPrevia="blob:1" />)
    expect(entradas(container)[0]).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent('Identificando…')
  })

  it('ofrece la cámara solo en pantallas táctiles', () => {
    window.matchMedia = vi.fn(() => ({ matches: true }))
    const { container } = render(<ZonaFoto alSeleccionar={vi.fn()} ocupado={false} vistaPrevia={null} />)
    expect(screen.getByText('Tomar foto')).toBeInTheDocument()
    expect(entradas(container)[1]).toHaveAttribute('capture', 'environment')
  })

  it('en computadora no muestra la cámara', () => {
    render(<ZonaFoto alSeleccionar={vi.fn()} ocupado={false} vistaPrevia={null} />)
    expect(screen.queryByText('Tomar foto')).not.toBeInTheDocument()
  })
})
```

`frontend/pruebas/Identificar.test.jsx`:

```javascript
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/compartido/api.js', () => ({ predecir: vi.fn() }))
vi.mock('../src/compartido/datos.js', () => ({
  cargarDemostracion: vi.fn(),
  archivoDesdeRuta: vi.fn(),
}))

import { predecir } from '../src/compartido/api.js'
import { archivoDesdeRuta, cargarDemostracion } from '../src/compartido/datos.js'
import Identificar from '../src/paginas/identificar/Identificar.jsx'

const AFIRMADA = {
  orden: 'Hymenoptera', confianza_orden: 0.99, familia: 'Apidae', confianza_familia: 0.98,
  familia_incierta: false, top_familias: [{ familia: 'Apidae', confianza: 0.98 }],
  fichas: [{ ID: 'INS-0003', Nombre_comun: 'abeja melífera', Importancia_economica: 'Benéfico - polinizador' }],
}
const INCIERTA = {
  orden: 'Odonata', confianza_orden: 0.91, familia: 'Gomphidae', confianza_familia: 0.53,
  familia_incierta: true,
  top_familias: [{ familia: 'Gomphidae', confianza: 0.53 }, { familia: 'Coenagrionidae', confianza: 0.43 }],
  fichas: [],
}
const EJEMPLO = {
  archivo: '/catalogo/demo/abeja.webp', credito: '(c) Ana', licencia: 'cc-by',
  real: { orden: 'Hymenoptera', familia: 'Apidae' },
}
const foto = () => new File(['x'], 'insecto.jpg', { type: 'image/jpeg' })

async function montar() {
  const vista = render(<Identificar />)
  await screen.findByText('Probar con un ejemplo')
  return vista
}

describe('Identificar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    cargarDemostracion.mockResolvedValue({ ejemplos: [EJEMPLO] })
    URL.createObjectURL = vi.fn(() => 'blob:1')
    URL.revokeObjectURL = vi.fn()
  })

  it('en estado vacío muestra consejos abiertos y ejemplos', async () => {
    const { container } = await montar()
    expect(container.querySelector('details.consejos')).toHaveAttribute('open')
    expect(screen.getByText(/Aquí aparecerá/)).toBeInTheDocument()
  })

  it('identifica una foto elegida y muestra resultado y ficha', async () => {
    predecir.mockResolvedValue(AFIRMADA)
    const { container } = await montar()
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [foto()] } })
    // "Apidae" también es el rótulo del botón de ejemplo: se busca por la ficha.
    expect(await screen.findByText('abeja melífera')).toBeInTheDocument()
    expect(screen.getByText('Afirmada')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Información biológica' })).toBeInTheDocument()
    expect(container.querySelector('details.consejos')).not.toHaveAttribute('open')
  })

  it('con familia incierta titula las fichas como registros del orden', async () => {
    predecir.mockResolvedValue({ ...INCIERTA, fichas: [{ ID: '9', Nombre_comun: 'libélula' }] })
    const { container } = await montar()
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [foto()] } })
    expect(await screen.findByRole('heading', { name: 'Registros del orden Odonata en la base' })).toBeInTheDocument()
  })

  it('muestra el error del backend y reintenta con la misma foto', async () => {
    predecir.mockRejectedValueOnce(new Error('la foto pesa más de 20 MB: usa una más liviana'))
    predecir.mockResolvedValueOnce(AFIRMADA)
    const { container } = await montar()
    const archivo = foto()
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [archivo] } })
    expect(await screen.findByRole('alert')).toHaveTextContent('20 MB')
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('abeja melífera')).toBeInTheDocument()
    expect(predecir).toHaveBeenLastCalledWith(archivo)
  })

  it('un ejemplo se envía de verdad a la API', async () => {
    const archivo = foto()
    archivoDesdeRuta.mockResolvedValue(archivo)
    predecir.mockResolvedValue(AFIRMADA)
    await montar()
    fireEvent.click(screen.getByRole('button', { name: /Apidae/ }))
    expect(await screen.findByText('abeja melífera')).toBeInTheDocument()
    expect(archivoDesdeRuta).toHaveBeenCalledWith('/catalogo/demo/abeja.webp', 'abeja.webp')
    expect(predecir).toHaveBeenCalledWith(archivo)
  })

  it('si la foto de ejemplo no carga, lo dice y no queda identificando', async () => {
    archivoDesdeRuta.mockRejectedValue(new Error('No se pudo cargar la foto de ejemplo.'))
    await montar()
    fireEvent.click(screen.getByRole('button', { name: /Apidae/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('foto de ejemplo')
    expect(screen.queryByText('Identificando…')).not.toBeInTheDocument()
  })

  it('"Identificar otra foto" vuelve al estado vacío', async () => {
    predecir.mockResolvedValue(AFIRMADA)
    const { container } = await montar()
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [foto()] } })
    fireEvent.click(await screen.findByRole('button', { name: 'Identificar otra foto' }))
    expect(screen.getByText(/Aquí aparecerá/)).toBeInTheDocument()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:1')
  })

  it('sin demostración disponible la página funciona igual', async () => {
    cargarDemostracion.mockRejectedValue(new Error('No se encontró el contenido del catálogo.'))
    render(<Identificar />)
    await act(async () => {})
    expect(screen.queryByText('Probar con un ejemplo')).not.toBeInTheDocument()
    expect(screen.getByText('Elegir foto')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run (en `frontend/`): `npm run prueba`
Expected: FAIL en `ZonaFoto` (no existe el archivo) y en `Identificar` (la página mínima no tiene esos elementos).

- [ ] **Step 3: Implementar**

```bash
git rm frontend/src/componentes/SubirFoto.jsx frontend/pruebas/SubirFoto.test.jsx
```

La carpeta `src/componentes/` queda vacía y se elimina.

`frontend/src/paginas/identificar/ZonaFoto.jsx`:

```javascript
import { useEffect, useState } from 'react'

// Los formatos que el backend sabe abrir. HEIC queda fuera a propósito.
const TIPOS = 'image/jpeg,image/png,image/webp'

function esTactil() {
  return window.matchMedia?.('(pointer: coarse)')?.matches === true
}

export default function ZonaFoto({ alSeleccionar, ocupado, vistaPrevia }) {
  // Cambiar la clave monta selectores nuevos y vacíos: sin esto, elegir otra
  // vez la misma foto (por ejemplo, para reintentar) no avisa nada.
  const [clave, setClave] = useState(0)
  const [arrastrando, setArrastrando] = useState(false)
  const [tactil, setTactil] = useState(false)

  useEffect(() => setTactil(esTactil()), [])

  function entregar(archivo) {
    if (!archivo || ocupado) return
    setClave((valor) => valor + 1)
    alSeleccionar(archivo)
  }

  return (
    <div
      className={`zona${arrastrando ? ' zona--arrastrando' : ''}`}
      onDragOver={(evento) => {
        evento.preventDefault()
        setArrastrando(true)
      }}
      onDragLeave={() => setArrastrando(false)}
      onDrop={(evento) => {
        evento.preventDefault()
        setArrastrando(false)
        entregar(evento.dataTransfer?.files?.[0])
      }}
    >
      <div className="zona__marco marco">
        {vistaPrevia ? (
          <img className="zona__foto" src={vistaPrevia} alt="Foto elegida" />
        ) : (
          <p className="zona__vacio">Arrastra una foto aquí o elígela desde tu equipo.</p>
        )}
        {ocupado && (
          <div className="zona__ocupado" role="status">
            <span className="zona__indicador" aria-hidden="true" />
            Identificando…
          </div>
        )}
      </div>

      <div className="zona__acciones" key={clave}>
        <label className="boton boton--principal">
          Elegir foto
          <input
            className="visualmente-oculto"
            type="file"
            accept={TIPOS}
            disabled={ocupado}
            onChange={(evento) => entregar(evento.target.files?.[0])}
          />
        </label>
        {tactil && (
          <label className="boton boton--secundario">
            Tomar foto
            <input
              className="visualmente-oculto"
              type="file"
              accept="image/*"
              capture="environment"
              disabled={ocupado}
              onChange={(evento) => entregar(evento.target.files?.[0])}
            />
          </label>
        )}
      </div>
    </div>
  )
}
```

`frontend/src/paginas/identificar/Consejos.jsx`:

```javascript
export default function Consejos({ abierto }) {
  return (
    <details className="consejos" open={abierto}>
      <summary>Consejos para una buena foto</summary>
      <ul>
        <li>Luz pareja, sin sombras duras: mejor a la sombra o con el cielo nublado.</li>
        <li>El insecto centrado y ocupando buena parte de la foto.</li>
        <li>Un fondo simple, que no se confunda con el insecto.</li>
        <li>
          JPG, PNG o WEBP de hasta 20 MB. Las fotos HEIC del iPhone no sirven: envíala como JPG
          o elige “Más compatible” en los ajustes de la cámara.
        </li>
      </ul>
    </details>
  )
}
```

`frontend/src/paginas/identificar/Ejemplos.jsx`:

```javascript
export default function Ejemplos({ ejemplos, alElegir, ocupado }) {
  if (!ejemplos?.length) return null
  return (
    <section className="ejemplos" aria-labelledby="titulo-ejemplos">
      <h2 id="titulo-ejemplos" className="ejemplos__titulo">
        Probar con un ejemplo
      </h2>
      <ul className="ejemplos__lista">
        {ejemplos.map((ejemplo) => (
          <li key={ejemplo.archivo}>
            <button
              type="button"
              className="ejemplos__boton"
              disabled={ocupado}
              onClick={() => alElegir(ejemplo)}
            >
              <img src={ejemplo.archivo} alt="" loading="lazy" />
              <span className="cientifico">{ejemplo.real.familia || ejemplo.real.orden}</span>
            </button>
          </li>
        ))}
      </ul>
      <p className="ejemplos__nota">
        Fotos que el modelo no vio al entrenar. Créditos:{' '}
        {ejemplos.map((e) => `${e.credito} (${e.licencia.toUpperCase()})`).join('; ')}.
      </p>
    </section>
  )
}
```

`frontend/src/paginas/identificar/Identificar.jsx` (reemplazo completo):

```javascript
import { useEffect, useRef, useState } from 'react'
import { predecir } from '../../compartido/api.js'
import Cabecera from '../../compartido/Cabecera.jsx'
import { archivoDesdeRuta, cargarDemostracion } from '../../compartido/datos.js'
import Ficha from '../../compartido/Ficha.jsx'
import Pie from '../../compartido/Pie.jsx'
import Resultado from '../../compartido/Resultado.jsx'
import Consejos from './Consejos.jsx'
import Ejemplos from './Ejemplos.jsx'
import ZonaFoto from './ZonaFoto.jsx'

export default function Identificar() {
  const [estado, setEstado] = useState('vacio') // vacio | identificando | resultado | error
  const [prediccion, setPrediccion] = useState(null)
  const [error, setError] = useState('')
  const [vistaPrevia, setVistaPrevia] = useState(null)
  const [ejemplos, setEjemplos] = useState([])
  // Cómo volver a obtener el archivo del último intento, para "Reintentar".
  const ultimoIntento = useRef(null)
  // URL creada con createObjectURL: se libera al reemplazarla o al salir.
  const urlPropia = useRef(null)

  useEffect(() => {
    cargarDemostracion()
      .then((demostracion) => setEjemplos(demostracion.ejemplos))
      .catch(() => setEjemplos([]))
    return () => urlPropia.current && URL.revokeObjectURL(urlPropia.current)
  }, [])

  function mostrarFoto(url, esPropia) {
    if (urlPropia.current) URL.revokeObjectURL(urlPropia.current)
    urlPropia.current = esPropia ? url : null
    setVistaPrevia(url)
  }

  async function identificar(obtenerArchivo) {
    ultimoIntento.current = obtenerArchivo
    setEstado('identificando')
    setError('')
    setPrediccion(null)
    try {
      const archivo = await obtenerArchivo()
      setPrediccion(await predecir(archivo))
      setEstado('resultado')
    } catch (e) {
      setError(e.message)
      setEstado('error')
    }
  }

  function alElegirArchivo(archivo) {
    mostrarFoto(URL.createObjectURL(archivo), true)
    identificar(async () => archivo)
  }

  function alElegirEjemplo(ejemplo) {
    mostrarFoto(ejemplo.archivo, false)
    const nombre = ejemplo.archivo.split('/').pop()
    identificar(() => archivoDesdeRuta(ejemplo.archivo, nombre))
  }

  function reiniciar() {
    mostrarFoto(null, false)
    setPrediccion(null)
    setError('')
    setEstado('vacio')
  }

  const ocupado = estado === 'identificando'
  const deOrden = prediccion && (prediccion.familia_incierta || !prediccion.familia)

  return (
    <>
      <Cabecera pagina="identificar" />
      <main id="contenido" className="contenedor identificar">
        <div className="identificar__intro">
          <h1>Identificar un insecto</h1>
          <p>Sube una foto: el sistema propone el orden y, si está seguro, la familia.</p>
        </div>

        <div className="identificar__columnas">
          <div className="identificar__foto">
            <ZonaFoto alSeleccionar={alElegirArchivo} ocupado={ocupado} vistaPrevia={vistaPrevia} />
            <Consejos abierto={estado === 'vacio'} />
            <Ejemplos ejemplos={ejemplos} alElegir={alElegirEjemplo} ocupado={ocupado} />
          </div>

          <div className="identificar__resultado">
            {estado === 'vacio' && (
              <p className="identificar__espera">
                Aquí aparecerán el orden, la familia y la ficha biológica de la base.
              </p>
            )}
            {estado === 'error' && (
              <div className="aviso aviso--error" role="alert">
                <p>{error}</p>
                <button
                  type="button"
                  className="boton boton--secundario"
                  onClick={() => identificar(ultimoIntento.current)}
                >
                  Reintentar
                </button>
              </div>
            )}
            {estado === 'resultado' && (
              <>
                <Resultado prediccion={prediccion} />
                <Ficha
                  fichas={prediccion.fichas}
                  titulo={
                    deOrden ? `Registros del orden ${prediccion.orden} en la base` : 'Información biológica'
                  }
                  vacio="Aún no hay fichas de este insecto en la base de datos biológica."
                />
                <button type="button" className="boton boton--secundario" onClick={reiniciar}>
                  Identificar otra foto
                </button>
              </>
            )}
          </div>
        </div>
      </main>
      <Pie />
    </>
  )
}
```

`frontend/src/paginas/identificar/main.jsx` (agregar la hoja de la página):

```javascript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../compartido/base.css'
import './identificar.css'
import Identificar from './Identificar.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Identificar />
  </StrictMode>,
)
```

`frontend/src/paginas/identificar/identificar.css`:

```css
.identificar { padding-block: var(--espacio-6) var(--espacio-8); }
.identificar__intro p { color: var(--texto-suave); font-size: 1.125rem; }

.identificar__columnas { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--espacio-6); }
@media (min-width: 900px) {
  .identificar__columnas { grid-template-columns: minmax(0, 5fr) minmax(0, 6fr); align-items: start; }
  .identificar__resultado { position: sticky; top: 88px; }
}
.identificar__foto { display: grid; gap: var(--espacio-5); }
.identificar__resultado > .boton { margin-top: var(--espacio-4); }
.identificar__espera {
  max-width: none;
  margin: 0;
  padding: var(--espacio-6);
  border: 1px dashed rgba(46, 46, 46, 0.3);
  border-radius: var(--radio-grande);
  background: var(--superficie);
  color: var(--texto-suave);
}

/* Zona de la foto */
.zona {
  display: grid;
  gap: var(--espacio-4);
  padding: var(--espacio-4);
  border: 1px solid var(--borde);
  border-radius: var(--radio-grande);
  background: var(--superficie);
  transition: border-color 200ms var(--curva-salida), background-color 200ms var(--curva-salida);
}
.zona--arrastrando { border-color: var(--verde-amazonico); background: var(--selva-fondo); }
.zona__marco { display: grid; place-items: center; aspect-ratio: 4 / 3; }
.zona__foto { width: 100%; height: 100%; object-fit: contain; border-radius: var(--radio); background: var(--fondo); }
.zona__vacio { max-width: 28ch; margin: 0; text-align: center; color: var(--texto-suave); }
.zona__ocupado {
  position: absolute;
  inset: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--espacio-3);
  border-radius: var(--radio);
  background: rgba(15, 61, 62, 0.78);
  color: #fff;
  font-weight: 700;
}
.zona__indicador {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: var(--verde-lima);
  border-radius: 50%;
  animation: girar 900ms linear infinite;
}
@keyframes girar { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) {
  .zona__indicador { animation: none; border-top-color: rgba(255, 255, 255, 0.3); }
}
.zona__acciones { display: flex; flex-wrap: wrap; gap: var(--espacio-3); }
.zona__acciones .boton { flex: 1 1 10rem; }

/* Consejos */
.consejos { padding: var(--espacio-2) var(--espacio-4); border: 1px solid var(--borde); border-radius: var(--radio); background: var(--superficie); }
.consejos summary { display: flex; align-items: center; min-height: 44px; font-weight: 700; color: var(--petroleo); cursor: pointer; }
.consejos ul { display: grid; gap: var(--espacio-2); margin: var(--espacio-2) 0 var(--espacio-3); padding-left: 1.2rem; }

/* Ejemplos */
.ejemplos__titulo { font-size: 1.125rem; }
.ejemplos__lista { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: var(--espacio-3); margin: 0; padding: 0; list-style: none; }
.ejemplos__boton {
  display: grid;
  gap: var(--espacio-2);
  width: 100%;
  min-height: 44px;
  padding: var(--espacio-2);
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  background: var(--superficie);
  color: var(--gris);
  font: inherit;
  font-size: 0.9375rem;
  text-align: left;
  cursor: pointer;
}
.ejemplos__boton:hover { border-color: var(--verde-amazonico); }
.ejemplos__boton:disabled { opacity: 0.55; cursor: not-allowed; }
.ejemplos__boton img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 6px; }
.ejemplos__nota { margin-top: var(--espacio-3); font-size: 0.8125rem; color: var(--texto-suave); }
```

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run (en `frontend/`): `npm run prueba`
Expected: pasan todas.

Run (en `frontend/`): `npm run build`
Expected: sin errores.

- [ ] **Step 5: Commit**

```bash
git add -A frontend
git commit -m "Frontend: página de identificación con todos sus estados" -m "Elegir, tomar o arrastrar una foto; consejos para una buena foto; ejemplos del conjunto de prueba que se envían de verdad a la API; resultado con la ruta orden → familia; errores con Reintentar. La vista previa libera su URL al cambiar de foto." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 7: Página de presentación y catálogo

**Files:**
- Create: `frontend/src/paginas/inicio/{Portada.jsx, ComoFunciona.jsx, Desempeno.jsx, Catalogo.jsx, TarjetaClase.jsx, PanelFichas.jsx, inicio.css}`
- Modify (reemplazo completo): `frontend/src/paginas/inicio/Inicio.jsx`, `frontend/src/paginas/inicio/main.jsx`
- Test: `frontend/pruebas/Catalogo.test.jsx`, `frontend/pruebas/Inicio.test.jsx`

**Interfaces:**
- Consumes:
  - `cargarCatalogo()` y `cargarDemostracion()`;
  - `obtenerTaxon(orden, familia)` de `compartido/api.js`;
  - `Resultado`, `Ficha`, `Cabecera`, `Pie` y `porcentaje`;
  - las formas de `catalogo.json` y `demostracion.json` (tarea 3).
- Produces:
  - `Catalogo({ catalogo: object | null, error: string })`
  - `TarjetaClase({ clase, alAbrir })`
  - `PanelFichas({ clase, alCerrar })`
  - anclas `#catalogo`, `#familia-<Nombre>` y `#orden-<Nombre>`, que usan la cabecera y la tarea 6.

- [ ] **Step 1: Escribir las pruebas que fallan**

`frontend/pruebas/Catalogo.test.jsx`:

```javascript
import { fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/compartido/api.js', () => ({ obtenerTaxon: vi.fn() }))

import { obtenerTaxon } from '../src/compartido/api.js'
import Catalogo from '../src/paginas/inicio/Catalogo.jsx'

const foto = { archivo: '/catalogo/fotos/x.webp', ancho: 640, alto: 480, credito: '', licencia: 'cc-by', url_origen: '' }
const CATALOGO = {
  corrida: 'v4',
  metricas: {},
  ordenes: [
    { nombre: 'Coleoptera', nombre_comun: 'escarabajos', tiene_familias: true },
    { nombre: 'Mantodea', nombre_comun: 'mantis', tiene_familias: false },
  ],
  clases: [
    { id: 'familia-Curculionidae', tipo: 'familia', nombre: 'Curculionidae', nombre_comun: 'gorgojos',
      orden: 'Coleoptera', provisional: false, f1: 0.92, fotos_entrenamiento: 600,
      foto: { ...foto, credito: '(c) Ana' } },
    { id: 'familia-Coccinellidae', tipo: 'familia', nombre: 'Coccinellidae', nombre_comun: 'mariquitas',
      orden: 'Coleoptera', provisional: true, f1: 0.95, fotos_entrenamiento: 580,
      foto: { ...foto, credito: 'Autor no registrado' } },
    { id: 'orden-Mantodea', tipo: 'orden', nombre: 'Mantodea', nombre_comun: 'mantis',
      orden: 'Mantodea', provisional: false, f1: 0.87, fotos_entrenamiento: 817, foto },
  ],
}

describe('Catalogo', () => {
  beforeEach(() => vi.clearAllMocks())

  it('agrupa por orden y muestra cada clase con su F1 y el crédito de la foto', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    const tarjeta = document.getElementById('familia-Curculionidae')
    expect(within(tarjeta).getByText('gorgojos')).toBeInTheDocument()
    expect(within(tarjeta).getByText('92 %')).toBeInTheDocument()
    expect(within(tarjeta).getByText(/\(c\) Ana · CC-BY/)).toBeInTheDocument()
  })

  it('marca las familias provisionales', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    expect(within(document.getElementById('familia-Coccinellidae')).getByText('Provisional')).toBeInTheDocument()
    expect(within(document.getElementById('familia-Curculionidae')).queryByText('Provisional')).not.toBeInTheDocument()
  })

  it('un orden sin familias dice que se identifica solo hasta orden', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    expect(within(document.getElementById('orden-Mantodea')).getByText(/solo hasta orden/i)).toBeInTheDocument()
  })

  it('filtra por orden', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.click(screen.getByRole('button', { name: 'Mantodea' }))
    expect(document.getElementById('familia-Curculionidae')).toBeNull()
    expect(document.getElementById('orden-Mantodea')).not.toBeNull()
    expect(screen.getByRole('button', { name: 'Mantodea' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('busca por nombre común sin importar tildes ni mayúsculas', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'MARIQUÍTAS' } })
    expect(document.getElementById('familia-Coccinellidae')).not.toBeNull()
    expect(document.getElementById('familia-Curculionidae')).toBeNull()
  })

  it('avisa cuando la búsqueda no encuentra nada', () => {
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'zzz' } })
    expect(screen.getByText(/no hay clases que coincidan/i)).toBeInTheDocument()
  })

  it('abre las fichas de la familia y se cierra con Escape', async () => {
    obtenerTaxon.mockResolvedValue({ fichas: [{ ID: '1', Nombre_comun: 'gorgojo del plátano' }] })
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.click(within(document.getElementById('familia-Curculionidae')).getByRole('button', { name: 'Ver fichas' }))
    expect(await screen.findByText('gorgojo del plátano')).toBeInTheDocument()
    expect(obtenerTaxon).toHaveBeenCalledWith('Coleoptera', 'Curculionidae')
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('las fichas de un orden sin familias se piden por orden', async () => {
    obtenerTaxon.mockResolvedValue({ fichas: [] })
    render(<Catalogo catalogo={CATALOGO} error="" />)
    fireEvent.click(within(document.getElementById('orden-Mantodea')).getByRole('button', { name: 'Ver fichas' }))
    expect(await screen.findByText('Aún no hay fichas de este orden en la base.')).toBeInTheDocument()
    expect(obtenerTaxon).toHaveBeenCalledWith('Mantodea', '')
  })

  it('si el catálogo no carga, lo explica', () => {
    render(<Catalogo catalogo={null} error="No se encontró el contenido del catálogo." />)
    expect(screen.getByRole('alert')).toHaveTextContent('No se encontró')
  })
})
```

`frontend/pruebas/Inicio.test.jsx`:

```javascript
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/compartido/datos.js', () => ({ cargarCatalogo: vi.fn(), cargarDemostracion: vi.fn() }))
vi.mock('../src/compartido/api.js', () => ({ obtenerTaxon: vi.fn() }))

import { cargarCatalogo, cargarDemostracion } from '../src/compartido/datos.js'
import Inicio from '../src/paginas/inicio/Inicio.jsx'

const PRED = (familia, conf, incierta) => ({
  orden: 'Hymenoptera', confianza_orden: 0.99, familia, confianza_familia: conf,
  familia_incierta: incierta, top_familias: [{ familia, confianza: conf }],
})
const DEMO = {
  principal: { archivo: '/catalogo/demo/a.webp', credito: '(c) Ana', licencia: 'cc-by',
    real: { orden: 'Hymenoptera', familia: 'Apidae' }, prediccion: PRED('Apidae', 0.98, false) },
  incierto: { archivo: '/catalogo/demo/b.webp', credito: '(c) Luis', licencia: 'cc0',
    real: { orden: 'Hymenoptera', familia: 'Vespidae' }, prediccion: PRED('Vespidae', 0.52, true) },
  ejemplos: [],
}
const CATALOGO = {
  corrida: 'v4_convnext_t_288',
  metricas: { n_prueba: 5165, exactitud_familia: 0.9216, top3_familia: 0.958, f1_orden: 0.935,
    f1_familia: 0.921, umbral: 0.7, responde: 0.94, acierta_cuando_responde: 0.955 },
  ordenes: [], clases: [],
}

describe('Inicio', () => {
  beforeEach(() => {
    cargarCatalogo.mockResolvedValue(CATALOGO)
    cargarDemostracion.mockResolvedValue(DEMO)
  })

  it('la portada lleva a la herramienta', async () => {
    render(<Inicio />)
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent(/orden y la familia/)
    const acciones = screen.getAllByRole('link', { name: 'Identificar un insecto' })
    expect(acciones.every((a) => a.getAttribute('href') === '/identificar/')).toBe(true)
  })

  it('la demostración es un resultado real rotulado, con el crédito de la foto', async () => {
    render(<Inicio />)
    expect(await screen.findByText('Resultado real del modelo con esta foto')).toBeInTheDocument()
    expect(screen.getByText(/\(c\) Ana · CC-BY/)).toBeInTheDocument()
  })

  it('cómo funciona muestra un caso real en que no afirma la familia', async () => {
    render(<Inicio />)
    expect(await screen.findByText(/prefiere no afirmar la familia/)).toBeInTheDocument()
    expect(screen.getByText(/no se puede determinar la familia/i)).toBeInTheDocument()
  })

  it('las cifras salen del catálogo y aclaran que son de fotos de catálogo', async () => {
    render(<Inicio />)
    expect(await screen.findByText('92 %')).toBeInTheDocument()
    expect(screen.getByText('95.5 %')).toBeInTheDocument()
    expect(screen.getByText('96 %')).toBeInTheDocument()
    expect(screen.getByText(/evaluación con fotos de campo está pendiente/i)).toBeInTheDocument()
  })

  it('sin catálogo ni demostración la portada sigue en pie', async () => {
    cargarCatalogo.mockRejectedValue(new Error('No se encontró el contenido del catálogo.'))
    cargarDemostracion.mockRejectedValue(new Error('x'))
    render(<Inicio />)
    expect(await screen.findByRole('alert')).toHaveTextContent('No se encontró')
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run (en `frontend/`): `npm run prueba`
Expected: FAIL en `Catalogo` (no existe) y en `Inicio` (la página mínima no carga datos).

- [ ] **Step 3: Implementar los componentes**

`frontend/src/paginas/inicio/Portada.jsx`:

```javascript
import Resultado from '../../compartido/Resultado.jsx'

export default function Portada({ demostracion, nFamilias }) {
  const principal = demostracion?.principal
  return (
    <section className="portada">
      <div className="contenedor portada__rejilla">
        <div className="portada__texto">
          <h1>Identifica el orden y la familia de un insecto con una foto</h1>
          <p className="portada__bajada">
            Sistema de Inteligencia Artificial para la identificación de órdenes y familias de
            insectos de importancia económica de la Amazonía peruana.
          </p>
          <div className="portada__acciones">
            <a className="boton boton--claro" href="/identificar/">
              Identificar un insecto
            </a>
            <a className="boton boton--contorno" href="#catalogo">
              {nFamilias ? `Ver las ${nFamilias} familias` : 'Ver las familias'}
            </a>
          </div>
        </div>

        {principal && (
          <figure className="portada__demo">
            <div className="marco marco--claro">
              <img
                src={principal.archivo}
                alt={`Foto de ejemplo: ${principal.real.familia || principal.real.orden}`}
              />
            </div>
            <figcaption className="portada__leyenda">
              <p className="portada__rotulo">Resultado real del modelo con esta foto</p>
              <Resultado prediccion={principal.prediccion} conEnlace={false} />
              <p className="credito">
                Foto: {principal.credito} · {principal.licencia.toUpperCase()}
              </p>
            </figcaption>
          </figure>
        )}
      </div>
    </section>
  )
}
```

`frontend/src/paginas/inicio/ComoFunciona.jsx`:

```javascript
import Resultado from '../../compartido/Resultado.jsx'

export default function ComoFunciona({ demostracion }) {
  const incierto = demostracion?.incierto
  return (
    <section className="contenedor como" aria-labelledby="titulo-como">
      <h2 id="titulo-como">Cómo funciona</h2>
      <ol className="como__pasos">
        <li>
          <h3>Subes una foto</h3>
          <p>Desde el celular o la computadora, con el insecto bien visible.</p>
        </li>
        <li>
          <h3>El modelo decide el orden</h3>
          <p>Por ejemplo, si es un escarabajo (Coleoptera) o una mariposa (Lepidoptera).</p>
        </li>
        <li>
          <h3>Y la familia dentro de ese orden</h3>
          <p>
            Solo la afirma si está seguro en al menos un 70 %. Si no, muestra las tres familias
            más probables para que las revise un especialista.
          </p>
        </li>
      </ol>

      {incierto && (
        <figure className="como__ejemplo">
          <div className="marco">
            <img src={incierto.archivo} alt={`Foto de ejemplo: ${incierto.real.orden}`} loading="lazy" />
          </div>
          <figcaption className="como__leyenda">
            <p className="como__rotulo">Un caso real en que el sistema prefiere no afirmar la familia</p>
            <Resultado prediccion={incierto.prediccion} conEnlace={false} />
            <p className="credito">
              Foto: {incierto.credito} · {incierto.licencia.toUpperCase()}
            </p>
          </figcaption>
        </figure>
      )}
    </section>
  )
}
```

`frontend/src/paginas/inicio/Desempeno.jsx`:

```javascript
const pct = (valor, decimales = 0) => `${(valor * 100).toFixed(decimales)} %`

export default function Desempeno({ metricas }) {
  return (
    <section className="desempeno" aria-labelledby="titulo-desempeno">
      <div className="contenedor desempeno__rejilla">
        <div>
          <h2 id="titulo-desempeno">Qué tan bien funciona</h2>
          <p>
            Lo medimos con {metricas.n_prueba} fotos que el modelo nunca vio al entrenar, de
            fotógrafos que tampoco vio.
          </p>
          <p className="desempeno__aviso">
            Medido con fotos de catálogo. La evaluación con fotos de campo está pendiente.
          </p>
        </div>
        <dl className="desempeno__datos">
          <div>
            <dt>Acierta la familia</dt>
            <dd className="desempeno__cifra">{pct(metricas.exactitud_familia)}</dd>
            <dd className="desempeno__detalle">de las fotos de prueba.</dd>
          </div>
          <div>
            <dt>Cuando se anima a responder</dt>
            <dd className="desempeno__cifra">{pct(metricas.acierta_cuando_responde, 1)}</dd>
            <dd className="desempeno__detalle">
              de acierto. Responde en el {pct(metricas.responde)} de los casos; en el resto dice
              que no está seguro.
            </dd>
          </div>
          <div>
            <dt>Entre sus tres primeras opciones</dt>
            <dd className="desempeno__cifra">{pct(metricas.top3_familia)}</dd>
            <dd className="desempeno__detalle">de las veces está la familia correcta.</dd>
          </div>
        </dl>
      </div>
    </section>
  )
}
```

`frontend/src/paginas/inicio/TarjetaClase.jsx`:

```javascript
import { porcentaje } from '../../compartido/BarraConfianza.jsx'

export default function TarjetaClase({ clase, alAbrir }) {
  const { id, tipo, nombre, nombre_comun, orden, provisional, f1, foto } = clase
  return (
    <article id={id} className="tarjeta">
      <img
        className="tarjeta__foto"
        src={foto.archivo}
        alt={`Ejemplo de ${nombre}`}
        width={foto.ancho}
        height={foto.alto}
        loading="lazy"
        decoding="async"
      />
      <div className="tarjeta__cuerpo">
        <p className="tarjeta__orden">{tipo === 'familia' ? `Orden ${orden}` : 'Orden'}</p>
        <h4 className="tarjeta__nombre cientifico">{nombre}</h4>
        {nombre_comun && <p className="tarjeta__comun">{nombre_comun}</p>}
        {provisional && <span className="chip chip--provisional">Provisional</span>}
        {tipo === 'orden' && <p className="tarjeta__nota">Se identifica solo hasta orden.</p>}
        {f1 != null && (
          <div className="tarjeta__f1">
            <span>Qué tan bien la distingue (F1)</span>
            <strong>{porcentaje(f1)}</strong>
            <div className="barra__pista" aria-hidden="true">
              <div className="barra__relleno" style={{ '--valor': f1 }} />
            </div>
          </div>
        )}
        <p className="credito">
          Foto: {foto.credito} · {foto.licencia.toUpperCase()}
        </p>
        <button type="button" className="boton boton--secundario boton--chico" onClick={alAbrir}>
          Ver fichas
        </button>
      </div>
    </article>
  )
}
```

`frontend/src/paginas/inicio/PanelFichas.jsx`:

```javascript
import { useEffect, useRef, useState } from 'react'
import { obtenerTaxon } from '../../compartido/api.js'
import Ficha from '../../compartido/Ficha.jsx'

export default function PanelFichas({ clase, alCerrar }) {
  const [estado, setEstado] = useState({ cargando: true, fichas: [], error: '' })
  const botonCerrar = useRef(null)

  useEffect(() => {
    let vigente = true
    const familia = clase.tipo === 'familia' ? clase.nombre : ''
    obtenerTaxon(clase.orden, familia)
      .then((datos) => vigente && setEstado({ cargando: false, fichas: datos.fichas, error: '' }))
      .catch((e) => vigente && setEstado({ cargando: false, fichas: [], error: e.message }))
    return () => {
      vigente = false
    }
  }, [clase])

  useEffect(() => {
    // Foco al panel al abrir y de vuelta al botón que lo abrió al cerrar.
    const previo = document.activeElement
    botonCerrar.current?.focus()
    const alTeclear = (evento) => evento.key === 'Escape' && alCerrar()
    document.addEventListener('keydown', alTeclear)
    return () => {
      document.removeEventListener('keydown', alTeclear)
      previo?.focus?.()
    }
  }, [alCerrar])

  return (
    <div className="panel__fondo" onClick={alCerrar}>
      <div
        className="panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-panel"
        onClick={(evento) => evento.stopPropagation()}
      >
        <div className="panel__encabezado">
          <h2 id="titulo-panel" className="cientifico">
            {clase.nombre}
          </h2>
          <button ref={botonCerrar} type="button" className="boton boton--secundario boton--chico" onClick={alCerrar}>
            Cerrar
          </button>
        </div>
        {estado.cargando && <p role="status">Cargando fichas…</p>}
        {estado.error && (
          <p className="aviso aviso--error" role="alert">
            {estado.error}
          </p>
        )}
        {!estado.cargando && !estado.error && (
          <Ficha
            fichas={estado.fichas}
            titulo="Fichas de la base de datos biológica"
            vacio={
              clase.tipo === 'familia'
                ? 'Aún no hay fichas de esta familia en la base.'
                : 'Aún no hay fichas de este orden en la base.'
            }
          />
        )}
      </div>
    </div>
  )
}
```

`frontend/src/paginas/inicio/Catalogo.jsx`:

```javascript
import { useCallback, useMemo, useState } from 'react'
import PanelFichas from './PanelFichas.jsx'
import TarjetaClase from './TarjetaClase.jsx'

const normalizar = (texto) =>
  (texto ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')

export default function Catalogo({ catalogo, error }) {
  const [orden, setOrden] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [abierta, setAbierta] = useState(null)
  const cerrarPanel = useCallback(() => setAbierta(null), [])

  const grupos = useMemo(() => {
    if (!catalogo) return []
    const consulta = normalizar(busqueda.trim())
    return catalogo.ordenes
      .filter((o) => !orden || o.nombre === orden)
      .map((o) => ({
        ...o,
        clases: catalogo.clases.filter(
          (c) =>
            c.orden === o.nombre &&
            (!consulta || normalizar(`${c.nombre} ${c.nombre_comun}`).includes(consulta)),
        ),
      }))
      .filter((grupo) => grupo.clases.length > 0)
  }, [catalogo, orden, busqueda])

  return (
    <section id="catalogo" className="catalogo" aria-labelledby="titulo-catalogo">
      <div className="contenedor">
        <h2 id="titulo-catalogo">Catálogo de familias</h2>
        <p className="catalogo__bajada">
          Las familias y órdenes que el sistema reconoce, con una foto de ejemplo y qué tan bien
          las distingue el modelo.
        </p>

        {error && (
          <p className="aviso aviso--error" role="alert">
            {error}
          </p>
        )}
        {!catalogo && !error && <p role="status">Cargando el catálogo…</p>}

        {catalogo && (
          <>
            <div className="catalogo__filtros">
              <label className="campo">
                <span>Buscar</span>
                <input
                  type="search"
                  value={busqueda}
                  onChange={(evento) => setBusqueda(evento.target.value)}
                  placeholder="Nombre científico o común"
                />
              </label>
              <div className="catalogo__ordenes" role="group" aria-label="Filtrar por orden">
                <button type="button" className="filtro" aria-pressed={orden === ''} onClick={() => setOrden('')}>
                  Todos
                </button>
                {catalogo.ordenes.map((o) => (
                  <button
                    key={o.nombre}
                    type="button"
                    className="filtro"
                    aria-pressed={orden === o.nombre}
                    onClick={() => setOrden(o.nombre)}
                  >
                    {o.nombre}
                  </button>
                ))}
              </div>
            </div>

            {grupos.length === 0 && (
              <p className="catalogo__vacio">No hay clases que coincidan con la búsqueda.</p>
            )}

            {grupos.map((grupo) => (
              <div key={grupo.nombre} className="catalogo__grupo">
                <h3 className="catalogo__orden">
                  {grupo.nombre} <span>{grupo.nombre_comun}</span>
                </h3>
                <ul className="catalogo__lista">
                  {grupo.clases.map((clase) => (
                    <li key={clase.id}>
                      <TarjetaClase clase={clase} alAbrir={() => setAbierta(clase)} />
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </>
        )}
      </div>
      {abierta && <PanelFichas clase={abierta} alCerrar={cerrarPanel} />}
    </section>
  )
}
```

`frontend/src/paginas/inicio/Inicio.jsx` (reemplazo completo):

```javascript
import { useEffect, useState } from 'react'
import Cabecera from '../../compartido/Cabecera.jsx'
import { cargarCatalogo, cargarDemostracion } from '../../compartido/datos.js'
import Pie from '../../compartido/Pie.jsx'
import Catalogo from './Catalogo.jsx'
import ComoFunciona from './ComoFunciona.jsx'
import Desempeno from './Desempeno.jsx'
import Portada from './Portada.jsx'

export default function Inicio() {
  const [catalogo, setCatalogo] = useState(null)
  const [errorCatalogo, setErrorCatalogo] = useState('')
  const [demostracion, setDemostracion] = useState(null)

  useEffect(() => {
    cargarCatalogo()
      .then(setCatalogo)
      .catch((e) => setErrorCatalogo(e.message))
    cargarDemostracion()
      .then(setDemostracion)
      .catch(() => setDemostracion(null))
  }, [])

  // Un enlace como /#familia-Apidae (desde la herramienta) llega a su tarjeta
  // cuando el catálogo ya se dibujó.
  useEffect(() => {
    if (!catalogo || !window.location.hash) return
    document.getElementById(window.location.hash.slice(1))?.scrollIntoView?.({ block: 'center' })
  }, [catalogo])

  const nFamilias = catalogo?.clases.filter((c) => c.tipo === 'familia').length

  return (
    <>
      <Cabecera pagina="inicio" />
      <main id="contenido">
        <Portada demostracion={demostracion} nFamilias={nFamilias} />
        <ComoFunciona demostracion={demostracion} />
        {catalogo && <Desempeno metricas={catalogo.metricas} />}
        <Catalogo catalogo={catalogo} error={errorCatalogo} />
      </main>
      <Pie corrida={catalogo?.corrida} />
    </>
  )
}
```

`frontend/src/paginas/inicio/main.jsx` (agregar la hoja de la página):

```javascript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '../../compartido/base.css'
import './inicio.css'
import Inicio from './Inicio.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Inicio />
  </StrictMode>,
)
```

`frontend/src/paginas/inicio/inicio.css`:

```css
/* Portada: franja Azul Petróleo a todo el ancho */
.portada { padding-block: var(--espacio-8); background: var(--petroleo); color: #fff; }
.portada h1 { color: #fff; }
.portada__rejilla { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--espacio-7); align-items: center; }
@media (min-width: 960px) { .portada__rejilla { grid-template-columns: minmax(0, 6fr) minmax(0, 5fr); } }
.portada__bajada { font-size: 1.1875rem; color: var(--texto-sobre-petroleo); }
.portada__acciones { display: flex; flex-wrap: wrap; gap: var(--espacio-3); margin-top: var(--espacio-5); }
.portada__demo { display: grid; gap: var(--espacio-4); margin: 0; }
.marco--claro::before { --color: var(--verde-lima); }
.portada__leyenda { display: grid; gap: var(--espacio-2); }
.portada__rotulo { margin: 0; font-weight: 700; color: var(--verde-lima); }
.portada .credito { color: var(--texto-sobre-petroleo); }

/* Cómo funciona: una secuencia real de tres pasos */
.como { display: grid; gap: var(--espacio-6); padding-block: var(--espacio-8); }
@media (min-width: 960px) {
  .como { grid-template-columns: minmax(0, 6fr) minmax(0, 5fr); align-items: start; }
  .como > h2 { grid-column: 1 / -1; }
}
.como__pasos { display: grid; gap: var(--espacio-5); margin: 0; padding: 0; list-style: none; counter-reset: paso; }
.como__pasos li { display: grid; grid-template-columns: 3rem 1fr; column-gap: var(--espacio-4); counter-increment: paso; }
.como__pasos li::before {
  content: counter(paso);
  grid-row: span 2;
  display: grid;
  place-items: center;
  width: 3rem;
  height: 3rem;
  border-radius: 50%;
  background: var(--verde-amazonico);
  color: #fff;
  font-family: var(--fuente-titulo);
  font-size: 1.25rem;
  font-weight: 700;
}
.como__pasos h3 { margin-bottom: var(--espacio-1); }
.como__pasos p { margin: 0; color: var(--texto-suave); }
.como__ejemplo { display: grid; gap: var(--espacio-3); margin: 0; }
.como__leyenda { display: grid; gap: var(--espacio-2); }
.como__rotulo { margin: 0; font-weight: 700; color: var(--ambar-texto); }

/* Qué tan bien funciona: texto y datos, sin cifras gigantes */
.desempeno { padding-block: var(--espacio-8); border-block: 1px solid var(--borde); background: var(--superficie); }
.desempeno__rejilla { display: grid; gap: var(--espacio-6); }
@media (min-width: 960px) { .desempeno__rejilla { grid-template-columns: minmax(0, 5fr) minmax(0, 6fr); align-items: start; } }
.desempeno__aviso { display: inline-block; padding: var(--espacio-3) var(--espacio-4); border-radius: var(--radio); background: var(--ambar-fondo); color: var(--ambar-texto); font-weight: 700; }
.desempeno__datos { display: grid; gap: var(--espacio-4); margin: 0; }
.desempeno__datos > div {
  display: grid;
  grid-template-columns: 7.5rem 1fr;
  column-gap: var(--espacio-4);
  align-items: baseline;
  padding-bottom: var(--espacio-4);
  border-bottom: 1px solid var(--borde);
}
.desempeno__datos dt { grid-column: 1 / -1; margin-bottom: var(--espacio-1); font-weight: 700; color: var(--petroleo); }
.desempeno__datos dd { margin: 0; }
.desempeno__cifra { font-family: var(--fuente-titulo); font-size: 2rem; font-weight: 700; color: var(--verde-amazonico); font-variant-numeric: tabular-nums; }
.desempeno__detalle { color: var(--texto-suave); }

/* Catálogo */
.catalogo { padding-block: var(--espacio-8); }
.catalogo__bajada { color: var(--texto-suave); }
.catalogo__filtros { display: grid; gap: var(--espacio-4); margin-block: var(--espacio-5); }
.campo { display: grid; gap: var(--espacio-1); max-width: 28rem; font-weight: 700; color: var(--petroleo); }
.campo input {
  min-height: 44px;
  padding: 0 var(--espacio-3);
  border: 1.5px solid rgba(46, 46, 46, 0.35);
  border-radius: var(--radio);
  background: var(--superficie);
  color: var(--gris);
  font: inherit;
  font-weight: 400;
}
.campo input::placeholder { color: var(--texto-suave); }
.catalogo__ordenes { display: flex; flex-wrap: wrap; gap: var(--espacio-2); }
.filtro {
  min-height: 44px;
  padding: 0 var(--espacio-4);
  border: 1.5px solid rgba(46, 46, 46, 0.2);
  border-radius: var(--radio-pastilla);
  background: var(--superficie);
  color: var(--gris);
  font: inherit;
  font-size: 0.9375rem;
  cursor: pointer;
}
.filtro:hover { border-color: var(--verde-amazonico); }
.filtro[aria-pressed='true'] { border-color: var(--verde-amazonico); background: var(--verde-amazonico); color: #fff; }
.catalogo__grupo { margin-top: var(--espacio-7); }
.catalogo__orden { display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--espacio-3); }
.catalogo__orden span { font-family: var(--fuente-texto); font-size: 1rem; font-weight: 400; color: var(--texto-suave); }
.catalogo__lista { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 250px), 1fr)); gap: var(--espacio-5); margin: 0; padding: 0; list-style: none; }
.catalogo__vacio { color: var(--texto-suave); }

.tarjeta {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  background: var(--superficie);
  scroll-margin-top: 96px;
}
.tarjeta:target { outline: 3px solid var(--verde-selva); outline-offset: 2px; }
.tarjeta__foto { width: 100%; height: auto; aspect-ratio: 4 / 3; object-fit: cover; background: var(--pista); }
.tarjeta__cuerpo { display: flex; flex: 1; flex-direction: column; gap: var(--espacio-2); padding: var(--espacio-4); }
.tarjeta__orden { margin: 0; font-size: 0.875rem; color: var(--texto-suave); }
.tarjeta__nombre { margin: 0; font-size: 1.1875rem; font-weight: 700; overflow-wrap: anywhere; }
.tarjeta__comun { margin: 0; }
.tarjeta__nota { margin: 0; font-size: 0.9375rem; color: var(--texto-suave); }
.tarjeta__f1 { display: grid; grid-template-columns: 1fr auto; gap: var(--espacio-1) var(--espacio-3); font-size: 0.9375rem; }
.tarjeta__f1 .barra__pista { grid-column: 1 / -1; }
.tarjeta__f1 strong { font-variant-numeric: tabular-nums; }
.tarjeta .credito { margin-top: auto; }
.tarjeta .boton { align-self: flex-start; }

/* Panel de fichas */
.panel__fondo {
  position: fixed;
  inset: 0;
  z-index: var(--z-fondo-panel);
  display: grid;
  place-items: center;
  padding: var(--espacio-4);
  background: rgba(15, 61, 62, 0.55);
}
.panel {
  width: min(100%, 40rem);
  max-height: min(90vh, 48rem);
  overflow: auto;
  padding: var(--espacio-5);
  border-radius: var(--radio-grande);
  background: var(--fondo);
  box-shadow: 0 16px 40px rgba(15, 61, 62, 0.18);
  animation: aparecer 240ms var(--curva-salida);
}
.panel__encabezado { display: flex; align-items: center; justify-content: space-between; gap: var(--espacio-3); }
.panel__encabezado h2 { margin: 0; }
```

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run (en `frontend/`): `npm run prueba`
Expected: pasan todas.

Run (en `frontend/`): `npm run build`
Expected: sin errores.

- [ ] **Step 5: Commit**

```bash
git add -A frontend
git commit -m "Frontend: página de presentación con demostración real y catálogo" -m "Portada con un resultado real del modelo sobre una foto de prueba; cómo funciona, con un caso real en que no afirma la familia; cifras de la corrida vigente con la aclaración de que son de catálogo; y el catálogo por orden, con búsqueda, F1, crédito de cada foto y las fichas de la base." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 8: Verificación en navegador, detector de diseño y documentación

**Files:**
- Modify: `README.md` (sección "Ejecutar el prototipo"), `CLAUDE.md` (procedimiento de corrida nueva, paso 7)
- Modify (solo si la verificación encuentra fallas): los archivos de las tareas 4 a 7

**Interfaces:**
- Consumes: todo lo anterior.

- [ ] **Step 1: Suite completa**

Run: `.venv\Scripts\python -m pytest -q`
Expected: pasan todas.

Run (en `frontend/`): `npm run prueba && npm run build`
Expected: pasan todas y se construye sin errores.

- [ ] **Step 2: Peso de la página**

Run (en `frontend/`): `ls -l dist/assets/*.js`
Expected: cada JS menor a 250 KB sin comprimir. Si alguno lo supera, anotar en el ledger qué lo agranda antes de seguir.

- [ ] **Step 3: Servidor real y verificación visual**

Levantar en segundo plano: `.venv\Scripts\python -m uvicorn backend.app:app_produccion --factory --port 8000`

Con la extensión de Chrome (`tabs_context_mcp`, `navigate`, `resize_window`, `computer` screenshot, `find` y `file_upload`), capturar a **1440 px** y a **390 px** de ancho, en una sola ronda. Guardar las capturas en `.impeccable/review/`:
1. `http://127.0.0.1:8000/`: portada, cómo funciona, desempeño y catálogo, con desplazamiento hasta el final (`desktop.png` y `mobile.png`).
2. En el catálogo: filtrar por un orden, buscar "mariquitas" y abrir las fichas de Apidae.
3. `http://127.0.0.1:8000/identificar`, sin barra: tiene que cargar la página.
4. Tocar un ejemplo afirmado, un ejemplo incierto, y subir `../insectos-demo/ejemplos/ejemplo_Coleoptera_Coleoptera_0162.jpg`.
5. Enviar un archivo que no es imagen (por ejemplo `README.md`) y comprobar el mensaje en español y "Reintentar".

Revisar en las capturas:
- ningún texto se desborda (por ejemplo, "Heterotermitidae" en el celular);
- la cabecera en el celular muestra el símbolo más el botón;
- no hay halos en el logo;
- en el resultado incierto, el bloque es amarillo, con las candidatas;
- las fotos del catálogo tienen su crédito;
- el foco con el teclado se ve (recorrer con Tab la cabecera, los filtros y una tarjeta).

Arreglar en un solo lote lo que se encuentre, volver a construir y confirmar con una segunda ronda. **Máximo dos rondas.**

- [ ] **Step 4: Detector de patrones de diseño**

Run: `C:/Users/DANIEL/.claude/skills/impeccable/scripts/impeccable.cmd detect --json frontend/src`, con `sh` o `bash` según lo que resuelva.
Expected: un JSON de hallazgos. Corregir lo mecánico (por ejemplo, un contraste o un patrón prohibido) y anotar el resto en el ledger para la revisión final.

- [ ] **Step 5: Documentación**

En `README.md`, dentro de "Ejecutar el prototipo", después de la tabla de artefactos, agregar:

```markdown
### Contenido de la web

El catálogo, las fotos y la demostración se generan desde los datos y la corrida vigente:

```powershell
.venv\Scripts\python -m pipeline.marca_web --hoja ..\imagenes_web\imagen_1.png
.venv\Scripts\python -m pipeline.catalogo_web --desempeno docs\desempeno_por_clase_v4.md
```

Las fotos elegidas a mano van en `frontend/catalogo_preferencias.yaml`; la hoja de contactos queda en `datos/catalogo_contactos.jpg`.
```

En `CLAUDE.md`, en "Cuando llegue una corrida nueva", reemplazar el paso 7 por:

```markdown
7. Si la corrida nueva pasa a ser la vigente, cambiar `CORRIDA_VIGENTE` en `backend/app.py` y `MODELO_DIR` en `iniciar.bat`, y regenerar el contenido de la web: `python -m pipeline.catalogo_web --desempeno docs/desempeno_por_clase_<vN>.md`. El prototipo lee la resolución del propio ONNX.
```

- [ ] **Step 6: Commit**

```bash
git add -A README.md CLAUDE.md frontend
git commit -m "Frontend: verificación en navegador y documentación del contenido de la web" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Si el paso 3 o el 4 no cambiaron código, el commit lleva solo la documentación.

---

## Task 9: Revisión final de diseño y DESIGN.md

**Files:**
- Create: `DESIGN.md` y `.impeccable/design.json`, los escribe el documentador
- Modify: lo que la revisión marque como corrección material

- [ ] **Step 1: Revisión independiente de diseño**

Lanzar el agente `impeccable-finish-reviewer`, en contexto nuevo, con:
- el pedido original del usuario;
- la especificación y `PRODUCT.md`;
- las capturas de `.impeccable/review/`;
- los hallazgos del detector;
- la ruta `C:/Users/DANIEL/.claude/skills/impeccable/reference/craft-floor.md`;
- la nota "construido directamente desde el código, sin bocetos; la referencia visual es el prototipo de Stitch `projects/16595468791669318138`, usado como guía".

- [ ] **Step 2: Actuar según el veredicto**

| Veredicto | Qué hacer |
| --- | --- |
| **ship** | Seguir al paso 3. |
| **fix** | Aplicar las correcciones en un lote, volver a capturar y pedir el veredicto sobre esas correcciones. Máximo dos rondas. |
| **recapture** | Volver a capturar y pedir una revisión completa. |
| **rebuild** | Rehacer las regiones indicadas y pedir una revisión completa. |

Cada corrección que toque comportamiento lleva su prueba primero, y la suite tiene que quedar en verde.

- [ ] **Step 3: DESIGN.md**

Lanzar el agente `impeccable-documenter` con la raíz del proyecto, `frontend/` como artefacto, `PRODUCT.md` y la especificación. Tiene que escribir `DESIGN.md` y `.impeccable/design.json` a partir de lo construido.

Verificar que `DESIGN.md` tenga los tokens de color con sus valores, la tipografía, los componentes y el movimiento.

- [ ] **Step 4: Commit final**

```bash
git add DESIGN.md .impeccable/design.json frontend
git commit -m "Diseño: revisión final y DESIGN.md del sistema construido" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

`.impeccable/review/` contiene capturas de trabajo: no se versiona. Agregar `.impeccable/review/` a `.gitignore` en este mismo commit.
