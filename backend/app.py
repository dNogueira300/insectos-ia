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
# Tope de peso de una foto. Las de teléfono rondan 2–8 MB; más que esto es
# otra cosa, y se rechaza sin cargarla entera en memoria.
MAXIMO_BYTES = 20 * 1024 * 1024
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
    def predecir(archivo: UploadFile = File(...)) -> dict:
        # `def` y no `async def`: FastAPI lo corre en un hilo aparte, así la
        # inferencia (CPU, varios cientos de ms) no frena al resto del servidor.
        datos = archivo.file.read(MAXIMO_BYTES + 1)
        if len(datos) > MAXIMO_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"la foto pesa más de {MAXIMO_BYTES // (1024 * 1024)} MB: usa una más liviana",
            )
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
            # Con familia incierta, `familia` trae la primera candidata: mostrar su
            # ficha la presentaría como confirmada. Se muestran las del orden.
            "fichas": repositorio.por_taxon(
                prediccion.orden, "" if prediccion.familia_incierta else prediccion.familia
            ),
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

    # Sirve el frontend construido, si existe. En desarrollo se usa Vite (5173)
    # y este bloque simplemente no se activa.
    dist = RAIZ / "frontend" / "dist"
    if dist.exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")

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
