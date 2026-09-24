# Rediseño del frontend: INSECTIA

- **Fecha:** 2026-09-24.
- **Estado:** diseño aprobado por partes en conversación; pendiente de revisión escrita.
- **Contexto de producto:** `PRODUCT.md`, con usuarios, propósito, compromisos de marca, evidencia disponible y principios.
- **Referencia visual:** el prototipo de Stitch `projects/16595468791669318138`, usado como guía y no como copia.

## 1. Objetivo

Convertir el prototipo funcional (plan 03) en la interfaz pública de **INSECTIA**, con la marca provista por el usuario. Tiene dos páginas: una de **presentación**, que explica el proyecto a un jurado o un estudiante, y otra de **identificación**, pensada para usar en campo desde el celular. Todo lo que se muestre tiene que ser verdadero.

**Éxito:**
- Un visitante nuevo entiende en segundos qué hace el sistema y llega a identificar un insecto.
- Un agrónomo al sol lee el resultado sin esfuerzo.
- La interfaz nunca afirma algo que el modelo o la base no dicen.

## 2. Alcance

**Dentro:**
- Dos páginas nuevas.
- Sistema visual con la paleta del usuario.
- Recursos de marca optimizados.
- Catálogo de familias generado por script.
- Todos los estados del flujo de identificación.
- Pruebas y verificación en navegador.
- `DESIGN.md`.

**Fuera:**
- Cambios en la API o en el modelo.
- Usuarios y sesiones.
- Modo sin conexión.
- Identificación de especie, mapas de calor, cajas sobre la foto y GPS.
- Recomendaciones de manejo integrado de plagas.
- Reportes en PDF.
- Despliegue en la nube.

**Tomado del prototipo de Stitch:**
- la estructura por franjas;
- el tono científico;
- la barra de confianza por nivel;
- las esquinas de encuadre como motivo;
- el protocolo de buenas fotos;
- el catálogo con fotos.

**Descartado del prototipo, por falso para este producto:**
- las cifras inventadas (96.4 %, 42 familias, "Offline", < 1.2 s);
- certificaciones y alianzas (SENASA, IIAP);
- el usuario con sesión iniciada;
- la especie, los mapas de calor y el GPS;
- la cámara web con "sensor macro";
- las recomendaciones de manejo integrado de plagas;
- el PDF.

## 3. Arquitectura

### 3.1 Dos páginas de Vite

`frontend/vite.config.js` declara dos entradas:

| Ruta | Archivo | Modo |
| --- | --- | --- |
| `/` | `frontend/index.html` → `src/paginas/inicio/main.jsx` | Presentación: convencer y orientar |
| `/identificar/` | `frontend/identificar/index.html` → `src/paginas/identificar/main.jsx` | Herramienta: completar una tarea |

- Comparten `src/compartido/`: cabecera, pie, estilos base, tokens y el cliente de la API (`api.js`).
- No se agrega ningún enrutador. FastAPI ya sirve `frontend/dist/identificar/index.html` en `/identificar/`, porque `StaticFiles(html=True)` resuelve carpetas con `index.html`. La navegación entre páginas es un enlace normal.

### 3.2 Catálogo generado: `pipeline/catalogo_web.py`

**Entradas:**
- `ontologia/clases.yaml`: nombre, nombre común y marca de provisional.
- `modelo/<corrida>/etiquetas.json`.
- `docs/desempeno_por_clase_<vN>.md`: F1 por clase de la corrida vigente.
- `datos/splits/{train,test}.csv`: fotos, licencia y atribución.
- `datos/curado/`: las imágenes.

**Salida en `frontend/public/catalogo/`:**
- `catalogo.json`: la lista de las 38 familias y los 6 órdenes sin familias. Cada entrada lleva:
  - `tipo`: `familia` u `orden`;
  - `nombre` y `nombre_comun`;
  - `orden` y `orden_nombre_comun`;
  - `provisional`;
  - `f1`, de la corrida indicada en `corrida`;
  - `fotos_entrenamiento`;
  - `foto`, con `archivo`, `credito`, `licencia` y `url_origen`.
- Una imagen WebP por clase de unos 640 px de lado mayor, con un objetivo de 40 a 60 KB.
- `demostracion.json`: el resultado real del modelo para la foto de la primera vista y para las fotos de "Probar con un ejemplo".

**Reglas de elección de la foto:**
- **Catálogo:** fotos del conjunto de entrenamiento, con este orden de preferencia de licencia: CC0, CC BY, CC BY-SA, y después las demás. A igual licencia, gana la de mayor resolución.
- **Primera vista y ejemplos:** fotos del **conjunto de prueba**, que el modelo nunca vio, para que la demostración sea honesta.
- `catalogo_preferencias.yaml` permite fijar una foto por clase, con su `obs_id` o `archivo`, sin tocar código.

**Hoja de contactos:** el script genera `catalogo_contactos.jpg`, fuera de `public/` y sin versionar, para que el usuario revise las 44 fotos.

**Demostración precalculada:** el script pasa las fotos de prueba elegidas por el ONNX de la corrida vigente, con el mismo `ServicioInsectos` del backend, y guarda el resultado. Ninguna cifra de demostración se escribe a mano.

**Se vuelve a correr cuando cambia la corrida vigente.**

### 3.3 Recursos de marca: `pipeline/marca_web.py`

- `imagenes_web/logo_1.png` y `favicon.png` no se usan: el 94 % y el 99.8 % de sus píxeles son semitransparentes, restos de un recorte de fondo.
- La fuente es `imagenes_web/imagen_1.png`, con el logo sobre un fondo casi blanco y uniforme (#FCFCFA). El script:
  1. recorta el logo completo (símbolo y "INSECTIA") y el símbolo solo;
  2. quita el fondo con un umbral suave de distancia al color de fondo, sin halos y con los bordes suavizados;
  3. exporta WebP y PNG transparentes, en 1x y 2x, a `frontend/public/marca/`;
  4. compone el favicon: el símbolo sobre un cuadrado redondeado Azul Petróleo, en `favicon.ico` (16/32/48), `apple-touch-icon.png` (180) e `icon-192.png`/`icon-512.png`, más `manifest.webmanifest`.
- Los originales quedan fuera del repositorio. El script recibe su ruta como argumento.
- Si más adelante llega un SVG o un PNG con transparencia limpia, se reemplaza la fuente sin cambiar nada más.

### 3.4 Fuentes locales

- **Lexend** para títulos y **Atkinson Hyperlegible Next** para el texto, vía `@fontsource`. Solo se incluyen los pesos que se usan.
- No hay ninguna dependencia de internet en tiempo de ejecución.

### 3.5 Lo que no cambia

- La API: `/salud`, `/clases`, `/predecir`, `/taxon/{orden}` y `/resumen`.
- Las reglas de incertidumbre (`UMBRAL_FAMILIA` = 0.7).
- El frontend no decide taxonomía: muestra lo que responden la API y el `catalogo.json` generado.

## 4. Sistema visual

**Escena:** un agrónomo con el celular a pleno sol en una parcela, y un jurado frente a un proyector en un aula iluminada. Por eso el tema es **claro**, con contraste alto.

### 4.1 Color

Contrastes medidos con WCAG 2.x:

| Uso | Color | Contraste |
| --- | --- | --- |
| Fondo de página | #F6F8F5, blanco con un leve tinte hacia el verde de la marca, no crema | — |
| Superficies (tarjetas, paneles) | #FFFFFF | — |
| Texto de cuerpo | Gris Oscuro #2E2E2E | 12.7:1 sobre el fondo |
| Títulos | Azul Petróleo #0F3D3E | 11.2:1 |
| Acción principal (fondo del botón) | Verde Amazónico #0B5E3B, con texto blanco | 7.8:1 |
| Enlaces y texto de acento | Verde Amazónico #0B5E3B | 7.3:1 |
| Franjas de marca | Azul Petróleo #0F3D3E, con texto blanco | 11.9:1 |
| Acentos sobre las franjas | Verde Lima #A3D977 (7.3:1) y Amarillo #F4B400 (6.5:1) | — |

**Reglas:**
- **Verde Selva, Verde Lima y Amarillo nunca van como texto sobre fondo claro,** porque dan entre 1.5 y 2.8:1. Sobre fondo claro se usan solo como relleno de barras, chips e íconos.
- **Significados fijos:**
  - Verde Selva #4CAF50 significa "respuesta afirmada";
  - Amarillo #F4B400 significa "incierta, revisar con especialista" y también "plaga", en un chip amarillo con texto #2E2E2E (7.4:1).
- La confianza nunca se comunica solo con color: siempre lleva el porcentaje escrito y una etiqueta de texto.
- **Estrategia:** la presentación es *comprometida*, con franjas Azul Petróleo que ocupan regiones completas. La identificación es *contenida*: neutros más un acento, y color solo donde informa.

### 4.2 Tipografía

- **Títulos: Lexend**, pesos 500 y 700. Hace eco de las letras del logo. Tamaños con `clamp()`, con un máximo de 3.5 rem en el título principal. `text-wrap: balance`. Espaciado entre letras nunca menor a −0.02 em.
- **Texto: Atkinson Hyperlegible Next**, pesos 400 y 700. Mínimo de 16 px en el celular. `text-wrap: pretty` y líneas de 65 a 75 caracteres como máximo. Cifras tabulares (`font-variant-numeric: tabular-nums`) en porcentajes y métricas.
- Los nombres científicos van en cursiva.

### 4.3 Forma y componentes

- **Radios:** 8 px en botones, campos y tarjetas; 16 px en contenedores grandes y paneles; 9999 px solo en chips de estado.
- **Bordes y sombras:** borde fino de 1 px `rgba(46,46,46,.08)` y sombra mínima. No hay relieves marcados, efectos de vidrio ni bordes laterales de color.
- **Barra de confianza:** una pista clara con el relleno en Verde Selva (afirmada) o Amarillo (incierta), más el porcentaje escrito y la etiqueta "Afirmada" o "Revisar con especialista".
- **Esquinas de encuadre** tomadas del logo: marco de la vista previa y de la foto de la primera vista.
- **Zonas táctiles** de al menos 44 × 44 px.
- **Foco visible:** halo de 2 px en Verde Lima con separación. Sobre fondo claro se complementa con un contorno Verde Amazónico para no depender del lima.
- **Escala de `z-index`** semántica: cabecera fija, panel de fichas y avisos.

### 4.4 Movimiento

- **Qué se anima:** la aparición del resultado (opacidad y desplazamiento corto), el llenado de las barras de confianza y el indicador "Identificando…".
- **Curvas:** de salida exponencial (ease-out-quart), entre 200 y 400 ms. Sin rebotes.
- **Movimiento reducido:** `prefers-reduced-motion: reduce` deja solo transiciones instantáneas o fundidos.
- **El contenido es visible por defecto:** ninguna animación condiciona que algo se vea.

### 4.5 Evitado a propósito

- cifras gigantes con degradado ("hero-metric");
- grillas de tarjetas idénticas con ícono y texto;
- rótulos pequeños en mayúsculas encima de cada sección;
- efectos de vidrio;
- texto con degradado;
- bordes laterales de color;
- fondo crema.

## 5. Página de presentación (`/`)

1. **Cabecera fija y delgada:**
   - Logo completo a la izquierda, y navegación con "Inicio", "Catálogo" (ancla `#catalogo`) y el botón "Identificar un insecto" (→ `/identificar/`).
   - En el celular queda el símbolo más el botón.
2. **Primera vista, en una franja Azul Petróleo a todo el ancho:**
   - Título: "Identifica el orden y la familia de un insecto con una foto".
   - Bajada de la marca.
   - Dos acciones: "Identificar un insecto" (principal) y "Ver las 38 familias" (→ `#catalogo`).
   - Demostración: una foto del conjunto de prueba con la tarjeta de resultado real de `demostracion.json`, rotulada "Resultado real del modelo con esta foto", con el crédito de la foto.
3. **Cómo funciona, en tres pasos numerados** (es una secuencia real):
   1. Subes una foto.
   2. El modelo decide el orden.
   3. El modelo decide la familia dentro de ese orden. Si su seguridad es menor al 70 %, muestra tres candidatas en vez de afirmar.

   El tercer paso se ilustra con un caso incierto real de `demostracion.json`.
4. **Qué tan bien funciona:** un bloque sobrio, sin cifras gigantes, que dice que en 5 165 fotos de prueba que el modelo nunca vio:
   - acierta la familia el 92 % de las veces;
   - cuando responde (el 94 % de los casos), acierta el 95.5 %;
   - la familia correcta está entre sus tres primeras opciones el 96 % de las veces.

   Con la aclaración visible: "Medido con fotos de catálogo. La evaluación con fotos de campo está pendiente". Las cifras salen de `modelo/<corrida>/evaluacion.json` y de `docs/desempeno_por_clase_<vN>.md`, a través de `catalogo.json`, sin escribirse a mano.
5. **Catálogo** (`#catalogo`, reemplaza a `Explorador.jsx`):
   - Agrupado por orden, con filtro por orden y búsqueda por nombre científico o común.
   - **Tarjeta de familia:**
     - la foto, con carga diferida y su crédito;
     - el nombre científico en cursiva y el nombre común;
     - el orden;
     - la barra "Qué tan bien la reconoce", con el F1 escrito;
     - el chip "Provisional" cuando corresponde.
   - Al tocar la tarjeta se abre un panel (`<dialog>`) con las fichas de `/taxon/{orden}?familia=`. Si no hay fichas, dice "Aún no hay fichas de esta familia en la base".
   - Los órdenes sin familias aparecen como tarjeta de orden, con la nota "Se identifica solo hasta orden".
   - Cada tarjeta tiene el ancla `#familia-<Nombre>` (o `#orden-<Nombre>`) para enlazarla desde la herramienta.
6. **Pie:**
   - UNAP, Proyecto Formativo INAAM–FISI y Facultad de Agronomía.
   - "Fotos: iNaturalist, con el crédito de cada autor".
   - Versión del modelo y enlace a la herramienta.
   - **No lleva nombres de personas.**

## 6. Página de identificación (`/identificar/`)

**Distribución:**
- **En computadora:** dos columnas, con la foto a la izquierda y el resultado a la derecha.
- **En el celular:** una columna, con la foto arriba y el resultado debajo; la acción principal queda al alcance del pulgar.

**Zona de la foto:**
- "Elegir foto" (`accept="image/jpeg,image/png,image/webp"`), "Tomar foto" (`capture="environment"`, visible solo en pantallas táctiles) y arrastrar y soltar en computadora.
- La vista previa lleva las esquinas de encuadre como marco.
- **"Probar con un ejemplo":** 3 o 4 fotos del conjunto de prueba (de `demostracion.json`), al menos una con resultado incierto. Al tocarlas, la foto se envía de verdad a `/predecir`.

**Consejos para la foto:**
- luz pareja, sin sombras duras;
- el insecto centrado y ocupando buena parte de la foto;
- fondo simple;
- JPG, PNG o WEBP de hasta 20 MB (las fotos HEIC del iPhone no sirven).

Se ven desplegados mientras no hay resultado y plegados después.

**Estados:**

| Estado | Qué se ve |
| --- | --- |
| Vacío | Consejos, ejemplos y una línea que explica qué va a pasar |
| Identificando | La vista previa con un indicador sobrio y "Identificando…" |
| Familia afirmada | La ruta *orden → familia*, las dos barras de confianza, la ficha biológica si existe y "Ver esta familia en el catálogo" (→ `/#familia-X`) |
| Familia incierta | El orden afirmado y un bloque amarillo "Revisar con especialista", con las tres candidatas y su porcentaje. Las fichas llevan el título "Registros del orden X en la base" |
| Orden sin familias | "Este orden no se clasifica por familia en el sistema" y el enlace a la tarjeta del orden |
| Error | El mensaje en español del backend (formato, tamaño, imagen dañada) o "No se pudo conectar con el servidor", con "Reintentar" |

- "Identificar otra foto" vuelve al estado vacío.
- **Chip plaga / benéfico:** solo aparece si la ficha de la base lo dice, en `Importancia_economica`. Nunca se deduce.

## 7. Pruebas y verificación

- **Frontend (Vitest y Testing Library):**
  - los estados de la tabla del §6;
  - que la barra de confianza lleve siempre número y etiqueta;
  - catálogo: filtro por orden, búsqueda, panel de fichas (con y sin fichas), tarjetas de orden;
  - ejemplos: envío real a la API simulada;
  - selección de foto, cámara y arrastrar y soltar;
  - que la cabecera enlace entre páginas.

  Las pruebas actuales se adaptan a los componentes nuevos.
- **Scripts (pytest, con datos diminutos y sin red):**
  - `catalogo_web.py`: una foto por clase, preferencia de licencia, crédito presente, formato del JSON, que las fotos de demostración salgan del conjunto de prueba y que se respeten las preferencias;
  - `marca_web.py`: fondo eliminado sin halos (la transparencia del fondo es 0 y la del interior del símbolo es 255), tamaños y archivos del favicon y el manifiesto.
- **Navegador real:**
  - a 1440 px y a 390 px de ancho, con fotos reales;
  - contraste de todos los textos;
  - navegación completa con teclado;
  - movimiento reducido;
  - peso: JavaScript de cada página menor a 250 KB sin comprimir, y fotos del catálogo con carga diferida.
- **Cierre:**
  - el detector de patrones de Impeccable (`impeccable detect`);
  - la revisión independiente (`impeccable-finish-reviewer`);
  - `DESIGN.md` y su sidecar, generados por `impeccable-documenter` a partir de lo construido.

## 8. Decisiones abiertas

Ninguna. Si al revisar la hoja de contactos alguna foto no convence, se cambia en `catalogo_preferencias.yaml`.
