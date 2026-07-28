"""Conteo de ocurrencias con imagen en GBIF.

Solo se usa para el censo de disponibilidad. La descarga de imágenes en esta
fase sale de iNaturalist; GBIF entra como fuente de imágenes solo si el censo
muestra que alguna clase no llega al umbral.
"""
from __future__ import annotations

import requests

API = "https://api.gbif.org/v1/occurrence/search"
USER_AGENT = "insectos-ia-UNAP/1.0 (proyecto academico; eliasdna0499@gmail.com)"


def nueva_sesion() -> requests.Session:
    sesion = requests.Session()
    sesion.headers.update({"User-Agent": USER_AGENT})
    return sesion


def contar_ocurrencias(taxon_key: int, *, pais: str | None = None, sesion=None) -> int:
    """Ocurrencias con foto para un taxón. `pais` es código ISO-2, p. ej. 'PE'."""
    if not taxon_key:
        return 0
    sesion = sesion or nueva_sesion()
    params = {"taxonKey": taxon_key, "mediaType": "StillImage", "limit": 0}
    if pais:
        params["country"] = pais
    respuesta = sesion.get(API, params=params, timeout=30)
    respuesta.raise_for_status()
    return int(respuesta.json().get("count", 0))
