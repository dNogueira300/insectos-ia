import json

import numpy as np
from PIL import Image

from pipeline.marca_web import aclarar_oscuros, generar, quitar_fondo

FONDO = (252, 252, 250)
PETROLEO = (0, 56, 56)
VERDE = (16, 112, 56)


def hoja_sintetica(ruta):
    """Una hoja de marca diminuta: fondo plano, un 'símbolo' y una 'palabra'."""
    img = Image.new("RGB", (300, 260), FONDO)
    a = np.asarray(img).copy()
    a[20:120, 100:200] = PETROLEO        # símbolo, parte oscura
    a[60:120, 100:140] = VERDE           # símbolo, hoja verde
    a[150:190, 40:260] = PETROLEO        # palabra
    Image.fromarray(a).save(ruta)
    return (90, 10, 210, 130), (30, 140, 270, 200)


def test_quitar_fondo_deja_el_fondo_transparente_y_el_dibujo_opaco():
    img = Image.new("RGB", (40, 40), FONDO)
    a = np.asarray(img).copy()
    a[10:30, 10:30] = PETROLEO
    salida = np.asarray(quitar_fondo(Image.fromarray(a)))
    assert salida[0, 0, 3] == 0
    assert salida[20, 20, 3] == 255
    assert tuple(salida[20, 20, :3]) == PETROLEO


def test_quitar_fondo_deja_semitransparente_solo_el_borde_tenue():
    """Un píxel apenas teñido (el borde más externo) queda a medias; uno con
    tinta clara pero saturada, como el verde lima de las alas, queda opaco."""
    tenue = tuple(round(0.05 * p + 0.95 * f) for p, f in zip(PETROLEO, FONDO))
    lima = (163, 217, 119)
    img = Image.new("RGB", (30, 30), FONDO)
    a = np.asarray(img).copy()
    a[5:15, 5:15] = tenue
    a[16:26, 16:26] = lima
    salida = np.asarray(quitar_fondo(Image.fromarray(a)))
    assert 0 < salida[10, 10, 3] < 255
    assert salida[20, 20, 3] == 255


def test_aclarar_oscuros_cambia_el_petroleo_y_respeta_el_verde():
    rgba = np.zeros((1, 2, 4), dtype=np.uint8)
    rgba[0, 0] = (*PETROLEO, 255)
    rgba[0, 1] = (*VERDE, 255)
    salida = np.asarray(aclarar_oscuros(Image.fromarray(rgba, "RGBA")))
    assert tuple(salida[0, 0, :3]) == (255, 255, 255)
    assert tuple(salida[0, 1, :3]) == VERDE


def test_generar_escribe_todos_los_archivos(tmp_path):
    hoja = tmp_path / "hoja.png"
    caja_simbolo, caja_palabra = hoja_sintetica(hoja)
    publico = tmp_path / "public"
    rutas = generar(hoja, publico, caja_simbolo, caja_palabra)
    nombres = {r.relative_to(publico).as_posix() for r in rutas}
    assert {
        "favicon.ico", "manifest.webmanifest",
        "marca/logo-horizontal.webp", "marca/logo-horizontal.png",
        "marca/simbolo.webp", "marca/simbolo.png", "marca/simbolo-claro.webp",
        "marca/apple-touch-icon.png", "marca/icon-192.png", "marca/icon-512.png",
    } <= nombres
    assert all(r.exists() for r in rutas)
    with Image.open(publico / "marca" / "icon-512.png") as icono:
        assert icono.size == (512, 512)
    with Image.open(publico / "marca" / "logo-horizontal.png") as logo:
        assert logo.height == 96 and logo.width > logo.height
        assert logo.getchannel("A").getextrema()[0] == 0   # tiene transparencia real
    with Image.open(publico / "favicon.ico") as ico:
        assert {(16, 16), (32, 32), (48, 48)} <= set(ico.info["sizes"])
    manifiesto = json.loads((publico / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifiesto["name"] == "INSECTIA"
    assert manifiesto["start_url"] == "/identificar/"
    assert {i["sizes"] for i in manifiesto["icons"]} == {"192x192", "512x512"}
