import io

import numpy as np
import pytest
from PIL import Image

from backend.preproceso import (
    LADO,
    PROPORCION_RECORTE,
    desde_bytes,
    lado_redimension,
    preparar,
    recortar_centro,
    redimensionar_lado_corto,
)


def imagen(ancho=400, alto=300, semilla=1):
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(12, 16, 3), dtype=np.uint8)
    return Image.fromarray(base).resize((ancho, alto), Image.BICUBIC)


def test_redimensionar_lleva_el_lado_corto_al_objetivo():
    salida = redimensionar_lado_corto(imagen(400, 300), 256)
    assert min(salida.size) == 256


def test_redimensionar_conserva_la_proporcion():
    entrada = imagen(400, 300)
    salida = redimensionar_lado_corto(entrada, 256)
    proporcion_entrada = entrada.width / entrada.height
    proporcion_salida = salida.width / salida.height
    assert proporcion_salida == pytest.approx(proporcion_entrada, abs=0.01)


def test_redimensionar_funciona_con_imagen_vertical():
    salida = redimensionar_lado_corto(imagen(300, 500), 256)
    assert salida.width == 256


def test_recortar_centro_da_el_lado_pedido():
    assert recortar_centro(imagen(400, 300), 224).size == (224, 224)


def test_lado_redimension_da_256_para_224_y_329_para_288():
    assert lado_redimension(224) == 256
    assert lado_redimension(288) == 329


def test_preparar_devuelve_la_forma_del_modelo():
    tensor = preparar(imagen())
    assert tensor.shape == (1, 3, LADO, LADO)
    assert tensor.dtype == np.float32


def test_preparar_acepta_otra_resolucion():
    assert preparar(imagen(), lado=288).shape == (1, 3, 288, 288)


def test_preparar_normaliza_fuera_del_rango_cero_uno():
    tensor = preparar(imagen())
    assert tensor.min() < 0.0


def test_preparar_convierte_escala_de_grises_a_tres_canales():
    tensor = preparar(Image.new("L", (400, 300), color=120))
    assert tensor.shape == (1, 3, LADO, LADO)


def test_desde_bytes_acepta_un_jpeg():
    buffer = io.BytesIO()
    imagen().save(buffer, "JPEG")
    assert desde_bytes(buffer.getvalue()).shape == (1, 3, LADO, LADO)


def test_desde_bytes_respeta_la_resolucion_pedida():
    buffer = io.BytesIO()
    imagen().save(buffer, "JPEG")
    assert desde_bytes(buffer.getvalue(), lado=288).shape == (1, 3, 288, 288)


def test_desde_bytes_rechaza_contenido_invalido():
    with pytest.raises(ValueError):
        desde_bytes(b"esto no es una imagen")


def test_la_proporcion_de_recorte_es_la_del_pipeline():
    pytest.importorskip("torch")
    from pipeline import datos_torch

    assert PROPORCION_RECORTE == datos_torch.PROPORCION_RECORTE


@pytest.mark.parametrize("lado", [224, 288])
def test_paridad_con_la_transformacion_de_evaluacion(lado):
    """El backend debe preprocesar exactamente igual que la evaluación."""
    pytest.importorskip("torch")
    from pipeline.datos_torch import transformaciones_evaluacion

    entrada = imagen(500, 380, semilla=7)
    del_backend = preparar(entrada, lado=lado)[0]
    del_pipeline = transformaciones_evaluacion(lado)(entrada).numpy()

    assert del_backend.shape == del_pipeline.shape
    assert np.abs(del_backend - del_pipeline).max() < 1e-5


@pytest.mark.parametrize("lado", [224, 288])
def test_paridad_tambien_en_imagen_vertical(lado):
    pytest.importorskip("torch")
    from pipeline.datos_torch import transformaciones_evaluacion

    entrada = imagen(280, 640, semilla=9)
    diferencia = np.abs(
        preparar(entrada, lado=lado)[0] - transformaciones_evaluacion(lado)(entrada).numpy()
    ).max()
    assert diferencia < 1e-5


def test_el_backend_no_importa_torch():
    """El despliegue no debe arrastrar PyTorch.

    Se miran los imports y no el texto: el docstring puede nombrar a
    torchvision para explicar qué replica.
    """
    import ast

    import backend.preproceso as modulo

    with open(modulo.__file__, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module.split(".")[0])
    assert not importados & {"torch", "torchvision"}


def test_desde_bytes_aplica_la_orientacion_exif():
    """Los teléfonos guardan la foto vertical como píxeles apaisados y una
    marca EXIF de rotación. El navegador la muestra derecha; el modelo debe
    recibirla igual, porque en el entrenamiento no vio giros de 90°."""
    from PIL import ImageOps

    derecha = imagen(300, 500, semilla=5)  # como la ve el usuario
    guardada = derecha.transpose(Image.Transpose.ROTATE_90)  # como la guarda la cámara
    exif = Image.Exif()
    exif[0x0112] = 6  # Orientation: girar 90° en sentido horario al mostrar
    buffer = io.BytesIO()
    guardada.save(buffer, "JPEG", exif=exif, quality=95)

    with Image.open(io.BytesIO(buffer.getvalue())) as img:
        esperado = preparar(ImageOps.exif_transpose(img), lado=288)
    obtenido = desde_bytes(buffer.getvalue(), lado=288)
    assert np.abs(obtenido - esperado).max() < 1e-6


def test_formato_no_reconocido_sugiere_jpg_o_png():
    """Las fotos HEIC del iPhone, por ejemplo, Pillow no las abre."""
    with pytest.raises(ValueError, match="JPG o PNG"):
        desde_bytes(b"\x00\x00\x00\x18ftypheic esto no lo abre Pillow")


def test_imagen_de_demasiados_megapixeles_tiene_mensaje_propio(monkeypatch):
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1000)
    buffer = io.BytesIO()
    imagen(100, 100).save(buffer, "PNG")  # 10 000 píxeles: más del doble del tope
    with pytest.raises(ValueError, match="demasiado grande"):
        desde_bytes(buffer.getvalue())
