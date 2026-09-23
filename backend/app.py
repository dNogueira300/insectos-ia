"""API del prototipo de identificación de insectos."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.fichas import RepositorioFichas
from backend.servicio import ErrorImagen, ServicioInsectos

RAIZ = Path(__file__).resolve().parent.parent
# Corrida que sirve el prototipo. Al registrar una mejor, cambiarla aquí y en
# iniciar.bat; MODELO_DIR permite apuntar a otra sin tocar código.
CORRIDA_VIGENTE = "v4_convnext_t_288"
ORIGENES = ["http://localhost:5173", "http://127.0.0.1:5173"]


def crear_app(servicio, repositorio) -> FastAPI:
    """Fábrica con dependencias inyectadas: las pruebas usan dobles."""
    app = FastAPI(
        title="Identificador de insectos amazónicos",
        description="Clasificación jerárquica orden → familia",
        version="1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGENES,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/salud")
    def salud() -> dict:
        return {
            "estado": "ok",
            **servicio.version(),
            "bd_disponible": repositorio.disponible(),
        }

    @app.get("/clases")
    def clases() -> dict:
        return servicio.clases()

    @app.post("/predecir")
    async def predecir(archivo: UploadFile = File(...)) -> dict:
        datos = await archivo.read()
        try:
            prediccion = servicio.predecir_bytes(datos)
        except ErrorImagen as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        return {
            "orden": prediccion.orden,
            "confianza_orden": prediccion.confianza_orden,
            "familia": prediccion.familia,
            "confianza_familia": prediccion.confianza_familia,
            "familia_incierta": prediccion.familia_incierta,
            "top_familias": [
                {"familia": nombre, "confianza": valor}
                for nombre, valor in prediccion.top_familias
            ],
            "fichas": repositorio.por_taxon(prediccion.orden, prediccion.familia),
        }

    @app.get("/taxon/{orden}")
    def taxon(orden: str, familia: str = "") -> dict:
        return {
            "orden": orden,
            "familia": familia,
            "fichas": repositorio.por_taxon(orden, familia),
        }

    @app.get("/resumen")
    def resumen() -> dict:
        return {"por_orden": repositorio.resumen_por_orden()}

    return app


def app_produccion() -> FastAPI:
    """Fábrica de la app real. Carga el modelo al arrancar, no al importar.

    Se usa con `uvicorn backend.app:app_produccion --factory`. Si esto se
    construyera a nivel de módulo, importar `backend.app` para probarlo
    fallaría mientras no exista el ONNX de la corrida.
    """
    carpeta = Path(os.environ.get("MODELO_DIR", RAIZ / "modelo" / CORRIDA_VIGENTE))
    return crear_app(
        ServicioInsectos(carpeta / "insectos.onnx", carpeta / "etiquetas.json"),
        RepositorioFichas(
            Path(os.environ.get("BD_SQLITE", RAIZ / "bd" / "bd_insectos.sqlite"))
        ),
    )
