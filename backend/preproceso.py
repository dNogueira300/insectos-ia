"""Preprocesamiento de imágenes para inferencia.

Replica exactamente `transformaciones_evaluacion(lado)` del pipeline de
entrenamiento: redimensiona el lado corto a `lado / PROPORCION_RECORTE`,
recorta el centro a `lado`, escala a [0,1] y normaliza con las estadísticas
de ImageNet. Usa Pillow, igual que torchvision, para que la coincidencia sea
exacta y no aproximada. El `lado` lo decide el modelo (ver `servicio.py`).
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

LADO = 224
# La misma proporción que `pipeline.datos_torch`: 224 → 256, 288 → 329.
PROPORCION_RECORTE = 224 / 256
MEDIA = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
DESVIACION = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)


def lado_redimension(lado: int) -> int:
    """Lado corto al que se redimensiona antes del recorte central."""
    return round(lado / PROPORCION_RECORTE)


def redimensionar_lado_corto(img: Image.Image, corto: int) -> Image.Image:
    """Lleva el lado corto a `corto` conservando la proporción.

    Reproduce el cálculo de torchvision.transforms.Resize con un entero:
    el lado largo se trunca, no se redondea.
    """
    ancho, alto = img.size
    if min(ancho, alto) == corto:
        return img
    if ancho < alto:
        nuevo = (corto, int(corto * alto / ancho))
    else:
        nuevo = (int(corto * ancho / alto), corto)
    return img.resize(nuevo, Image.BILINEAR)


def recortar_centro(img: Image.Image, lado: int = LADO) -> Image.Image:
    ancho, alto = img.size
    izquierda = int(round((ancho - lado) / 2.0))
    arriba = int(round((alto - lado) / 2.0))
    return img.crop((izquierda, arriba, izquierda + lado, arriba + lado))


def preparar(img: Image.Image, lado: int = LADO) -> np.ndarray:
    """Imagen PIL → tensor (1, 3, lado, lado) listo para onnxruntime."""
    img = recortar_centro(
        redimensionar_lado_corto(img.convert("RGB"), lado_redimension(lado)), lado
    )
    arreglo = np.asarray(img, dtype=np.float32) / 255.0   # alto, ancho, canal
    arreglo = arreglo.transpose(2, 0, 1)                  # canal, alto, ancho
    arreglo = (arreglo - MEDIA) / DESVIACION
    return arreglo[np.newaxis, ...].astype(np.float32)


def desde_bytes(datos: bytes, lado: int = LADO) -> np.ndarray:
    try:
        with Image.open(io.BytesIO(datos)) as img:
            # Las fotos de teléfono traen la rotación como marca EXIF. El
            # navegador la aplica al mostrarlas; el modelo tiene que recibirlas
            # igual de derechas (en entrenamiento no vio giros de 90°).
            return preparar(ImageOps.exif_transpose(img), lado)
    except Image.DecompressionBombError as error:
        # Pillow corta antes de decodificar imágenes de cientos de megapíxeles.
        raise ValueError(
            "la imagen es demasiado grande: redúcela a una foto de menos de 50 megapíxeles"
        ) from error
    except UnidentifiedImageError as error:
        raise ValueError(
            "no se reconoce el formato de la imagen: usa una foto JPG o PNG "
            "(las fotos HEIC del iPhone no se admiten)"
        ) from error
    except Exception as error:
        raise ValueError("el archivo no es una imagen válida o está dañado") from error
