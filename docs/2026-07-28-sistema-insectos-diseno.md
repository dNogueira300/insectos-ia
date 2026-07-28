# Diseño — Sistema de IA para identificación de órdenes y familias de insectos amazónicos

**Fecha:** 2026-07-28
**Proyecto:** Proyecto Formativo (INAAM–FISI) + Responsabilidad Social (INAAM)
**Equipo:** 2 desarrolladores (FISI)
**Repositorio:** https://github.com/dNogueira300/insectos-ia
**Estado:** diseño aprobado, pendiente plan de implementación

---

## 1. Objetivo

Identificar, a partir de una imagen digital, el **orden** y la **familia** de un insecto amazónico de importancia económica, de forma jerárquica, y devolver además la ficha biológica asociada (nombre común, cultivo asociado, tipo de daño, importancia económica).

Meta declarada en la hoja de alcance: **≥90% en órdenes y ≥85% en familias**. Ver §7 para cómo se mide realmente esa meta y por qué la cifra de familias es optimista.

## 2. Alcance

**Incluido:**

- Un sistema de clasificación jerárquica orden → familia.
- Hasta 15 órdenes y 25 familias. La lista definitiva la confirma la Facultad en Semana 3 (§5).
- Banco de imágenes etiquetadas y base de datos biológica consultable.
- Prototipo web de consulta.
- Pipeline reutilizable de datos, entrenamiento, evaluación y despliegue.

**Fuera de alcance (Fase 2, proyecto distinto):**

- Identificación de plagas específicas de los 7 cultivos (cacao, café, arroz, maíz, yuca, plátano, cítricos/palma).
- App móvil nativa y funcionamiento offline.

**No se toca:** `agro/insectos-demo/` queda intacta como prueba de concepto para presentaciones. El sistema real se construye en este repositorio, desde cero.

## 3. Enfoque de modelo: un backbone, dos cabezas

Se implementa un **modelo multi-tarea con enmascaramiento jerárquico**:

- Un backbone convolucional preentrenado en ImageNet (EfficientNet-B0 como línea base, B3 si el presupuesto de cómputo lo permite).
- Dos cabezas lineales sobre el mismo vector de características: una de **orden** (N_orden clases) y una de **familia** (N_familia clases).
- Pérdida combinada: `L = L_orden + λ · L_familia`, con `λ` ajustable (línea base `λ = 1.0`).
- En inferencia, la distribución de familia se **enmascara** para que solo compitan las familias que pertenecen al orden predicho. La matriz de pertenencia familia→orden se deriva de `ontologia/clases.yaml`, no se escribe a mano.

**Por qué esta opción y no las alternativas evaluadas:**

| Alternativa                                                | Por qué se descartó                                                                                                                                                |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Cascada: 1 modelo de orden + 1 modelo de familia por orden | ~8–10 artefactos que mantener y desplegar, cada uno entrenado con una fracción de los datos; el error del primer nivel se propaga sin posibilidad de recuperación. |
| Modelo plano de 25 familias, orden derivado por tabla      | El peor caso para la cola larga: sin señal de orden las familias raras colapsan, y no permite degradar a "conozco el orden, no la familia".                        |

La ventaja decisiva del modelo elegido es que las clases de orden tienen mucho más volumen de datos que las de familia, y la cabeza de orden actúa como regularizador de la representación compartida. Además produce **un solo artefacto ONNX**, lo que simplifica el despliegue.

**Degradación elegante:** si la confianza de familia queda por debajo de un umbral configurable, el sistema responde el orden y declara la familia como incierta, mostrando el top-3. Nunca inventa una familia para llenar el hueco.

## 4. Arquitectura del repositorio

```
insectos-ia/
├─ ontologia/
│   clases.yaml            # única fuente de verdad: orden, familia, taxon_id (GBIF/iNat), mínimos
├─ pipeline/
│   censo.py               # cuenta imágenes disponibles por taxón, sin descargar
│   descarga.py            # descarga desde iNaturalist + GBIF, 1 foto por observación
│   curacion.py            # deduplicado perceptual, filtro de adultos, filtro de calidad
│   splits.py              # train/val/test agrupados por observación y observador
│   entrenar.py            # entrenamiento multi-tarea, exporta ONNX
│   evaluar.py             # métricas por clase, matriz de confusión, reporte markdown
├─ datos/                  # NO versionado (.gitignore)
│   crudo/  curado/  splits/  campo/
├─ bd/
│   bd_insectos.xlsx       # base de datos que llena Agronomía (19 columnas)
│   esquema.sql            # esquema SQLite equivalente
│   importar.py            # Excel → SQLite, valida contra ontologia/clases.yaml
├─ backend/                # FastAPI: /predecir, /clases, /taxon/{id}, /salud
├─ frontend/               # React + Vite
├─ modelo/                 # artefactos entrenados: .onnx, labels.json, metricas.json
└─ docs/                   # este documento, plan de implementación, informes de métricas
```

**Principio de aislamiento:** cada script de `pipeline/` es ejecutable de forma independiente, lee y escribe archivos en `datos/`, y no importa a los demás. Se pueden re-ejecutar etapas sueltas sin rehacer todo. `ontologia/clases.yaml` es la única entrada de configuración de clases para todo el sistema: ningún nombre de orden o familia se escribe literal en el código.

### 4.1 Contrato de `ontologia/clases.yaml`

```yaml
version: 1
minimos:
  familia_train: 150      # umbral de admisión de una familia (§6)
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
```

Cambiar la lista de clases es editar este archivo y re-ejecutar el pipeline. No hay nada más que tocar.

## 5. Estrategia de ontología: censo antes que descarga

La lista de clases **no está cerrada** y no se puede esperar a que lo esté sin perder un cuarto del cronograma. El plan la trata como parámetro:

1. **Semana 1–2:** `censo.py` consulta las APIs y produce `docs/censo_disponibilidad.md`: para cada orden y familia candidata, cuántas observaciones *research-grade* de adultos con foto existen, con filtro geográfico opcional (Perú / Neotrópico) y sin él.
2. **Semana 3:** se presenta esa tabla a la Facultad. La decisión de qué clases entran deja de ser una opinión y pasa a tomarse con el dato de disponibilidad delante. Se congela `clases.yaml` v1.
3. Si la lista cambia después, el costo es re-descargar y re-entrenar, no reescribir código.

## 6. Regla de admisión de clases (cola larga)

Una familia entra al modelo **solo si supera 150 imágenes curadas en train y 30 en test**. Las que no lleguen se agrupan en una clase `Otros_<Orden>` dentro de su orden y se documentan en el informe.

Esta regla es explícita y se aplica automáticamente en `splits.py`. Su propósito es evitar el escenario en que se declaran 25 familias y una decena de ellas tiene un F1 cercano a cero, que arrastra la métrica global y hace inútil el sistema en producción.

**Consecuencia que hay que comunicar a la Facultad:** es probable que no salgan 25 familias viables solo con repositorios. Es mejor entregar 12 familias con 85% que 25 familias con 40%.

## 7. Calidad del dato y prevención de fugas

Es la parte del diseño que más determina si el sistema funciona. Cuatro reglas no negociables:

1. **Agrupamiento en los splits.** El particionado train/val/test se hace **por observación y por observador**, nunca por imagen suelta. Dos fotos del mismo individuo repartidas entre train y test producen métricas infladas que se derrumban en campo.
2. **Solo ejemplares adultos.** Filtro `term_id=1&term_value_id=2` de la API de iNaturalist. Ya está validado empíricamente: en la demo, filtrar adultos subió la precisión de ~77% a 90.6%, porque las clases mezclaban larvas, orugas y fotos de hábitat.
3. **Deduplicado perceptual** (pHash) dentro de cada clase, entre clases y contra las imágenes ya usadas en `insectos-demo/`.
4. **Conjunto de prueba de campo separado.** Las fotografías que aporte la Facultad se apartan íntegras en `datos/campo/` y **nunca entran a entrenamiento ni a validación**. Es la única medición honesta de cómo se comporta el modelo con una foto de celular tomada en una parcela, que siempre es peor que con una foto curada de iNaturalist.

## 8. Métricas y criterio de aceptación

La exactitud global (*accuracy*) es engañosa con clases desbalanceadas: un modelo que ignore las familias raras puede exhibir buena exactitud y ser inservible. Se reporta:

| Métrica                   | Qué mide                                                               |
| ------------------------- | ---------------------------------------------------------------------- |
| macro-F1 de orden         | Desempeño promedio por clase, sin premiar a las clases mayoritarias    |
| macro-F1 de familia       | Ídem, sobre las familias admitidas                                     |
| Exactitud jerárquica      | Fracción de casos con orden **y** familia correctos                    |
| Top-3 de familia          | Utilidad práctica para un usuario que revisa opciones                  |
| Cobertura @ confianza ≥ τ | Qué porcentaje de casos el sistema responde sin declarar incertidumbre |
| F1 por clase              | Tabla completa; ninguna clase se esconde en el promedio                |

**Criterio de aceptación:** las metas de ≥90% (orden) y ≥85% (familia) se evalúan como **macro-F1 sobre el conjunto de prueba de campo**, no sobre validación de iNaturalist. Se reportan ambas cifras siempre, y la diferencia entre ellas es en sí misma un resultado que el informe debe explicar.

## 9. Base de datos y su conexión con el modelo

La BD biológica (19 columnas, definidas en `reunion/5_Base_de_Datos_Estructura.md`) se mantiene en **Excel** porque es lo que el equipo de Agronomía puede llenar sin instalar nada. `importar.py` la convierte a **SQLite** y valida que cada `Orden`/`Familia` exista en `clases.yaml`, rechazando filas inconsistentes con un reporte de errores.

El backend usa esa BD **después** de predecir: el modelo devuelve orden y familia, y la BD aporta la ficha (nombre común, cultivo asociado, tipo de daño, hospedero, importancia económica). Es lo que convierte una etiqueta taxonómica en información útil para agronomía, y materializa el vínculo entre el Producto 2 (base de datos) y el Producto 3 (banco de imágenes) del documento IF.

## 10. Backend y frontend

**Backend (FastAPI):**

| Endpoint          | Función                                                 |
| ----------------- | ------------------------------------------------------- |
| `POST /predecir`  | Imagen → orden, familia, confianzas, top-3, ficha de BD |
| `GET /clases`     | Ontología vigente servida desde `clases.yaml`           |
| `GET /taxon/{id}` | Ficha biológica completa desde SQLite                   |
| `GET /salud`      | Versión del modelo, versión de ontología, estado        |

Inferencia con **ONNX Runtime** en CPU: sin dependencia de GPU en despliegue, y coherente con lo ya probado en la demo.

**Frontend (React + Vite):** subida de foto, resultado jerárquico con las dos confianzas, top-3 de familia cuando hay incertidumbre, ficha biológica y explorador de la base de datos. Se reutilizan los patrones ya probados en `cassava-disease-detector`.

## 11. Cronograma (16 semanas)

| Semanas | Entregable                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------ |
| 1–3     | Repo estructurado, `censo.py`, `docs/censo_disponibilidad.md`, **ontología congelada con la Facultad** |
| 4–7     | Descarga masiva, curación, banco de imágenes v1, BD Excel → SQLite operativa                           |
| 8–11    | Entrenamiento multi-tarea, iteración de hiperparámetros, export ONNX, informe de métricas              |
| 12–14   | Backend FastAPI + frontend React, evaluación contra el conjunto de campo                               |
| 15–16   | Ajustes finales, informe de resultados, presentación                                                   |

## 12. Mapeo a los productos exigidos

| Producto (documento IF)                 | Cómo se cumple                                                                                          |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 1. Colección entomológica digital       | Campo `Vistas_fotograficas` en la BD + estructura de carpetas por vista para el material de la Facultad |
| 2. Base de datos de insectos amazónicos | `bd/bd_insectos.xlsx` → SQLite, 19 columnas, consultable desde el prototipo                             |
| 3. Banco de imágenes (+5000 fotos)      | `datos/curado/` (repositorios) + `datos/campo/` (colecta propia)                                        |
| Prototipo web de consulta               | `backend/` + `frontend/`                                                                                |

## 13. Riesgos

| Riesgo                                                        | Mitigación                                                                                              |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Familias sin datos suficientes en repositorios                | Regla de admisión (§6) + clase `Otros_<Orden>`; se decide con el censo, no al final                     |
| Brecha entre foto de repositorio y foto de campo              | Conjunto de prueba de campo separado (§7.4); la métrica reportada es la de campo                        |
| Demora de la Facultad en confirmar clases                     | Pipeline agnóstico a la lista; el censo avanza en paralelo                                              |
| Sesgo geográfico (mayoría de observaciones no son amazónicas) | El censo reporta disponibilidad con y sin filtro geográfico; se decide por clase si conviene restringir |
| Licencias de imágenes                                         | Solo Creative Commons; `descarga.py` registra licencia y autor por imagen para la atribución            |

## 14. Decisiones cerradas

- Alcance: solo insectos, orden → familia. Plagas de cultivos quedan como Fase 2.
- Modelo: multi-tarea con enmascaramiento jerárquico (opción B).
- Ontología: archivo de configuración, congelada en Semana 3 con datos del censo.
- Arquitectura: monorepo nuevo con pipeline Python + FastAPI + React.
- Fuentes de datos: iNaturalist y GBIF. IP102 no se usa (es de plagas de cultivos, Fase 2).
