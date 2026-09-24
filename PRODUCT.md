# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Jurado y docentes de la Facultad de Agronomía (UNAP)**: evalúan el proyecto en la sustentación, en laptop o proyector. Necesitan entender en pocos segundos qué hace el sistema, qué tan bien funciona y con qué honestidad reporta sus límites.
- **Agrónomos y técnicos en campo**: usan el celular al sol, con una foto recién tomada de un insecto en una parcela amazónica. Necesitan saber orden y familia, y si es plaga o benéfico.
- **Estudiantes y docentes**: exploran en aula o biblioteca las familias que el sistema reconoce y la información biológica asociada.

## Product Purpose

INSECTIA identifica el **orden y la familia** de un insecto de importancia económica de la Amazonía peruana a partir de una foto, y muestra la ficha biológica de la base de datos (nombre común, cultivo asociado, tipo de daño, importancia económica). Es el Proyecto Formativo INAAM–FISI y de Responsabilidad Social de la UNAP. El éxito es que una persona sin formación entomológica obtenga una respuesta útil, y que el sistema diga "no estoy seguro" cuando no lo está, en vez de inventar.

## Positioning

Clasificación jerárquica orden → familia con incertidumbre explícita: afirma la familia solo con confianza ≥ 70 % y, si no, muestra las candidatas para revisar con un especialista. Entrenado con 34 360 fotos de 15 órdenes y 38 familias elegidas con la Facultad para la Amazonía peruana.

## Operating Context

- Prototipo servido por FastAPI en una laptop (`iniciar.bat`, http://127.0.0.1:8000); se abre también desde un celular en la misma red.
- Dos páginas: una de presentación del proyecto y otra de identificación (confirmado por el usuario).
- La identificación tarda alrededor de 1 s en CPU.

## Capabilities and Constraints

- Predice orden y familia, con confianza y top-3 de familias. **No** identifica especie, no marca regiones en la foto (sin mapas de calor ni cajas), no funciona sin conexión al servidor, no tiene usuarios ni sesiones.
- 6 de los 15 órdenes no tienen familias en el sistema (Dermaptera, Mantodea, Neuroptera, Phasmida, Psocodea, Thysanoptera): para ellos solo se informa el orden.
- Acepta JPG, PNG y WEBP hasta 20 MB; las fotos HEIC del iPhone no se admiten.
- El frontend nunca decide taxonomía: muestra lo que responde la API.
- La base biológica tiene hoy 5 fichas de ejemplo; crece cuando Agronomía complete el Excel.

## Brand Commitments

- Nombre: **INSECTIA** ("INSECT" + "IA" en verde). Bajada: "Sistema de Inteligencia Artificial para la identificación de órdenes y familias de insectos de importancia económica de la Amazonía peruana".
- Logo, favicon y hoja de marca provistos por el usuario (`agro/imagenes_web/`).
- Paleta fijada por el usuario: Verde Amazónico #0B5E3B, Verde Selva #4CAF50, Verde Lima #A3D977, Azul Petróleo #0F3D3E, Amarillo Amazonía #F4B400, Gris Oscuro #2E2E2E.
- Prototipo de referencia en Stitch (projects/16595468791669318138), como guía y no como copia: varias de sus afirmaciones no son ciertas para este producto.
- Personalidad: **científica y cercana**. Rigurosa y honesta con la incertidumbre, amable para un agricultor o un estudiante.

## Evidence on Hand

- Métricas reales del modelo v4 en 5 165 fotos de prueba de catálogo: macro-F1 de orden 0.935 y de familia 0.921; top-3 de familia 0.958; con umbral 0.7 responde el 94 % de las veces y acierta el 95.5 %. **Aún no hay evaluación con fotos de campo**; toda cifra debe aclarar que es sobre fotos de catálogo.
- Banco de imágenes: 34 360 fotos de iNaturalist con licencia y atribución por foto (`datos/splits/*.csv`, columnas `licencia` y `atribucion`). El 73 % tiene licencia no comercial. Toda foto que se muestre lleva su crédito.
- **No existen y no deben inventarse:** cifras de precisión distintas de las anteriores, certificaciones o alianzas (SENASA, IIAP), número de estaciones o muestras de campo, recomendaciones de manejo integrado de plagas, nombres de especie, coordenadas GPS.

## Product Principles

1. **Honestidad antes que impresión**: la incertidumbre se muestra, no se esconde; ninguna cifra ni capacidad inventada.
2. **Útil al sol y en el aula**: legible en un celular a pleno sol y en un proyector.
3. **La foto es la protagonista**: el insecto y la fotografía guían la mirada; la tecnología es discreta.
4. **Ciencia con lenguaje llano**: términos taxonómicos correctos, explicados para quien no es entomólogo.

## Accessibility & Inclusion

- WCAG 2.2 AA: texto normal ≥ 4.5:1 y texto grande ≥ 3:1.
- Uso al sol: contraste alto, objetivos táctiles de al menos 44 px y tipografía generosa en el celular.
- Respetar `prefers-reduced-motion`.
- La confianza nunca se comunica solo con color: siempre con número y texto.
- Toda la interfaz en español.
