# insectos-ia — guía para trabajar en este repositorio

Sistema de IA que identifica **orden → familia** de insectos amazónicos a partir de una foto.
Es el Proyecto Formativo INAAM–FISI y de Responsabilidad Social de la UNAP (Facultad de Agronomía).
La entomóloga de referencia es la Dra. Aldi Guerra Teixeira.
Hay un demo previo, independiente, en `../insectos-demo/`: 4 órdenes, Gradio.

## Estado actual (2026-11-17)

| Etapa | Estado |
| --- | --- |
| Plan 01 — datos | **Cerrado.** 34 360 fotos, repartidas 24 032 / 5 163 / 5 165 (entrenamiento / validación / prueba). |
| Plan 02 — modelo | **Código terminado.** Modelo vigente: `v4_convnext_t_288`. Se entrena en Colab gratis (T4), una sola cuenta. |
| Plan 03 — web | **Terminado.** Backend FastAPI en `backend/`, React + Vite en `frontend/`. Se arranca con `iniciar.bat` (http://127.0.0.1:8000). |
| Rediseño del frontend (INSECTIA) | **Terminado** (2026-09-25) y subido a `main`. |
| Base de estudiantes y evaluación de campo | **Hechas** (2026-11-17). 1 051 fotos propias de 24 grupos; 705 forman el conjunto de campo. |
| Entregables | Base de datos, banco de imágenes, informe científico (borrador) y los dos manuales en `../entregables/`. Ver «Entregables y pendientes». |
| Despliegue | **Pendiente.** Hoy solo corre en local. |

Pruebas: 422 de Python (`pytest`) y 153 del frontend (`npm run prueba`).

### La web: INSECTIA

- **Cinco páginas**, cinco entradas de Vite, sin enrutador:
  - `/` (`frontend/src/paginas/inicio/`): presentación, demostración con un resultado real, cómo funciona, desempeño y una vista previa del catálogo (dos filas, una clase por orden) con el enlace "Ver catálogo completo";
  - `/identificar/` (`frontend/src/paginas/identificar/`): la herramienta, con todos sus estados;
  - `/catalogo/` (`frontend/src/paginas/catalogo/`): las 44 clases con buscador y filtros. El resultado de la herramienta enlaza a `/catalogo/#familia-X`. Su `index.html` convive en `dist/catalogo/` con los datos que genera `pipeline.catalogo_web`;
  - `/creditos/` (`frontend/src/paginas/creditos/`): grupo, docente, desarrolladores y los 98 estudiantes recolectores;
  - `/registros/?orden=X&familia=Y` (`frontend/src/paginas/registros/`): todos los registros de la base para un taxón, con un recuadro que explica de dónde salen.
  - El resultado y el panel del catálogo muestran **una sola ficha resumen** (`compartido/ResumenFichas.jsx`, cálculo en `compartido/resumen.js`): importancia con conteos, cultivos resaltados, nombres, daños, estados, lugares y géneros anotados, más el enlace «Ver los N registros» a `/registros/`.
  - En el celular la cabecera oculta "Catálogo" y "Créditos": el pie los enlaza.
  - Comparten `frontend/src/compartido/`: tokens y estilos base, cabecera, pie, resultado, ficha, crédito y cliente de la API.
- **Documentos:**
  - `PRODUCT.md`: usuarios, marca y lo que no se debe inventar;
  - `DESIGN.md` y `.impeccable/design.json`: el sistema visual tal como quedó;
  - especificación y plan en `docs/superpowers/`.
- **Contenido generado, versionado en `frontend/public/`:**
  - `pipeline.marca_web`: logo, símbolo, favicon y manifiesto, a partir de `../imagenes_web/imagen_1.png`. `logo_1.png` y `favicon.png` no se usan: su transparencia está dañada.
  - `pipeline.catalogo_web`: `catalogo.json` (fotos, F1 y métricas), `demostracion.json` y las fotos WebP. La demostración usa fotos del conjunto de **prueba** pasadas por el modelo real: ninguna cifra se escribe a mano.
  - Las fotos elegidas a mano van en `frontend/catalogo_preferencias.yaml`. El script valida contra el modelo las fotos fijadas de la demostración: una "incierta" que el modelo afirma no se publica.
  - La hoja de contactos para revisar las 44 fotos queda en `datos/catalogo_contactos.jpg`.
- **Reglas de contenido:**
  - no hay especie, SENASA, IIAP, manejo integrado de plagas ni GPS;
  - las fichas se rotulan "Especie del registro" porque describen especies de la base, no la identificación;
  - no se muestran nombres de personas en fichas ni resultados: por eso `Verificado_por` no aparece. La única excepción es la página **Créditos** (`frontend/src/paginas/creditos/creditos.js`): grupo INAAM, docente, desarrolladores y, cuando lleguen, los estudiantes recolectores;
  - toda foto del catálogo lleva autor, licencia y enlace a su observación en iNaturalist;
  - el desempeño de la portada muestra también la cifra de campo, que `pipeline.catalogo_web` lee de `modelo/<corrida>/evaluacion_campo.json` (`metricas_de_campo`); sin ese archivo no se menciona el campo.
- **Base biológica (`bd/`):** `bd_insectos.xlsx` tiene los 783 registros de estudiantes de taxones que el modelo conoce (familias de la ontología u órdenes sin familias; Phasmatodea → Phasmida). Se carga en SQLite con `python -m pipeline.bd`. Sale de `../entregables/Base_de_datos_y_banco_de_imagenes/BD_Insectos_Amazonicos_Consolidada.csv`.
- **Pendientes menores de la revisión final:**
  - en el servidor de desarrollo de Vite, `/identificar` sin barra muestra la portada (en FastAPI funciona);
  - un `catalogo.json` dañado muestra un error técnico en inglés;
  - el 70 % de "Cómo funciona" está escrito a mano, en vez de leer `metricas.umbral`;
  - `credito()` y `url_origen()` no miran la columna `fuente`: las fotos de campo futuras necesitarán su propio crédito;
  - la identificación no tiene límite de tiempo si el servidor se cuelga.
  - "Sin fichas en la base todavía" se decide por orden, porque `/resumen` solo cuenta por orden.
- **Verificar la interfaz:**
  - `npx vite preview` basta para la parte estática y no carga el modelo;
  - las capturas a 390 px se toman con Chrome sin interfaz y un iframe de 390 px;
  - para la vista táctil, Chrome con `--remote-debugging-port` y `Emulation.setTouchEmulationEnabled`.
  - Las capturas de la extensión de Chrome salen recortadas en esta PC.
- **Memoria de la PC:** es limitada. Correr la suite de Python con el servidor apagado (tarda unos 5 min). Claude Code puede detener procesos de fondo cuando falta memoria.

### Corridas del modelo (conjunto de prueba, 5 165 fotos de repositorio)

| Corrida | Qué cambió | F1 orden | F1 familia | Top-3 familia |
| --- | --- | ---: | ---: | ---: |
| `v1_efficientnet_b0` | Base del plan, 224 px | 0.832 | 0.791 | 0.863 |
| `v2_antisobreajuste` | Aumentos fuertes, suavizado 0.1, tasa en coseno | 0.864 | 0.832 | 0.891 |
| `v3_b2_288` | EfficientNet-B2 a 288 px | 0.900 | 0.874 | 0.925 |
| `v4_convnext_t_288` | ConvNeXt-Tiny preentrenado en ImageNet-22k, 288 px | **0.935** | **0.921** | **0.958** |

La meta del plan es ≥0.90 en orden y ≥0.85 en familia. Desde la v3 se alcanza **sobre fotos de repositorio**. Sin conjunto de campo, eso no permite declararla cumplida.
La ficha de la Facultad pide 99 %, que no es realista; está pendiente renegociarla.
La v4 responde con 95.5 % de acierto cuando exige confianza ≥0.7, y lo hace en el 94 % de las fotos (v3: 93.6 % y 89 %). Ver `docs/desempeno_por_clase_v4.md`.

La v4 corrió las 25 épocas; la mejor fue la 23 (F1 de familia en validación 0.909, subiendo despacio con la tasa en coseno, sin sobreajuste).
Mejoró todas las clases débiles. Las más bajas siguen siendo Termitidae (0.78), Acrididae (0.81), Formicidae (0.82) y Heterotermitidae (0.83).
Lo que decidió el salto fue el preentrenamiento en ImageNet-22k: la v3 se había estancado con la tasa aún alta.

Las mejoras se prueban **una a una**, para medir el aporte de cada cambio. El usuario lo pidió así.
Las mejoras hechas son: anti-sobreajuste (v2), backbone y resolución (v3), `UMBRAL_FAMILIA` = 0.7 en `pipeline/inferencia.py` (elegido con la tabla de la v3) y preentrenamiento 22k (v4).
El umbral no se reajustó con la v4: elegirlo mirando la tabla de prueba sería ajustar sobre el examen.
Medido sin reentrenar sobre la v3, en validación: elegir orden y familia a la vez no mejora (+0.2 pt) si se incluyen los 6 órdenes sin familias; el volteo en inferencia da +0.5 pt a costa de duplicar el tiempo.
Si una corrida nueva cambia esa tabla, revisar el umbral con ella. `desempeno` mide la misma confianza enmascarada que `predecir`.

## Cuando llegue una corrida nueva

El usuario descarga la carpeta de la corrida desde Drive a `D:\300\OTROS\XXX\DAN\IA\agro\entrenamiento\corridas\<corrida>`. Luego:

1. Copiar a `modelo/<corrida>/` los archivos `config.json`, `etiquetas.json`, `evaluacion.json`, `metricas.json`, `insectos.onnx`, `mejor.pth` y `ultimo.pth`. Los `.onnx` y `.pth` no se versionan.
2. Copiar `informe_metricas.md` a `docs/informe_metricas.md`.
3. Revisar el historial de `metricas.json` (tasa, pérdida y F1 por época) para ver si hubo sobreajuste o si faltaron épocas.
4. El informe por clase lo genera el paso 8 del cuaderno (`desempeno_por_clase.md`); copiarlo a `docs/desempeno_por_clase_<vN>.md`. En la PC local, `python -m pipeline.desempeno` se cortó por falta de memoria con la v4.
5. Comparar contra la corrida anterior, en especial las clases débiles.
6. Commit, y actualizar la tabla de corridas de este archivo y `docs/RESUMEN_EJECUTIVO.md`.
7. Si la corrida nueva pasa a ser la vigente, cambiar `CORRIDA_VIGENTE` en `backend/app.py` y `MODELO_DIR` en `iniciar.bat`, y regenerar el contenido de la web: `python -m pipeline.catalogo_web --desempeno docs/desempeno_por_clase_<vN>.md`. El prototipo lee la resolución del propio ONNX.

## Cómo se trabaja aquí (convenciones del proyecto)

- **Todo en español:** código, nombres, comentarios, commits y documentos.
- **Nunca nombres taxonómicos literales en `pipeline/`.** Salen de `ontologia/clases.yaml`, y una prueba lo verifica.
- **TDD:** primero la prueba que falla, después el código. Las pruebas no usan red ni pesos preentrenados, y cada una tarda menos de 5 s.
- **Verificar con datos reales, no solo con pruebas.** Varias fallas solo aparecieron así:
  - el filtro de contenido v1 descartaba insectos camuflados;
  - la paridad ONNX daba falsas alarmas con ruido.
- **Commits:** mensaje en español que explique el porqué, terminado con las líneas `Co-Authored-By` que indique el sistema. Se trabaja sobre `main`; las ramas de los planes ya se fusionaron y borraron.
- **Entorno:** Windows con Git Bash y PowerShell. Se usa `.venv\Scripts\python` (Python 3.12). `gh` está autenticado como `dNogueira300`.
- **`datos/` no se versiona**, salvo `datos/splits/asignacion_observadores.yaml`, que fija qué fotógrafo está en cada grupo. Regenerarla invalida los modelos entrenados.

## Orden del pipeline

```
censo → descarga → curacion → filtro_contenido → splits → empaquetar → [Colab] entrenar → exportar → evaluar → desempeno
```

Los comandos están en `README.md`. Los datos crudos (39 668 fotos, ~2 GB) están en `datos/crudo`. El paquete para Colab está en `datos/paquete/dataset_v1.zip` (1.83 GB, sha256 `bd13076c…`).

## Colab

- Cuaderno: `colab/entrenar.ipynb`, rama `main`. **Se genera** con `python colab/crear_cuaderno.py`: editar el generador, no el `.ipynb`.
- Datos en `MyDrive/insectos-ia-colab/`: es una carpeta de otra cuenta, compartida, que necesita un **acceso directo en Mi unidad** para verse al montar Drive.
- **Cada corrida nueva necesita un `CORRIDA` distinto:** reanudar con otra configuración se detiene a propósito.
- Si Colab corta la sesión, se vuelve a ejecutar todo: `--reanudar` continúa desde la última época.

## Pendientes con la Facultad

- Confirmar las familias provisionales: 5 de Hemiptera y Coccinellidae.
- Renegociar la meta del 99 %.
- Validar las etiquetas de las fotos de campo (`Verificado_por`) y repetir la medición.

## Evaluación de campo (2026-11-17)

- 705 fotos de alumnos (26 familias del modelo, 7 órdenes) en `datos/campo_crudo/` y `datos/splits/campo.csv`, ingeridas con `pipeline.campo`: 0 coincidencias con los splits.
- v4 en campo: macro-F1 de orden 0.879 y de familia 0.699, sobre las clases presentes. Con umbral 0.7 responde el 85 % y acierta el 85.2 %. **La meta no se alcanza en campo.** La brecha en familia es de 0.22. Ver `docs/evaluacion_campo_v4.md`.
- Las 705 fotos son el examen de campo: no deben entrar a entrenamiento ni usarse para elegir el umbral.
- `pipeline.evaluar` promedia el macro-F1 sobre las 44 familias, y en campo las ausentes cuentan como 0. Para campo hay que promediar solo las presentes.

## Entregables y pendientes (2026-11-17)

Los entregables viven fuera del repositorio, en `../entregables/`:

| Entregable | Estado |
| --- | --- |
| Base de datos (`Base_de_datos_y_banco_de_imagenes/BD_Insectos_Amazonicos_Consolidada.xlsx` y `.csv`) | **Hecho.** 1 051 registros de 24 grupos, 12 órdenes, 73 familias; columnas extra `Grupo`, `ID_original`, `Archivo_original`, `Conjunto_de_campo`. |
| Banco de imágenes (`Banco_de_imagenes/Orden/Familia/`) | **Hecho.** Solo fotos de estudiantes (1 051). No llega a las 5 000 de la ficha: el usuario lo aceptó. |
| Evaluación de campo (`Evaluacion_de_campo/predicciones_campo_v4.csv`, `docs/evaluacion_campo_v4.md`) | **Hecha.** |
| Informe científico (`Informe_cientifico/Informe_cientifico_INSECTIA_borrador.docx`) | **Borrador.** Lo termina la ingeniera: autores, referencias entomológicas y revisión. |
| Manual de uso (`Manuales/Manual_uso_INSECTIA.pptx` y `.pdf`) | **Hecho.** 18 páginas, capturas de la web actual. |
| Manual ilustrado de insectos (`Manuales/Manual_ilustrado_insectos.pptx` y `.pdf`) | **Hecho.** 52 páginas, 69 familias de 10 órdenes. Textos de familias redactados por Claude: conviene que la docente los revise. |
| Fuentes de los manuales (`Manuales/fuentes/`) | Scripts pptxgenjs, textos, imágenes y fondos para regenerarlos. Si cambia la web, rehacer capturas y página 11 del manual de uso. |

**Pendientes:**
- **Despliegue gratuito** para la demostración (ver `docs/GUIA_BASE_DE_DATOS_Y_HOSTING.md`). Al publicar, cambiar en el manual de uso la página «Antes de empezar» y la nota del celular, que hoy hablan del uso local.
- Validación docente de las identificaciones (`Verificado_por` está en «(pendiente)» en las 1 051 filas).
- Presentación final y defensa.
- Videos educativos, material didáctico, talleres e informe de impacto social (proyecto de Responsabilidad Social): quedan para después.
- Confirmar con la Facultad las familias provisionales y renegociar la meta con las cifras de campo.
- La recopilación cubre 10 de los 15 órdenes: faltan Isoptera, Thysanoptera, Neuroptera, Dermaptera y Psocodea.
- No hay más fotos de campo que conseguir: el trabajo está en cierre.

## Límites declarados

- Solo 0.5 % de las fotos son de Perú.
- El 73 % de las licencias son no comerciales.
- Poca diversidad de fotógrafos en tres familias de Odonata.
- Todavía queda un 5–10 % de montículos entre las fotos de Termitidae.
