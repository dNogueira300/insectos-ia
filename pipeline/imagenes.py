"""Descarga, normalización y huella perceptual de imágenes."""
from __future__ import annotations

import io
from pathlib import Path

import imagehash
from PIL import Image

Image.MAX_IMAGE_PIXELS = 100_000_000  # evita el aviso de bomba de descompresión


def descargar_imagen(url: str, *, sesion, min_lado: int = 224, timeout: int = 30):
    """Descarga una imagen. Devuelve None si falla o si es demasiado chica."""
    try:
        respuesta = sesion.get(url, timeout=timeout)
        respuesta.raise_for_status()
        img = Image.open(io.BytesIO(respuesta.content)).convert("RGB")
    except Exception:
        return None
    if min(img.size) < min_lado:
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


def distancia(hash_a: str, hash_b: str) -> int:
    """Distancia de Hamming entre dos huellas hexadecimales."""
    return bin(int(hash_a, 16) ^ int(hash_b, 16)).count("1")


def bandas(hash_hex: str) -> tuple[str, str, str, str]:
    """Parte la huella en 4 bandas de 16 bits.

    Dos huellas a distancia <= 3 comparten al menos una banda idéntica
    (principio del palomar). Es lo que hace viable deduplicar sin comparar
    todos los pares.
    """
    return (hash_hex[0:4], hash_hex[4:8], hash_hex[8:12], hash_hex[12:16])
