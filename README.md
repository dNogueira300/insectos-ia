# insectos-ia

Sistema de IA para la identificación jerárquica (**orden → familia**) de insectos amazónicos de importancia económica.
Proyecto Formativo INAAM–FISI + Responsabilidad Social, UNAP.

- Estado del proyecto y resultados: [`docs/RESUMEN_EJECUTIVO.md`](docs/RESUMEN_EJECUTIVO.md)
- Guía de trabajo en el repositorio: [`CLAUDE.md`](CLAUDE.md)
- Diseño: `docs/2026-07-28-sistema-insectos-diseno.md`
- Planes:
  - 01 datos: `docs/2026-07-28-plan-01-fase-datos.md`
  - 02 modelo: `docs/2026-07-28-plan-02-modelo.md`
  - 03 web: `docs/2026-07-28-plan-03-prototipo.md`

## Entorno

Requiere **Python 3.12**. Python 3.14 no sirve: le falta soporte estable de torch y onnxruntime.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python -m pip install -e ".[modelo,filtro]"
.venv\Scripts\python -m pytest
```

## Pipeline completo

Cada paso lee y escribe en `datos/`, que no se versiona. Los reportes van a `docs/`.

| # | Paso | Comando | Tiempo aprox. |
| --- | --- | --- | --- |
| 1 | Censo de disponibilidad por clase | `python -m pipeline.censo` | minutos |
| 2 | Descarga desde iNaturalist (se puede pausar y retomar) | `python -m pipeline.descarga` | ~15 h |
| 3 | Curación: quita duplicados y archivos ilegibles | `python -m pipeline.curacion` | ~25 min |
| 4 | Filtro de contenido: quita fotos sin insecto visible (CLIP) | `python -m pipeline.filtro_contenido` | ~1 h en CPU |
| 5 | Reparto por fotógrafo, con tope de 20 fotos por fotógrafo y clase | `python -m pipeline.splits` | segundos |
| 6 | Paquete para Colab | `python -m pipeline.empaquetar` | ~15 min |
| 7 | Entrenamiento (en Colab, con `colab/entrenar.ipynb`) | `python -m pipeline.entrenar --reanudar --backbone … --lado … --destino …` | 1–4 h en T4 |
| 8 | Exportación a ONNX con verificación de paridad | `python -m pipeline.exportar --pesos <corrida>/mejor.pth --etiquetas <corrida>/etiquetas.json --salida <corrida>/insectos.onnx` | minutos |
| 9 | Evaluación contra el conjunto de prueba | `python -m pipeline.evaluar --pesos <corrida>/mejor.pth --etiquetas <corrida>/etiquetas.json` | minutos |
| 10 | Desempeño por clase y cobertura contra confianza | `python -m pipeline.desempeno --corrida <corrida> --salida docs/desempeno_por_clase_vN.md` | ~5 min en CPU |

Pasos complementarios:

- Fotos de campo de la Facultad: `python -m pipeline.campo`. Verifica que no se solapen con el entrenamiento.
- Base de datos biológica (Excel → SQLite): `python -m pipeline.bd`.

**Detalles importantes:**

- Los pasos 8, 9 y 10 leen el backbone y la resolución del `config.json` de la corrida. No hace falta repetirlos, y así no pueden quedar desajustados.
- `pipeline.splits` exige que exista `manifiesto_filtrado.csv` (paso 4). Nunca usa en silencio los datos sin filtrar.
- `datos/splits/asignacion_observadores.yaml` **se versiona y no se borra**: fija qué fotógrafo está en cada grupo. `--regenerar-asignacion` invalida la comparación con modelos anteriores.
- `pipeline.entrenar` guarda un checkpoint por época. Sin `--reanudar` no pisa una corrida existente, y con otra configuración se niega a reanudarla.

## Estructura

- `ontologia/clases.yaml`: única fuente de verdad de las clases (15 órdenes y 38 familias, v1 congelada). `candidatas.yaml` guarda la lista censada y el porqué de cada descarte.
- `pipeline/`: datos (censo, descarga, curación, filtro, particionado) y modelo (etiquetas, dataset, modelo, inferencia, métricas, entrenamiento, exportación, evaluación, desempeño).
- `colab/entrenar.ipynb`: entrenamiento en Google Colab con reanudación.
- `modelo/<corrida>/`: artefactos de cada corrida. Se versionan los `.json`; los `.onnx` y `.pth` no.
- `bd/`: base de datos biológica.
- `datos/`: imágenes y manifiestos. **No se versiona.**
- `docs/`: diseño, planes, reportes generados y resumen ejecutivo.
