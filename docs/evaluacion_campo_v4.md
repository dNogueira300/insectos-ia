# Evaluación de campo — modelo v4 (`v4_convnext_t_288`)

Fecha: 17/11/2026. Primera medición del sistema con fotos tomadas por personas en la Amazonía, no descargadas de repositorios.

## Conjunto de campo

- **Origen:** recopilaciones de los 24 grupos de alumnos de Entomología (UNAP), revisadas y cerradas en noviembre de 2026. La base consolidada tiene 1051 fotos propias.
- **Fotos evaluadas:** **705**, de las 26 familias de la base que están entre las 44 clases del modelo, en 7 órdenes. Las otras 346 fotos son de 47 familias que el modelo no conoce: quedan solo en la base de datos y no se evalúan.
- **Ingesta:** `python -m pipeline.campo` → `datos/splits/campo.csv`. Hubo 0 coincidencias con train, val o test y 0 fotos rechazadas.
- **Inferencia:** el ONNX exportado (el mismo de la web) en CPU, a 288 px, con el enmascaramiento jerárquico de `pipeline.inferencia`.
- **Predicciones por foto:** `../entregables/Evaluacion_de_campo/predicciones_campo_v4.csv`.
- **Etiquetas:** las de los alumnos, revisadas por foto. La validación docente (`Verificado_por`) todavía está pendiente: algunos "errores" del modelo podrían ser errores de etiqueta.
- **Muestra desequilibrada:** Orthoptera aporta 353 de las 705 fotos y Acrididae 215. Diez familias tienen menos de 10 fotos, y su F1 depende de una o dos imágenes.

## Resultados

| Métrica | Repositorio (test, 5165) | Campo (705) |
| --- | ---: | ---: |
| macro-F1 de orden | 0.935 | **0.879** (7 órdenes presentes) |
| Exactitud de orden | 0.945 | 0.887 |
| macro-F1 de familia | 0.921 | **0.699** (26 familias presentes) |
| macro-F1 de familia, solo familias con ≥10 fotos | — | 0.746 (15 familias, 659 fotos) |
| F1 de familia ponderado por fotos | — | 0.803 |
| Exactitud de familia | 0.922 | 0.772 |
| Top-3 de familia | 0.958 | 0.877 |

El macro-F1 de campo se promedia sobre las clases **presentes** en el conjunto. `pipeline.evaluar` promedia sobre las 15 órdenes y 44 familias: con clases ausentes que cuentan como F1 = 0, daría 0.41 y 0.47, cifras que no miden nada.

### Contra la meta (≥0.90 en orden, ≥0.85 en familia)

- **Orden:** macro-F1 de 0.879. Queda **cerca, pero no se alcanza**.
- **Familia:** macro-F1 de 0.699. **No se alcanza.**
- **Brecha repositorio → campo en familia:** 0.22. El modelo rinde bastante peor con fotos de parcela que con fotos curadas de iNaturalist.

### Con el umbral de confianza de la web (0.7)

| Umbral | Responde | Acierta cuando responde |
| --- | ---: | ---: |
| 0.0 | 100 % | 77.2 % |
| 0.5 | 94 % | 81.5 % |
| 0.6 | 91 % | 83.0 % |
| **0.7** | **85 %** | **85.2 %** |
| 0.8 | 77 % | 88.6 % |
| 0.9 | 66 % | 92.5 % |

Con el umbral vigente, la web da la familia en el 85 % de las fotos de campo y acierta el 85.2 % de esas veces. En el resto muestra la familia como incierta. En repositorio esas cifras eran 94 % y 95.5 %.

## Dónde falla

Por orden: Hemiptera (0.76), Blattodea (0.82) y Coleoptera (0.84) son los más débiles. Orthoptera (0.96) y Odonata (0.98) son los más sólidos.

Familias con 10 fotos o más, de la más débil a la más fuerte:

| Familia | F1 | Fotos | Confusión principal |
| --- | ---: | ---: | --- |
| Noctuidae | 0.18 | 10 | Casi todas son larvas: el modelo predice otro orden |
| Scarabaeidae | 0.61 | 19 | Blaberidae (3) |
| Coreidae | 0.67 | 13 | Ichneumonidae (2) |
| Libellulidae | 0.70 | 15 | Aeshnidae (5) |
| Reduviidae | 0.70 | 24 | Solo orden (3), Tettigoniidae (3) |
| Apidae | 0.76 | 46 | Vespidae (5), Chalcididae (3) |
| Tettigoniidae | 0.77 | 96 | Gryllidae (6), Acrididae (4) |
| Gryllidae | 0.77 | 42 | Tettigoniidae (6) |
| Pentatomidae | 0.77 | 16 | — |
| Chrysomelidae | 0.81 | 42 | Scarabaeidae (2) |
| Formicidae | 0.83 | 43 | Tephritidae (3) |
| Vespidae | 0.86 | 45 | Ichneumonidae (4) |
| Acrididae | 0.88 | 215 | Tettigoniidae (20), solo orden (13) |
| Curculionidae | 0.90 | 16 | — |
| Sphingidae | 0.97 | 17 | — |

Hallazgos:

- **Larvas:** 1 de 9 acertada. El modelo se entrenó casi solo con adultos y manda las orugas a Phasmida, Isoptera o Hemiptera. Es la falla más clara y tiene una causa concreta.
- **Orden equivocado:** 80 fotos (11 %), de las cuales 28 van a órdenes que el modelo identifica solo hasta orden (Mantodea, Phasmida, Psocodea…). En esos casos el enmascaramiento jerárquico arrastra también el error de familia.
- **Por tipo de foto:** acierta la familia en el 79 % de las fotos tomadas en campo y en el 75 % de las de ejemplares colectados sobre una mesa o papel. El fondo artificial no ayuda al modelo.
- **Por grupo:** los grupos de Orthoptera, Hymenoptera 1 y Lepidoptera 1 superan el 80 %. Coleoptera 1 (45 %), Maíz (47 %) e Insectos 1 (40 %) quedan muy por debajo; en Maíz pesan las larvas.

## Qué sigue

1. **Validación docente de las etiquetas** de las 705 fotos. Después, repetir esta medición, que solo cuesta correr la inferencia.
2. **No ajustar el umbral con este conjunto:** sería ajustar sobre el examen de campo, igual que no se hizo con el test.
3. **Para cerrar la brecha:** más material de campo y de larvas en entrenamiento, con fotos distintas de estas 705, que deben seguir intactas como examen. Más épocas no corrigen esta brecha.
4. **Renegociar la meta** con estas cifras reales. El 99 % de la ficha queda descartado, y conviene declarar las metas sobre campo con el umbral de confianza.
