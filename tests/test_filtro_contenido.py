import csv
from pathlib import Path

import pytest
from PIL import Image

from pipeline.curacion import COLUMNAS_CURADO, NOMBRE_MANIFIESTO_CURADO
from pipeline.filtro_contenido import (
    MOTIVO_ILEGIBLE,
    MOTIVO_SIN_INSECTO,
    NOMBRE_DESCARTES,
    NOMBRE_MANIFIESTO_FILTRADO,
    NOMBRE_PUNTAJES,
    ejecutar,
    filtrar,
    puntuar,
    reporte_markdown,
)


def fila(archivo, orden="OrdenA", familia="FamiliaX", obs_id=1):
    base = {c: "" for c in COLUMNAS_CURADO}
    base.update(archivo=archivo, orden=orden, familia=familia, obs_id=str(obs_id))
    return base


class ClasificadorPorColor:
    """Clasificador falso: el canal rojo de la imagen ES el puntaje (0-255 -> 0-1).

    Así cada imagen de prueba declara en su propio contenido qué puntaje
    debe recibir, y la prueba verifica que ese puntaje llegó a la fila
    correcta, no solo que se llamó a algo.
    """

    def __init__(self):
        self.lotes: list[int] = []

    def __call__(self, imagenes: list[Image.Image]) -> list[float]:
        self.lotes.append(len(imagenes))
        return [img.getpixel((0, 0))[0] / 255 for img in imagenes]


def imagen(raiz: Path, archivo: str, puntaje: float) -> str:
    ruta = raiz / archivo
    ruta.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 32), (round(puntaje * 255), 0, 0)).save(ruta, "PNG")
    return archivo


def test_filtrar_separa_por_umbral_y_conserva_el_empate():
    filas = [fila("a.png"), fila("b.png"), fila("c.png")]
    puntajes = {"a.png": 0.9, "b.png": 0.5, "c.png": 0.1}
    conservadas, descartadas = filtrar(filas, puntajes, umbral=0.5)
    assert [f["archivo"] for f in conservadas] == ["a.png", "b.png"]
    assert [f["archivo"] for f in descartadas] == ["c.png"]
    assert descartadas[0]["motivo"] == MOTIVO_SIN_INSECTO
    assert descartadas[0]["puntaje"] == pytest.approx(0.1)


def test_filtrar_descarta_como_ilegible_lo_que_no_tiene_puntaje():
    conservadas, descartadas = filtrar([fila("roto.png")], {"roto.png": None}, umbral=0.5)
    assert conservadas == []
    assert descartadas[0]["motivo"] == MOTIVO_ILEGIBLE


def test_puntuar_asigna_a_cada_archivo_su_puntaje_en_lotes(tmp_path: Path):
    valores = [0.2, 0.4, 0.6, 0.8, 1.0]
    filas = [fila(imagen(tmp_path, f"x/{i}.png", v)) for i, v in enumerate(valores)]
    clasificador = ClasificadorPorColor()
    puntajes = puntuar(filas, tmp_path, clasificador, lote=2)
    assert clasificador.lotes == [2, 2, 1]
    for i, v in enumerate(valores):
        assert puntajes[f"x/{i}.png"] == pytest.approx(v, abs=0.01)


def test_puntuar_no_reclasifica_lo_que_ya_esta_en_cache(tmp_path: Path):
    filas = [fila(imagen(tmp_path, "a.png", 0.2)), fila(imagen(tmp_path, "b.png", 0.8))]
    clasificador = ClasificadorPorColor()
    puntajes = puntuar(filas, tmp_path, clasificador, previos={"a.png": 0.33})
    assert clasificador.lotes == [1]
    assert puntajes["a.png"] == pytest.approx(0.33)


def test_puntuar_una_imagen_ilegible_no_tumba_el_lote(tmp_path: Path):
    buena = imagen(tmp_path, "bien.png", 0.8)
    (tmp_path / "roto.png").write_bytes(b"no es una imagen")
    puntajes = puntuar([fila("roto.png"), fila(buena)], tmp_path, ClasificadorPorColor())
    assert puntajes["roto.png"] is None
    assert puntajes["bien.png"] == pytest.approx(0.8, abs=0.01)


def _escribir_curado(raiz: Path, filas: list[dict]) -> None:
    with (raiz / NOMBRE_MANIFIESTO_CURADO).open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(COLUMNAS_CURADO))
        escritor.writeheader()
        escritor.writerows(filas)


def _leer(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_ejecutar_escribe_filtrado_descartes_y_cache(tmp_path: Path):
    filas = [
        fila(imagen(tmp_path, "A/X/1.png", 0.9), obs_id=1),
        fila(imagen(tmp_path, "A/X/2.png", 0.1), obs_id=2),
    ]
    _escribir_curado(tmp_path, filas)

    resumen = ejecutar(tmp_path, ClasificadorPorColor(), umbral=0.5)

    filtrado = _leer(tmp_path / NOMBRE_MANIFIESTO_FILTRADO)
    assert [f["obs_id"] for f in filtrado] == ["1"]
    assert list(filtrado[0]) == list(COLUMNAS_CURADO)
    descartes = _leer(tmp_path / NOMBRE_DESCARTES)
    assert [(f["obs_id"], f["motivo"]) for f in descartes] == [("2", MOTIVO_SIN_INSECTO)]
    assert {f["archivo"] for f in _leer(tmp_path / NOMBRE_PUNTAJES)} == {"A/X/1.png", "A/X/2.png"}
    assert resumen["entrada"] == 2 and resumen["conservadas"] == 1


def test_ejecutar_con_otro_umbral_reutiliza_la_cache_sin_clasificar(tmp_path: Path):
    """Ajustar el umbral no debe costar otra pasada del modelo por 40 mil fotos."""
    filas = [fila(imagen(tmp_path, "1.png", 0.3), obs_id=1)]
    _escribir_curado(tmp_path, filas)
    ejecutar(tmp_path, ClasificadorPorColor(), umbral=0.5)

    segundo = ClasificadorPorColor()
    resumen = ejecutar(tmp_path, segundo, umbral=0.2)
    assert segundo.lotes == []
    assert resumen["conservadas"] == 1


def test_ejecutar_no_toca_el_manifiesto_curado_ni_las_imagenes(tmp_path: Path):
    filas = [fila(imagen(tmp_path, "1.png", 0.1), obs_id=1)]
    _escribir_curado(tmp_path, filas)
    antes = (tmp_path / NOMBRE_MANIFIESTO_CURADO).read_bytes()
    ejecutar(tmp_path, ClasificadorPorColor(), umbral=0.5)
    assert (tmp_path / NOMBRE_MANIFIESTO_CURADO).read_bytes() == antes
    assert (tmp_path / "1.png").exists()


def test_reporte_muestra_el_porcentaje_descartado_por_clase():
    resumen = {
        "entrada": 4,
        "conservadas": 2,
        "umbral": 0.5,
        "por_clase": {"OrdenA/FamiliaX": {"entrada": 4, "descartadas": 2}},
    }
    texto = reporte_markdown(resumen)
    assert "| OrdenA/FamiliaX | 4 | 2 | 50% |" in texto
    assert "0.5" in texto
