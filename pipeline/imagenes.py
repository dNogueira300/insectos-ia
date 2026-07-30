"""Descarga, normalización y huella perceptual de imágenes."""
from __future__ import annotations

import io
import logging
from pathlib import Path

import imagehash
from PIL import Image

Image.MAX_IMAGE_PIXELS = 100_000_000  # evita el aviso de bomba de descompresión

# Longitud en caracteres hexadecimales de una huella de 64 bits.
LARGO_HUELLA = 16

_log = logging.getLogger(__name__)


def descargar_imagen(
    url: str, *, sesion, min_lado: int = 224, timeout: int = 30
) -> Image.Image | None:
    """Descarga una imagen. Devuelve None si falla o si es demasiado chica.

    Nunca propaga la excepción: una descarga masiva de horas no puede morir
    por una foto rota. Pero sí registra el motivo, porque sin rastro es
    imposible distinguir "la URL no respondió" de "el archivo está corrupto".
    """
    try:
        respuesta = sesion.get(url, timeout=timeout)
        respuesta.raise_for_status()
        img = Image.open(io.BytesIO(respuesta.content)).convert("RGB")
    except Exception as error:
        _log.debug("no se pudo descargar %s: %s: %s", url, type(error).__name__, error)
        return None
    if min(img.size) < min_lado:
        _log.debug("descartada %s: lado menor %d < %d", url, min(img.size), min_lado)
        return None
    return img


def normalizar(img: Image.Image, lado_max: int = 800) -> Image.Image:
    """Reduce la imagen si excede `lado_max`. Nunca la agranda."""
    if max(img.size) <= lado_max:
        return img
    escala = lado_max / max(img.size)
    nuevo = (round(img.width * escala), round(img.height * escala))
    return img.resize(nuevo, Image.LANCZOS)


def guardar_jpeg(img: Image.Image, ruta: Path, calidad: int = 90) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta, "JPEG", quality=calidad)


def hash_perceptual(img: Image.Image) -> str:
    """Huella de 64 bits en hexadecimal. Resistente a recompresión y escalado."""
    return str(imagehash.phash(img))


def _normalizada(hash_hex: str) -> str:
    """Rellena la huella a 16 caracteres.

    No es redundante: `bandas` trocea por posición de carácter, así que una
    huella que perdió un cero a la izquierda al serializarse produciría bandas
    desplazadas y sin solape con las de la misma huella bien formada. El
    deduplicado dejaría pasar el duplicado en silencio. No quitar.
    """
    return hash_hex.zfill(LARGO_HUELLA)


def distancia(hash_a: str, hash_b: str) -> int:
    """Distancia de Hamming entre dos huellas hexadecimales."""
    return bin(int(_normalizada(hash_a), 16) ^ int(_normalizada(hash_b), 16)).count("1")


def bandas(hash_hex: str) -> tuple[str, str, str, str]:
    """Parte la huella en 4 bandas de 16 bits.

    Dos huellas a distancia <= 3 comparten al menos una banda idéntica
    (principio del palomar): tres diferencias no pueden repartirse entre
    cuatro bandas disjuntas sin dejar una intacta. Es lo que hace viable
    deduplicar sin comparar todos los pares.
    """
    huella = _normalizada(hash_hex)
    return (huella[0:4], huella[4:8], huella[8:12], huella[12:16])
