"""Lectura de la configuración con la que se entrenó una corrida.

`pipeline.entrenar` escribe un `config.json` junto a los pesos. Exportar y
evaluar lo leen de ahí en vez de confiar en que quien ejecuta el comando
recuerde repetir las mismas opciones: entrenar a 288 píxeles y exportar a 224
produciría un modelo que en producción recibe imágenes distintas de las que
aprendió, sin ningún error visible. Lo mismo con el backbone.
"""
from __future__ import annotations

import json
from pathlib import Path

NOMBRE_CONFIG = "config.json"


class ErrorCorridaIncompleta(Exception):
    """La corrida tiene un `config.json` que no se puede interpretar."""


def config_de_corrida(ruta_pesos: Path) -> dict:
    """Config de la corrida a la que pertenecen esos pesos. `{}` si no hay."""
    ruta = Path(ruta_pesos).with_name(NOMBRE_CONFIG)
    if not ruta.is_file():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ErrorCorridaIncompleta(f"{ruta}: no es un {NOMBRE_CONFIG} válido ({error})") from error
    if not isinstance(datos, dict):
        raise ErrorCorridaIncompleta(f"{ruta}: se esperaba un mapa de opciones")
    return datos


def opcion_de_corrida(ruta_pesos: Path, clave: str, *, pedido, defecto):
    """Resuelve una opción: lo pedido a mano, luego la corrida, luego el defecto."""
    if pedido is not None:
        return pedido
    return config_de_corrida(ruta_pesos).get(clave, defecto)
