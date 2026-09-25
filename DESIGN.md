---
name: INSECTIA
description: Identificación de orden y familia de insectos de importancia económica de la Amazonía peruana, con la incertidumbre a la vista.
colors:
  verde-amazonico: "#0b5e3b"
  verde-selva: "#4caf50"
  verde-lima: "#a3d977"
  petroleo: "#0f3d3e"
  amarillo: "#f4b400"
  gris: "#2e2e2e"
  fondo: "#f6f8f5"
  superficie: "#ffffff"
  texto-suave: "#4e5a55"
  texto-sobre-petroleo: "#d6e4e0"
  ambar-texto: "#7a5a00"
  ambar-fondo: "#fff6d6"
  selva-fondo: "#e8f5e9"
  error-texto: "#7a1c14"
  error-fondo: "#fdecea"
  pista: "#e3e8e2"
  borde: "rgba(46, 46, 46, 0.12)"
typography:
  display:
    fontFamily: "'Lexend', system-ui, sans-serif"
    fontSize: "clamp(2rem, 1.3rem + 3vw, 3.5rem)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "'Lexend', system-ui, sans-serif"
    fontSize: "clamp(1.6rem, 1.2rem + 1.6vw, 2.25rem)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  ruta:
    fontFamily: "'Lexend', system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.15
  title:
    fontFamily: "'Lexend', system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  title-sm:
    fontFamily: "'Lexend', system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  lead:
    fontFamily: "'Atkinson Hyperlegible Next', system-ui, sans-serif"
    fontSize: "1.1875rem"
    fontWeight: 400
    lineHeight: 1.55
  body:
    fontFamily: "'Atkinson Hyperlegible Next', system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.55
  cientifico:
    fontFamily: "'Atkinson Hyperlegible Next', system-ui, sans-serif"
    fontSize: "inherit"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "'Atkinson Hyperlegible Next', system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 700
    lineHeight: 1.55
  caption:
    fontFamily: "'Atkinson Hyperlegible Next', system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  radio: "8px"
  radio-grande: "16px"
  radio-pastilla: "9999px"
spacing:
  espacio-1: "4px"
  espacio-2: "8px"
  espacio-3: "12px"
  espacio-4: "16px"
  espacio-5: "24px"
  espacio-6: "32px"
  espacio-7: "48px"
  espacio-8: "72px"
components:
  boton-principal:
    backgroundColor: "{colors.verde-amazonico}"
    textColor: "{colors.superficie}"
    rounded: "{rounded.radio}"
    padding: "0 24px"
    height: "44px"
  boton-principal-hover:
    backgroundColor: "{colors.petroleo}"
  boton-secundario:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.verde-amazonico}"
    rounded: "{rounded.radio}"
    padding: "0 24px"
    height: "44px"
  boton-secundario-hover:
    backgroundColor: "{colors.selva-fondo}"
  boton-claro:
    backgroundColor: "{colors.verde-lima}"
    textColor: "{colors.petroleo}"
    rounded: "{rounded.radio}"
    padding: "0 24px"
    height: "44px"
  boton-contorno:
    backgroundColor: "transparent"
    textColor: "{colors.superficie}"
    rounded: "{rounded.radio}"
    padding: "0 24px"
    height: "44px"
  boton-chico:
    padding: "0 16px"
    height: "44px"
  chip-plaga:
    backgroundColor: "{colors.amarillo}"
    textColor: "{colors.gris}"
    typography: "{typography.label}"
    rounded: "{rounded.radio-pastilla}"
    padding: "2px 12px"
    height: "28px"
  chip-benefico:
    backgroundColor: "{colors.selva-fondo}"
    textColor: "{colors.verde-amazonico}"
    typography: "{typography.label}"
    rounded: "{rounded.radio-pastilla}"
    padding: "2px 12px"
    height: "28px"
  chip-provisional:
    backgroundColor: "{colors.ambar-fondo}"
    textColor: "{colors.ambar-texto}"
    typography: "{typography.label}"
    rounded: "{rounded.radio-pastilla}"
    padding: "2px 12px"
    height: "28px"
  filtro:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.gris}"
    rounded: "{rounded.radio-pastilla}"
    padding: "0 16px"
    height: "44px"
  filtro-activo:
    backgroundColor: "{colors.verde-amazonico}"
    textColor: "{colors.superficie}"
  campo:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.gris}"
    rounded: "{rounded.radio}"
    padding: "0 12px"
    height: "44px"
  barra-pista:
    backgroundColor: "{colors.pista}"
    rounded: "{rounded.radio-pastilla}"
    height: "10px"
  resultado:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.gris}"
    rounded: "{rounded.radio-grande}"
    padding: "24px"
  resultado-incierto:
    backgroundColor: "{colors.ambar-fondo}"
    rounded: "{rounded.radio}"
    padding: "16px"
  ficha-registro:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.radio}"
    padding: "16px"
  tarjeta:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.radio}"
    padding: "16px"
  panel:
    backgroundColor: "{colors.fondo}"
    rounded: "{rounded.radio-grande}"
    padding: "24px"
    width: "min(100%, 40rem)"
  zona:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.radio-grande}"
    padding: "16px"
  zona-arrastrando:
    backgroundColor: "{colors.selva-fondo}"
  aviso-error:
    backgroundColor: "{colors.error-fondo}"
    textColor: "{colors.error-texto}"
    rounded: "{rounded.radio}"
    padding: "16px"
---

# Design System: INSECTIA

## Overview

**Creative North Star: "El encuadre de campo"**

INSECTIA se ve como una libreta de campo bien ordenada puesta al lado de un visor: la foto del insecto manda, encuadrada por las cuatro esquinas del logo, y a su lado la respuesta del modelo se lee como un registro, con el porcentaje escrito y una palabra que dice si se afirma o si hay que revisarlo. Es científica y cercana: nombres taxonómicos correctos en cursiva, frases en lenguaje llano y ninguna cifra que no exista.

El sistema tiene dos intensidades. La página de presentación es *comprometida*: franjas Azul Petróleo a todo el ancho (primera vista y pie) alternan con franjas claras (Fondo y Superficie), y el Verde Lima aparece solo sobre el petróleo. La página de identificación es *contenida*: fondo neutro, tarjetas blancas y color únicamente donde informa (la barra de confianza, los chips, el estado de arrastre). La densidad es cómoda, pensada para un celular al sol y para un proyector: cuerpo de 17 px, objetivos táctiles de 44 px y contraste AA verificado por prueba (`frontend/pruebas/contraste.test.js`).

El color tiene significados fijos. Verde Selva es "respuesta afirmada"; Amarillo es "incierta, revisar con especialista" y también "plaga"; Verde Amazónico es la acción y el enlace. La confianza nunca se comunica solo con color.

**Key Characteristics:**
- La foto como protagonista, con esquinas de encuadre tomadas del logo.
- Franjas Azul Petróleo en la presentación; neutros más un acento en la identificación.
- Confianza siempre en tres capas: porcentaje escrito, etiqueta de texto y barra.
- Plano por defecto: bordes finos y una sola sombra suave para lo que es resultado o diálogo.
- Movimiento corto, de salida, que nunca condiciona que algo se vea.

## Colors

Paleta de marca fijada por el usuario, verde amazónico sobre neutros ligeramente verdosos, más derivados de texto y fondo calculados para pasar AA.

### Primary
- **Verde Amazónico** (verde-amazonico): el color de la acción. Botón principal, borde y texto del botón secundario, enlaces, filtro activo, número del paso en "Cómo funciona", cifras destacadas de desempeño, flecha de la ruta taxonómica, contorno del foco, `accent-color` y `caret-color`.
- **Azul Petróleo** (petroleo): la franja. Fondo de la primera vista y del pie, color de todos los títulos, relleno neutro de la barra de confianza (orden), hover del botón principal, velo de "Identificando…" (al 78 %) y del fondo del panel (al 55 %), sombras teñidas.

### Secondary
- **Verde Selva** (verde-selva): significa "afirmada". Solo relleno de la barra de confianza afirmada y contorno de la tarjeta enlazada (`:target`). Nunca texto sobre claro.
- **Verde Lima** (verde-lima): el acento sobre petróleo. Botón claro de la primera vista, rótulo y enlaces sobre la franja, esquinas de encuadre claras, halo de foco, selección de texto, arco del indicador de carga. Nunca texto sobre claro.

### Tertiary
- **Amarillo Amazonía** (amarillo): significa "incierta, revisar" y "plaga". Relleno de las barras incierta y candidata, fondo del chip de plaga (con texto Gris Oscuro, 7.4:1). Nunca texto sobre claro.
- **Ámbar texto** (ambar-texto) y **Ámbar fondo** (ambar-fondo): la versión legible del amarillo. Etiqueta "Revisar con especialista", chip provisional, bloque de familia incierta, aviso "medido con fotos de catálogo", rótulo del caso incierto.

### Neutral
- **Gris Oscuro** (gris): texto de cuerpo.
- **Texto suave** (texto-suave): texto secundario, créditos, notas, etiquetas de la ficha, marcador del campo.
- **Texto sobre petróleo** (texto-sobre-petroleo): cuerpo y créditos dentro de las franjas petróleo.
- **Fondo** (fondo): fondo de página, fondo del panel de fichas, cabecera (al 97 %).
- **Superficie** (superficie): tarjetas, resultado, zona de foto, franja de desempeño, campos y filtros.
- **Selva fondo** (selva-fondo): hover del botón secundario y de la navegación, fondo del chip benéfico, zona de foto al arrastrar.
- **Pista** (pista): pista de la barra de confianza y fondo de la foto mientras carga.
- **Borde** (borde): el único borde de contenedor, 1 px.
- **Error texto / Error fondo** (error-texto, error-fondo): avisos de error.

### Named Rules
**The Tres Colores que No Se Leen Rule.** Verde Selva, Verde Lima y Amarillo nunca van como texto sobre fondo claro (dan entre 1.5 y 2.8:1). Sobre claro son solo rellenos (barras, chips con texto oscuro, contornos). El Verde Lima puede ser texto únicamente sobre Azul Petróleo.

**The Significado Fijo Rule.** Verde Selva es "afirmada"; Amarillo es "incierta" o "plaga". No se usan como decoración ni para otra cosa.

**The Nunca Solo Color Rule.** Todo estado de confianza lleva el porcentaje escrito y, en la familia, la etiqueta "Afirmada" o "Revisar con especialista". La barra es refuerzo y está oculta a lectores de pantalla.

**The Lima Sobre Petróleo Rule.** Dentro de una franja petróleo, los enlaces y rótulos pasan a Verde Lima y el cuerpo a Texto sobre petróleo; el Verde Amazónico no se lee ahí.

## Typography

**Display Font:** Lexend (con system-ui, sans-serif), pesos 500 y 700.
**Body Font:** Atkinson Hyperlegible Next (con system-ui, sans-serif), pesos 400, 400 cursiva y 700.

Ambas se sirven localmente con `@fontsource`: la sustentación puede ser sin internet.

**Character:** Lexend hace eco de las letras del logo y da títulos redondos y firmes; Atkinson Hyperlegible Next está hecha para distinguir cada letra, al sol o en proyector.

### Hierarchy
- **Display** (h1): solo el título de la primera vista.
- **Headline** (h2): títulos de sección y del panel de fichas.
- **Ruta** (Lexend 700, 1.375rem): la línea "Orden X → Familia Y" del resultado; los rótulos "Orden" y "Familia" van en Label, Texto suave.
- **Title** (h3, 500): pasos de "Cómo funciona", título de la ficha. **Title-sm** (h4, 500): títulos de grupo menores.
- **Lead** (1.1875rem): bajada de la primera vista; la intro de identificar y los datos de desempeño usan 1.125rem.
- **Body** (1.0625rem, 1.55): todo el texto corrido, máximo 70ch (60ch en la lista de desempeño), `text-wrap: pretty`.
- **Científico**: los nombres científicos (familias en tarjeta y panel, especie de la ficha, candidatas) van en Atkinson cursiva, incluso cuando el elemento es un título.
- **Label** (0.875rem, 700): chips, etiqueta de la barra, rótulos de nivel, orden en la tarjeta (este último en 400). Sin mayúsculas forzadas.
- **Caption** (0.8125rem): créditos de foto y notas de los ejemplos.

### Named Rules
**The Cifras Tabulares Rule.** Todo porcentaje y métrica usa `font-variant-numeric: tabular-nums`.

**The Espaciado Mínimo Rule.** El tracking de los títulos nunca baja de −0.02 em (display) ni de −0.01 em (resto); los títulos llevan `text-wrap: balance`.

## Layout

Contenedor centrado de 1200 px como máximo con 1 rem de margen a cada lado. Escala de espacio de 4 a 72 px (espacio-1 a espacio-8); las secciones de la presentación usan 72 px de relleno vertical y los grupos internos 24 a 48 px.

- **Presentación:** franjas a todo el ancho. Desde 960 px, primera vista, "Cómo funciona" y desempeño usan dos columnas asimétricas (6fr / 5fr o 5fr / 6fr); por debajo, una sola columna. En "Cómo funciona" los pasos quedan fijos (`sticky`, top 96 px) mientras baja el caso incierto.
- **Catálogo:** rejilla `auto-fill` de tarjetas de mínimo 250 px con 24 px de separación; bajo 640 px, dos columnas compactas con 12 px (en una sola columna las 44 clases superarían los 20 000 px).
- **Identificar:** desde 900 px, foto a la izquierda (5fr) y resultado a la derecha (6fr) fijo a 88 px del borde superior; en el celular se apila, con "Tomar foto" primero.
- **Cabecera** fija de 68 px; bajo 640 px el logotipo cede al símbolo y se ocultan los enlaces de texto.
- **Capas:** cabecera 10, fondo del panel 20, enlace "saltar al contenido" 40.

## Elevation & Depth

Plano por defecto. La profundidad se da por tono (franjas petróleo contra Fondo, tarjetas Superficie contra Fondo) y por el borde de 1 px. La sombra existe solo en dos lugares y está teñida de petróleo, nunca negra.

### Shadow Vocabulary
- **Sombra** (`0 1px 2px rgba(15, 61, 62, 0.06), 0 2px 8px rgba(15, 61, 62, 0.04)`): solo el bloque de resultado, para que se separe de la franja o de la columna.
- **Sombra del panel** (`0 16px 40px rgba(15, 61, 62, 0.18)`): solo el diálogo de fichas, sobre su velo petróleo.

### Named Rules
**The Plano Salvo Resultado Rule.** Tarjetas, zona de foto, ficha, consejos y avisos no llevan sombra: borde de 1 px y nada más. Solo el resultado y el diálogo se elevan.

## Shapes

Esquinas suavemente redondeadas: 8 px (radio) en botones, campos, tarjetas, registros de ficha, avisos y fotos; 16 px (radio-grande) en los contenedores grandes (resultado, zona de foto, panel, espera); 9999 px (radio-pastilla) en chips, filtros y pistas de la barra. Los números de paso son círculos de 3 rem. Las fotos se recortan a 4:3.

**Esquinas de encuadre.** El motivo del logo: cuatro escuadras de 28 × 4 px dibujadas con gradientes en un pseudo-elemento, con 10 px de aire alrededor de la foto. Petróleo sobre claro; Verde Lima (`marco--claro`) sobre la franja petróleo. Enmarcan la foto de la primera vista, el caso incierto de "Cómo funciona" y la vista previa de la zona de foto.

### Named Rules
**The Encuadre Solo Para la Foto Rule.** Las esquinas de encuadre enmarcan una foto de insecto que el modelo mira o miró. No se usan en texto, tarjetas del catálogo ni botones.

## Components

### Buttons
Firmes y directos, siempre con texto.
- **Shape:** radio de 8 px, alto mínimo 44 px, relleno lateral 24 px (16 px en `chico`), Atkinson 700 a 1rem (0.9375rem en chico), borde de 1.5 px.
- **Principal:** Verde Amazónico con texto blanco; hover a Azul Petróleo.
- **Secundario:** Superficie con texto y borde Verde Amazónico; hover a Selva fondo.
- **Claro:** Verde Lima con texto Azul Petróleo, solo sobre franja petróleo; hover a un lima más claro.
- **Contorno:** transparente con texto blanco y borde blanco al 75 %, solo sobre franja petróleo; hover con blanco al 8 %.
- **Estados:** transición de fondo de 200 ms; al presionar, escala 0.98 en 120 ms; deshabilitado al 55 % de opacidad. El botón de archivo es un `label` con el input oculto y hereda el foco del input.
- **Foco (global):** contorno de 2 px Verde Amazónico con 2 px de separación y halo de 5 px Verde Lima, visible tanto sobre claro como sobre petróleo.

### Chips
- **Style:** pastilla de 28 px de alto, Label 0.875rem 700, siempre con texto.
- **Plaga:** Amarillo con texto Gris Oscuro. **Benéfico:** Selva fondo, texto y borde de 1 px Verde Amazónico. **Provisional:** Ámbar fondo con Ámbar texto.

### Filtros y campo
- **Filtro de orden:** pastilla de 44 px, Superficie, borde de 1.5 px gris al 20 %; hover con borde Verde Amazónico; activo (`aria-pressed`) relleno Verde Amazónico con texto blanco.
- **Campo de búsqueda:** 44 px, radio 8 px, Superficie, borde de 1.5 px gris al 35 %; etiqueta encima en 700 Azul Petróleo; ancho máximo 28rem.

### Barra de confianza
La firma de la honestidad del sistema.
- Encabezado en una línea: título a la izquierda, porcentaje tabular a la derecha, ambos en 700.
- Pista de 10 px en Pista, pastilla; relleno por `scaleX(valor)` desde la izquierda.
- **Neutra** (orden): relleno Azul Petróleo, sin etiqueta. **Afirmada:** Verde Selva, etiqueta "Afirmada" en Verde Amazónico. **Incierta:** Amarillo, etiqueta "Revisar con especialista" en Ámbar texto. **Candidata:** Amarillo, título en cursiva 400 (nombre científico), sin etiqueta.
- La tarjeta del catálogo reutiliza la pista y el relleno neutro para el F1.

### Resultado
- Contenedor Superficie, radio 16 px, borde de 1 px, Sombra, relleno 24 px, separación interna 16 px; aparece con la animación `aparecer`.
- Ruta taxonómica en Lexend 1.375rem Azul Petróleo; cada paso ("Orden X", "→ Familia Y") es una unidad que no se parte al cortar línea.
- Si la familia es incierta, un bloque Ámbar fondo (radio 8 px, 16 px) agrupa la barra incierta, el aviso en negrita y la lista de tres candidatas; no se escribe la familia en la ruta.
- Si el orden no tiene familias en el sistema, solo una nota en Texto suave, sin tratarlo como duda.

### Ficha biológica
- Registro en Superficie, radio 8 px, borde de 1 px, relleno 16 px; chip de importancia arriba, luego una lista de definición de dos columnas (etiqueta 700 Texto suave, mínimo 8rem; valor en Body). Bajo 480 px pasa a una columna.
- La especie del registro va en cursiva y se rotula "Especie del registro", no como identificación.

### Crédito
- Una línea en Caption, Texto suave: "Foto: autor · licencia", con el autor enlazado a su observación. Toda foto mostrada lo lleva. Sobre petróleo cambia a Texto sobre petróleo con enlace Verde Lima.

### Tarjeta del catálogo
- Superficie, radio 8 px, borde de 1 px, sin sombra, recorte oculto; foto 4:3 arriba sobre Pista; cuerpo con 16 px y 8 px de separación: orden (0.875rem Texto suave), nombre científico en cursiva 700 a 1.1875rem, nombre común, chip provisional si aplica, F1 con barra, crédito y botón secundario chico "Ver fichas" al pie.
- Enlazada desde un resultado (`:target`): contorno de 3 px Verde Selva.
- Bajo 640 px: relleno 12 px, textos mínimos de 0.9375rem, botón a todo el ancho y el texto largo del F1 oculto.

### Panel de fichas
- Diálogo modal: velo Azul Petróleo al 55 %, panel en Fondo de hasta 40rem por 90vh (máx. 48rem), radio 16 px, relleno 24 px, sombra del panel, aparece en 240 ms.
- Encabezado con el nombre científico en cursiva y botón secundario chico "Cerrar". Foco retenido dentro; Escape cierra y devuelve el foco.

### Zona de foto
- Superficie, radio 16 px, borde de 1 px, relleno 16 px; dentro, un área 4:3 con esquinas de encuadre y la vista previa en `contain` sobre Fondo.
- Vacía: una frase centrada en Texto suave (máx. 28ch) que cambia según el dispositivo sea táctil o no.
- **Arrastrando:** borde Verde Amazónico y fondo Selva fondo, en 200 ms.
- **Identificando:** velo Azul Petróleo al 78 % dentro del encuadre, con un aro de 40 px (blanco al 30 %, arco Verde Lima) y el texto "Identificando…" en blanco 700.
- Acciones debajo, cada botón de mínimo 10rem y flexible; en táctil, "Tomar foto" (principal) antes que "Elegir foto" (secundario).

### Navegación
- Cabecera fija en Fondo al 97 % con borde inferior; enlaces de 44 px en Azul Petróleo 700, hover Selva fondo, página actual subrayada 2 px con 6 px de separación; botón principal a la derecha.

### Movimiento
- **Qué se anima:** la aparición del resultado (`aparecer`: opacidad desde 0 y 8 px hacia arriba, 320 ms) y del panel (240 ms); el llenado de la barra (`llenar`: `scaleX` desde 0, 600 ms); cambios de fondo y borde de botones y zona (200 ms); la presión del botón (120 ms); el indicador de carga (`girar`, 900 ms lineal, infinito).
- **Curva:** una sola, de salida: `cubic-bezier(0.25, 1, 0.5, 1)`. Sin rebotes. La rotación del indicador es la única lineal.
- **Movimiento reducido:** todas las animaciones y transiciones bajan a 1 ms y una iteración; el aro de carga se detiene y pierde el arco lima, y queda el texto "Identificando…".
- El contenido es visible sin animación: ninguna animación parte de un estado oculto que dependa de JavaScript.

## Do's and Don'ts

### Do:
- **Do** escribir el porcentaje y la etiqueta en toda confianza; la barra solo refuerza.
- **Do** usar Verde Lima como texto únicamente sobre Azul Petróleo, y Ámbar texto (no Amarillo) cuando el amarillo tiene que leerse.
- **Do** mantener 44 px de alto mínimo en todo objetivo táctil (botones, filtros, campo, enlaces de la cabecera, resumen de consejos).
- **Do** poner los nombres científicos en Atkinson cursiva y los porcentajes en cifras tabulares.
- **Do** acompañar toda foto con su crédito y enmarcar con las esquinas de encuadre solo las fotos que el modelo analiza.
- **Do** usar la curva de salida `cubic-bezier(0.25, 1, 0.5, 1)` y respetar `prefers-reduced-motion`.

### Don't:
- **Don't** usar Verde Selva, Verde Lima ni Amarillo como texto sobre Fondo o Superficie.
- **Don't** usar Verde Selva o Amarillo con un significado distinto de "afirmada", "incierta" o "plaga".
- **Don't** afirmar una familia en la ruta del resultado cuando es incierta; se muestran las candidatas.
- **Don't** añadir sombras a tarjetas, zona de foto o fichas; solo el resultado y el diálogo se elevan.
- **Don't** usar sombras negras: las sombras van teñidas de Azul Petróleo.
- **Don't** mostrar cifras gigantes con degradado: el desempeño se cuenta en frases con la cifra en Verde Amazónico.
