# Imagen de INSECTIA para publicarla (Google Cloud Run) o probarla en local.
#
# El modelo y la base no están en Git: se copian desde la carpeta local.
# Antes de construir deben existir:
#   modelo/v4_convnext_t_288/insectos.onnx y etiquetas.json  (de la corrida)
#   bd/bd_insectos.sqlite                                    (python -m pipeline.bd)
# Ver docs/DESPLIEGUE.md.

# --- 1. La web: se construye aquí, no hace falta frontend/dist en la PC ---
FROM node:24-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- 2. El servidor: solo onnxruntime, sin PyTorch ni pandas ---
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    ORT_HILOS=1 \
    MODELO_DIR=/app/modelo/v4_convnext_t_288
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY pipeline/ pipeline/
COPY ontologia/ ontologia/
COPY bd/esquema.sql bd/bd_insectos.sqlite bd/
COPY modelo/v4_convnext_t_288/insectos.onnx modelo/v4_convnext_t_288/etiquetas.json modelo/v4_convnext_t_288/
COPY --from=web /web/dist frontend/dist

RUN useradd --create-home insectia
USER insectia

# Cloud Run indica el puerto en PORT. ORT_HILOS debe coincidir con los vCPU
# contratados (--cpu en gcloud run deploy).
CMD ["sh", "-c", "exec uvicorn backend.app:app_produccion --factory --host 0.0.0.0 --port ${PORT}"]
