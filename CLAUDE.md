# insectos-ia — guía para trabajar en este repositorio

Sistema de IA que identifica **orden → familia** de insectos amazónicos a partir de una foto.
Es el Proyecto Formativo INAAM–FISI y de Responsabilidad Social de la UNAP (Facultad de Agronomía).
La entomóloga de referencia es la Dra. Aldi Guerra Teixeira.
Hay un demo previo, independiente, en `../insectos-demo/`: 4 órdenes, Gradio.

## Estado actual (2026-09-23)

| Etapa | Estado |
| --- | --- |
| Plan 01 — datos | **Cerrado.** 34 360 fotos, repartidas 24 032 / 5 163 / 5 165 (entrenamiento / validación / prueba). |
| Plan 02 — modelo | **Código terminado.** Modelo vigente: `v3_b2_288`. Se entrena en Colab gratis (T4), una sola cuenta. |
| Plan 03 — web | Planificado (`docs/2026-07-28-plan-03-prototipo.md`). Sin empezar. |

### Corridas del modelo (conjunto de prueba, 5 165 fotos de repositorio)

| Corrida | Qué cambió | F1 orden | F1 familia | Top-3 familia |
| --- | --- | ---: | ---: | ---: |
| `v1_efficientnet_b0` | Base del plan, 224 px | 0.832 | 0.791 | 0.863 |
| `v2_antisobreajuste` | Aumentos fuertes, suavizado 0.1, tasa en coseno | 0.864 | 0.832 | 0.891 |
| `v3_b2_288` | EfficientNet-B2 a 288 px | **0.900** | **0.874** | **0.925** |

La meta del plan es ≥0.90 en orden y ≥0.85 en familia. La v3 la alcanza **sobre fotos de repositorio**. Sin conjunto de campo, eso no permite declararla cumplida.
La ficha de la Facultad pide 99 %, que no es realista; está pendiente renegociarla.
La v3 responde con 93.6 % de acierto cuando exige confianza ≥0.7, y lo hace en el 89 % de las fotos. Con la v2 eran 91.9 % y 83 %. Ver `docs/desempeno_por_clase_v3.md`.

La v3 se detuvo sola en la época 19 de 25; la mejor fue la 14. El F1 de validación quedó plano (0.856–0.857) desde entonces, sin sobreajuste.
Mejoró todas las clases débiles de la v2 salvo **Termitidae**: bajó de 0.71 a 0.67, sobre solo 50 fotos, y aún quedan montículos en su material.
Las confusiones que persisten son Formicidae↔Termitidae, las termitas entre sí y Acrididae↔Tettigoniidae.

Las mejoras se prueban **una a una**, para medir el aporte de cada cambio. El usuario lo pidió así.
El paso 3 pendiente es subir `UMBRAL_FAMILIA` de 0.45 a ~0.7 en `pipeline/inferencia.py`, apoyado en la tabla de cobertura de la v3.

## Cuando llegue una corrida nueva

El usuario descarga la carpeta de la corrida desde Drive a `D:\300\OTROS\XXX\DAN\IA\agro\entrenamiento\corridas\<corrida>`. Luego:

1. Copiar a `modelo/<corrida>/` los archivos `config.json`, `etiquetas.json`, `evaluacion.json`, `metricas.json`, `insectos.onnx`, `mejor.pth` y `ultimo.pth`. Los `.onnx` y `.pth` no se versionan.
2. Copiar `informe_metricas.md` a `docs/informe_metricas.md`.
3. Revisar el historial de `metricas.json` (tasa, pérdida y F1 por época) para ver si hubo sobreajuste o si faltaron épocas.
4. Correr `python -m pipeline.desempeno --corrida modelo/<corrida> --salida docs/desempeno_por_clase_<vN>.md`. Toma sola la resolución de `config.json`. En CPU, a 288 px, tarda unos 15 minutos.
5. Comparar contra la corrida anterior, en especial las clases débiles.
6. Commit, y actualizar la tabla de corridas de este archivo y `docs/RESUMEN_EJECUTIVO.md`.

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
- Conseguir fotos de campo: todavía no existe `campo.csv`, y sin eso no se puede declarar la meta alcanzada.

## Límites declarados

- Solo 0.5 % de las fotos son de Perú.
- El 73 % de las licencias son no comerciales.
- Poca diversidad de fotógrafos en tres familias de Odonata.
- Todavía queda un 5–10 % de montículos entre las fotos de Termitidae.
