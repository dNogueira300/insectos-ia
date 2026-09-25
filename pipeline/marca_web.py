"""Recursos de marca para la web, a partir de la hoja de marca.

`logo_1.png` y `favicon.png` traen el fondo mal quitado: casi todo el dibujo
quedó semitransparente y se ve desteñido sobre la página. La hoja de marca
(`imagen_1.png`) tiene el logo sobre un fondo plano casi blanco. De ahí se
recorta y se quita el fondo según la distancia de cada píxel a ese color.

    python -m pipeline.marca_web --hoja ../imagenes_web/imagen_1.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# Cajas (x0, y0, x1, y1) medidas en imagen_1.png, con 8 px de margen.
CAJA_SIMBOLO = (329, 111, 827, 558)
CAJA_PALABRA = (136, 569, 1022, 716)

# Distancia L1 (suma de las diferencias RGB) al color de fondo: por debajo de
# DISTANCIA_FONDO el píxel es fondo; por encima de DISTANCIA_TINTA es dibujo
# opaco; entre ambas es un borde mezclado.
DISTANCIA_FONDO = 8
DISTANCIA_TINTA = 60

PETROLEO = (15, 61, 62, 255)
ALTO_LOGO = 96        # 2x para una cabecera de 48 px
ALTO_SIMBOLO = 256


def color_de_fondo(img: Image.Image) -> np.ndarray:
    """Mediana de las cuatro esquinas del recorte: el fondo plano de la hoja."""
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    esquinas = np.concatenate([a[:8, :8], a[:8, -8:], a[-8:, :8], a[-8:, -8:]])
    return np.median(esquinas.reshape(-1, 3), axis=0)


def quitar_fondo(img: Image.Image, fondo: np.ndarray | None = None) -> Image.Image:
    rgb = np.asarray(img.convert("RGB"), dtype=np.float64)
    if fondo is None:
        fondo = color_de_fondo(img)
    distancia = np.abs(rgb - fondo).sum(axis=2)
    # Solo el borde más tenue (distancia entre 8 y 60) queda semitransparente;
    # todo lo demás es dibujo opaco. Así el logo conserva sus colores exactos y
    # el antialias de la hoja, que tras reducir a la mitad queda bajo un píxel.
    alfa = np.clip(
        (distancia - DISTANCIA_FONDO) / (DISTANCIA_TINTA - DISTANCIA_FONDO), 0.0, 1.0
    )
    color = np.where(alfa[..., None] > 0, rgb, 0.0)
    rgba = np.dstack([color, alfa * 255]).round().astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def recortar_a_tinta(img: Image.Image) -> Image.Image:
    caja = img.getchannel("A").getbbox()
    return img.crop(caja) if caja else img


def aclarar_oscuros(img: Image.Image) -> Image.Image:
    """Vuelve blancas las partes Azul Petróleo, para usar el símbolo sobre ese color.

    El petróleo es un verde azulado (G ≈ B); las hojas son verdes (G mucho mayor
    que B). Separarlos por el tono deja las hojas intactas.
    """
    rgba = np.asarray(img.convert("RGBA")).astype(np.int32)
    r, g, b, a = rgba[..., 0], rgba[..., 1], rgba[..., 2], rgba[..., 3]
    petroleo = (g - b < 16) & (g < 100) & (r < 50) & (a > 0)
    rgba[petroleo, :3] = 255
    return Image.fromarray(rgba.astype(np.uint8), "RGBA")


def a_altura(img: Image.Image, alto: int) -> Image.Image:
    ancho = round(img.width * alto / img.height)
    return img.resize((ancho, alto), Image.LANCZOS)


def logo_horizontal(simbolo: Image.Image, palabra: Image.Image) -> Image.Image:
    """Símbolo a la izquierda y "INSECTIA" a la derecha, para la cabecera."""
    alto = simbolo.height
    palabra = a_altura(palabra, round(alto * 0.42))
    hueco = round(alto * 0.12)
    lienzo = Image.new("RGBA", (simbolo.width + hueco + palabra.width, alto), (0, 0, 0, 0))
    lienzo.alpha_composite(simbolo, (0, 0))
    lienzo.alpha_composite(palabra, (simbolo.width + hueco, (alto - palabra.height) // 2))
    return lienzo


def icono(simbolo_claro: Image.Image, lado: int) -> Image.Image:
    """El símbolo aclarado sobre un cuadrado redondeado Azul Petróleo."""
    lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    ImageDraw.Draw(lienzo).rounded_rectangle(
        (0, 0, lado - 1, lado - 1), radius=round(lado * 0.22), fill=PETROLEO
    )
    interior = round(lado * 0.78)
    simbolo = simbolo_claro.copy()
    simbolo.thumbnail((interior, interior), Image.LANCZOS)
    lienzo.alpha_composite(simbolo, ((lado - simbolo.width) // 2, (lado - simbolo.height) // 2))
    return lienzo


def _guardar(img: Image.Image, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.suffix == ".webp":
        img.save(ruta, "WEBP", quality=90, method=6)
    else:
        img.save(ruta, optimize=True)


def generar(
    hoja: Path,
    publico: Path,
    caja_simbolo: tuple[int, int, int, int] = CAJA_SIMBOLO,
    caja_palabra: tuple[int, int, int, int] = CAJA_PALABRA,
) -> list[Path]:
    with Image.open(hoja) as original:
        simbolo = recortar_a_tinta(quitar_fondo(original.crop(caja_simbolo)))
        palabra = recortar_a_tinta(quitar_fondo(original.crop(caja_palabra)))
    claro = aclarar_oscuros(simbolo)
    horizontal = a_altura(logo_horizontal(simbolo, palabra), ALTO_LOGO)

    marca = Path(publico) / "marca"
    salidas = {
        marca / "logo-horizontal.webp": horizontal,
        marca / "logo-horizontal.png": horizontal,
        marca / "simbolo.webp": a_altura(simbolo, ALTO_SIMBOLO),
        marca / "simbolo.png": a_altura(simbolo, ALTO_SIMBOLO),
        marca / "simbolo-claro.webp": a_altura(claro, ALTO_SIMBOLO),
        marca / "apple-touch-icon.png": icono(claro, 180),
        marca / "icon-192.png": icono(claro, 192),
        marca / "icon-512.png": icono(claro, 512),
    }
    for ruta, img in salidas.items():
        _guardar(img, ruta)

    ico = Path(publico) / "favicon.ico"
    icono(claro, 256).save(ico, sizes=[(16, 16), (32, 32), (48, 48)])

    manifiesto = Path(publico) / "manifest.webmanifest"
    manifiesto.write_text(
        json.dumps(
            {
                "name": "INSECTIA",
                "short_name": "INSECTIA",
                "description": "Identificación de órdenes y familias de insectos de la Amazonía peruana",
                "lang": "es",
                "start_url": "/identificar/",
                "display": "standalone",
                "background_color": "#f6f8f5",
                "theme_color": "#0f3d3e",
                "icons": [
                    {"src": "/marca/icon-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "/marca/icon-512.png", "sizes": "512x512", "type": "image/png"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return [*salidas, ico, manifiesto]


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera los recursos de marca para la web")
    parser.add_argument("--hoja", required=True, help="imagen_1.png, la hoja de marca")
    parser.add_argument("--publico", default="frontend/public")
    args = parser.parse_args()
    for ruta in generar(Path(args.hoja), Path(args.publico)):
        print(f"{ruta}  {ruta.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
