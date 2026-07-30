import io
import logging
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pipeline.imagenes import (
    bandas,
    descargar_imagen,
    distancia,
    guardar_jpeg,
    hash_perceptual,
    normalizar,
)


def imagen_patron(semilla: int, lado: int = 300) -> Image.Image:
    """Imagen determinista con estructura suficiente para un hash útil."""
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    return Image.fromarray(base).resize((lado, lado), Image.BICUBIC)


def a_bytes(img: Image.Image) -> bytes:
    buffer = io.BytesIO()
    img.save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


class RespuestaFalsa:
    def __init__(self, contenido):
        self.content = contenido

    def raise_for_status(self):
        return None


class SesionImagen:
    def __init__(self, contenido):
        self.contenido = contenido

    def get(self, url, timeout=None):
        return RespuestaFalsa(self.contenido)


def test_hash_tiene_16_caracteres_hex():
    h = hash_perceptual(imagen_patron(1))
    assert len(h) == 16
    int(h, 16)  # no debe lanzar


def test_distancia_cero_para_la_misma_imagen():
    img = imagen_patron(2)
    assert distancia(hash_perceptual(img), hash_perceptual(img)) == 0


def test_distancia_pequena_tras_recomprimir_y_redimensionar():
    img = imagen_patron(3)
    variante = Image.open(io.BytesIO(a_bytes(img.resize((220, 220))))).convert("RGB")
    assert distancia(hash_perceptual(img), hash_perceptual(variante)) <= 3


def test_distancia_grande_entre_imagenes_distintas():
    a = hash_perceptual(imagen_patron(10))
    b = hash_perceptual(imagen_patron(99))
    assert distancia(a, b) > 3


def test_bandas_son_cuatro_de_cuatro_hex():
    partes = bandas("0123456789abcdef")
    assert partes == ("0123", "4567", "89ab", "cdef")


def con_bits_volteados(hash_hex: str, posiciones: tuple[int, ...]) -> str:
    """Devuelve la huella con los bits indicados invertidos.

    Permite construir huellas a una distancia de Hamming exacta, sin depender
    de que una transformación de imagen produzca esa distancia por azar.
    """
    valor = int(hash_hex, 16)
    for posicion in posiciones:
        valor ^= 1 << posicion
    return f"{valor:016x}"


BASE = "3f2a9c07b15e6d84"


@pytest.mark.parametrize(
    "posiciones",
    [(0,), (17,), (0, 40), (5, 33, 61), (2, 3, 4)],
    ids=["1 bit", "1 bit lejano", "2 bits", "3 bits dispersos", "3 bits juntos"],
)
def test_hashes_a_distancia_maxima_tres_comparten_una_banda(posiciones):
    """Garantía del principio del palomar en la que se apoya el deduplicado.

    Con 4 bandas disjuntas de 16 bits, tres diferencias no pueden repartirse
    entre las cuatro: al menos una banda queda intacta.
    """
    otra = con_bits_volteados(BASE, posiciones)
    assert distancia(BASE, otra) == len(posiciones)
    assert set(bandas(BASE)) & set(bandas(otra))


def test_cuatro_bits_repartidos_pueden_no_compartir_banda():
    """Control: el palomar solo garantiza hasta 3. Con 4 la garantía cesa."""
    otra = con_bits_volteados(BASE, (0, 16, 32, 48))  # uno en cada banda
    assert distancia(BASE, otra) == 4
    assert not set(bandas(BASE)) & set(bandas(otra))


def test_la_misma_huella_sin_cero_a_la_izquierda_da_las_mismas_bandas():
    """Un cero perdido al serializar no debe desalinear el troceado."""
    completa = "0abc123456789abc"
    sin_cero = completa.lstrip("0")
    assert distancia(completa, sin_cero) == 0
    assert bandas(completa) == bandas(sin_cero)


def test_la_misma_huella_en_mayusculas_da_las_mismas_bandas_y_distancia_cero():
    """Un cambio de mayúsculas (p. ej. al viajar por un CSV) no debe desalinear
    el troceado ni hacer parecer distintas dos huellas idénticas."""
    minusculas = "abcdefabcdefabcd"
    mayusculas = minusculas.upper()
    assert distancia(minusculas, mayusculas) == 0
    assert bandas(minusculas) == bandas(mayusculas)


def test_imagen_recomprimida_conserva_banda_comun():
    """La variante de una imagen debe seguir siendo detectable como duplicada."""
    img = imagen_patron(4)
    variante = Image.open(io.BytesIO(a_bytes(img.resize((260, 260))))).convert("RGB")
    a, b = hash_perceptual(img), hash_perceptual(variante)
    assert distancia(a, b) <= 3
    assert set(bandas(a)) & set(bandas(b))


def test_descargar_imagen_registra_el_motivo_del_fallo(caplog):
    """Un fallo silencioso en una descarga de horas es indiagnosticable."""
    sesion = SesionImagen(b"esto no es una imagen")
    with caplog.at_level(logging.DEBUG, logger="pipeline.imagenes"):
        assert descargar_imagen("http://x/rota.jpg", sesion=sesion) is None
    assert "http://x/rota.jpg" in caplog.text


def test_normalizar_limita_el_lado_mayor():
    salida = normalizar(imagen_patron(5, lado=2000), lado_max=800)
    assert max(salida.size) == 800


def test_normalizar_no_agranda_imagenes_pequenas():
    salida = normalizar(imagen_patron(5, lado=300), lado_max=800)
    assert max(salida.size) == 300


def test_descargar_imagen_devuelve_none_si_es_muy_chica():
    sesion = SesionImagen(a_bytes(imagen_patron(6, lado=100)))
    assert descargar_imagen("http://x/y.jpg", sesion=sesion, min_lado=224) is None


def test_descargar_imagen_devuelve_rgb():
    sesion = SesionImagen(a_bytes(imagen_patron(7, lado=400)))
    img = descargar_imagen("http://x/y.jpg", sesion=sesion, min_lado=224)
    assert img is not None and img.mode == "RGB"


def test_descargar_imagen_devuelve_none_si_el_contenido_no_es_imagen():
    sesion = SesionImagen(b"esto no es una imagen")
    assert descargar_imagen("http://x/y.jpg", sesion=sesion) is None


def test_guardar_jpeg_crea_las_carpetas(tmp_path: Path):
    destino = tmp_path / "a" / "b" / "foto.jpg"
    guardar_jpeg(imagen_patron(8), destino)
    assert destino.exists()
    assert Image.open(destino).mode == "RGB"
