from pipeline.etiquetas import EspacioEtiquetas
from pipeline.evaluar import reporte_markdown

ESPACIO = EspacioEtiquetas(
    ordenes=("OrdenA", "OrdenB"),
    familias=("FamA1", "FamB1"),
    matriz=((True, False), (False, True)),
)


def resultado(f1_orden, f1_familia):
    return {
        "macro_f1_orden": f1_orden,
        "macro_f1_familia": f1_familia,
        "exactitud_orden": 0.9,
        "exactitud_familia": 0.8,
        "exactitud_jerarquica": 0.75,
        "top3_familia": 0.95,
        "n": 100,
    }


def test_reporte_incluye_las_dos_columnas():
    texto = reporte_markdown(
        {"test": resultado(0.93, 0.87), "campo": resultado(0.85, 0.62)}, ESPACIO
    )
    assert "test" in texto and "campo" in texto


def test_reporte_marca_meta_alcanzada_en_campo():
    texto = reporte_markdown({"campo": resultado(0.93, 0.87)}, ESPACIO)
    assert "ALCANZADA" in texto


def test_reporte_marca_meta_no_alcanzada_en_campo():
    texto = reporte_markdown({"campo": resultado(0.93, 0.62)}, ESPACIO)
    assert "NO ALCANZADA" in texto


def test_la_meta_se_juzga_contra_campo_no_contra_test():
    """Aunque test luzca bien, si campo no llega, la meta no está alcanzada."""
    texto = reporte_markdown(
        {"test": resultado(0.99, 0.99), "campo": resultado(0.99, 0.40)}, ESPACIO
    )
    assert "NO ALCANZADA" in texto


def test_reporte_reporta_la_brecha_entre_test_y_campo():
    texto = reporte_markdown(
        {"test": resultado(0.93, 0.87), "campo": resultado(0.85, 0.62)}, ESPACIO
    )
    assert "0.25" in texto  # 0.87 - 0.62


def test_sin_campo_el_reporte_lo_dice_explicitamente():
    texto = reporte_markdown({"test": resultado(0.93, 0.87)}, ESPACIO)
    assert "sin conjunto de campo" in texto.lower()


def test_los_resultados_se_guardan_junto_a_los_pesos():
    """En Colab no existe `modelo/`: los resultados van con la corrida."""
    from pathlib import Path

    from pipeline.evaluar import destino_resultados

    assert destino_resultados(Path("drive/corridas/v1/mejor.pth")) == Path(
        "drive/corridas/v1/evaluacion.json"
    )


def test_evaluar_split_usa_la_resolucion_que_se_le_pide(tmp_path):
    """Evaluar a 224 un modelo entrenado a 288 mediría otra cosa: el modelo
    recibiría un encuadre que nunca vio."""
    import csv as _csv
    from pathlib import Path

    import numpy as np
    import torch
    from PIL import Image

    from pipeline.etiquetas import EspacioEtiquetas
    from pipeline.evaluar import evaluar_split

    espacio = EspacioEtiquetas(ordenes=("A",), familias=("X",), matriz=((True,),))
    Image.fromarray(np.zeros((400, 400, 3), dtype=np.uint8)).save(tmp_path / "a.jpg")
    filas = [{"archivo": "a.jpg", "orden": "A", "familia": "X"}]

    vistos = []

    class ModeloEspia(torch.nn.Module):
        def forward(self, x):
            vistos.append(tuple(x.shape[-2:]))
            return torch.zeros(len(x), 1), torch.zeros(len(x), 1)

    evaluar_split(ModeloEspia(), filas, tmp_path, espacio, "cpu", lado=288)
    assert vistos == [(288, 288)]
