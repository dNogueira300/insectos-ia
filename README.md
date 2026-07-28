# insectos-ia

Sistema de IA para la identificación jerárquica (orden → familia) de insectos
amazónicos de importancia económica.
Proyecto Formativo INAAM–FISI + Responsabilidad Social, UNAP.

Diseño: `docs/2026-07-28-sistema-insectos-diseno.md`
Plan de la fase de datos: `docs/2026-07-28-plan-01-fase-datos.md`

## Entorno

Requiere **Python 3.12** (no 3.14: falta soporte estable de torch/onnxruntime).

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
```

## Estructura

- `ontologia/clases.yaml` — única fuente de verdad de las clases del sistema.

- `pipeline/` — censo, descarga, curación y particionado de datos.

- `bd/` — base de datos biológica (Excel → SQLite).

- `datos/` — imágenes y manifiestos. **No se versiona.**

- `docs/` — diseño, planes y reportes generados.
