"""Cliente de la API pública de iNaturalist.

Paginación por cursor (`id_above`), no por número de página: la API corta la
paginación clásica en 10 000 resultados y el sistema necesita bajar más.
"""
from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass

import requests

API = "https://api.inaturalist.org/v1"
USER_AGENT = "insectos-ia-UNAP/1.0 (proyecto academico; eliasdna0499@gmail.com)"
POR_PAGINA = 200
PAUSA_SEGUNDOS = 1.0


@dataclass(frozen=True)
class Observacion:
    id: int
    taxon_id: int
    taxon_nombre: str
    rango: str
    observador: str
    foto_url: str
    licencia: str
    atribucion: str
    latitud: float | None
    longitud: float | None
    fecha: str


def nueva_sesion() -> requests.Session:
    """Sesión con el User-Agent que exige iNaturalist."""
    sesion = requests.Session()
    sesion.headers.update({"User-Agent": USER_AGENT})
    return sesion


def _parametros(taxon_id: int, solo_adultos: bool, lugar_id: int | None) -> dict:
    params = {
        "taxon_id": taxon_id,
        "quality_grade": "research",
        "photos": "true",
        "locale": "es",
    }
    if solo_adultos:
        # Anotación "Life Stage = Adult": excluye larvas, orugas y ninfas,
        # que ensucian las clases y hunden la precisión.
        params["term_id"] = 1
        params["term_value_id"] = 2
    if lugar_id:
        params["place_id"] = lugar_id
    return params


def contar_observaciones(
    taxon_id: int,
    *,
    solo_adultos: bool = True,
    lugar_id: int | None = None,
    sesion=None,
) -> int:
    """Cuántas observaciones existen, sin descargar ninguna."""
    sesion = sesion or nueva_sesion()
    params = _parametros(taxon_id, solo_adultos, lugar_id) | {"per_page": 0}
    respuesta = sesion.get(f"{API}/observations", params=params, timeout=30)
    respuesta.raise_for_status()
    return int(respuesta.json().get("total_results", 0))


def _a_observacion(cruda: dict) -> Observacion | None:
    oid = cruda.get("id")
    if oid is None:
        return None

    fotos = cruda.get("photos") or []
    if not fotos:
        return None
    url = fotos[0].get("url") or ""
    if not url:
        return None
    prefijo, separador, sufijo = url.rpartition("square")
    if separador:
        # Solo se reemplaza la última aparición de "square" (el nombre de
        # archivo del tamaño de la foto); una aparición previa en la ruta
        # (por ejemplo en el dominio) queda intacta.
        url = f"{prefijo}medium{sufijo}"
    # Si "square" no aparece en la URL, se entrega tal cual: la descarga
    # posterior filtra por tamaño mínimo, así que no hace falta descartarla.

    taxon = cruda.get("taxon") or {}
    latitud = longitud = None
    ubicacion = cruda.get("location")
    if ubicacion and "," in ubicacion:
        try:
            latitud, longitud = (float(v) for v in ubicacion.split(",", 1))
        except ValueError:
            latitud = longitud = None

    return Observacion(
        id=int(oid),
        taxon_id=int(taxon.get("id") or 0),
        taxon_nombre=taxon.get("name") or "",
        rango=taxon.get("rank") or "",
        observador=(cruda.get("user") or {}).get("login") or "desconocido",
        foto_url=url,
        licencia=fotos[0].get("license_code") or "",
        atribucion=fotos[0].get("attribution") or "",
        latitud=latitud,
        longitud=longitud,
        fecha=cruda.get("observed_on") or "",
    )


def iterar_observaciones(
    taxon_id: int,
    *,
    limite: int,
    solo_adultos: bool = True,
    lugar_id: int | None = None,
    sesion=None,
    pausa: float = PAUSA_SEGUNDOS,
) -> Iterator[Observacion]:
    """Entrega hasta `limite` observaciones, una foto por observación."""
    sesion = sesion or nueva_sesion()
    entregadas = 0
    id_above = 0

    while entregadas < limite:
        params = _parametros(taxon_id, solo_adultos, lugar_id) | {
            "per_page": POR_PAGINA,
            "order_by": "id",
            "order": "asc",
            "id_above": id_above,
        }
        respuesta = sesion.get(f"{API}/observations", params=params, timeout=30)
        respuesta.raise_for_status()
        resultados = respuesta.json().get("results", [])
        if not resultados:
            return

        for cruda in resultados:
            oid = cruda.get("id")
            if oid is not None:
                id_above = max(id_above, int(oid))
            observacion = _a_observacion(cruda)
            if observacion is None:
                continue
            yield observacion
            entregadas += 1
            if entregadas >= limite:
                return

        if pausa:
            time.sleep(pausa)


def buscar_lugar(nombre: str, sesion=None) -> int | None:
    """Resuelve el `place_id` de iNaturalist a partir de un nombre.

    Se usa para no escribir identificadores de lugar a mano en la configuración.
    """
    sesion = sesion or nueva_sesion()
    respuesta = sesion.get(
        f"{API}/places/autocomplete", params={"q": nombre, "per_page": 1}, timeout=30
    )
    respuesta.raise_for_status()
    resultados = respuesta.json().get("results", [])
    if not resultados:
        return None
    oid = resultados[0].get("id")
    return int(oid) if oid is not None else None
