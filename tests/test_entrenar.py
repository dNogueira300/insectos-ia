import torch

from pipeline.entrenar import SEMILLA, epoca_entrenamiento, evaluar_cargador, fijar_semilla
from pipeline.etiquetas import SIN_FAMILIA_IDX, EspacioEtiquetas
from pipeline.modelo import PerdidaCombinada

ESPACIO = EspacioEtiquetas(
    ordenes=("OrdenA", "OrdenB"),
    familias=("FamA1", "FamB1"),
    matriz=((True, False), (False, True)),
)


class ModeloFalso(torch.nn.Module):
    """Lineal sobre la media de píxeles: entrena en milisegundos."""

    def __init__(self):
        super().__init__()
        self.cabeza_orden = torch.nn.Linear(3, 2)
        self.cabeza_familia = torch.nn.Linear(3, 2)

    def forward(self, x):
        rasgos = x.mean(dim=(2, 3))
        return self.cabeza_orden(rasgos), self.cabeza_familia(rasgos)


def lote(n=4, familia_valida=True):
    imagenes = torch.randn(n, 3, 8, 8)
    ordenes = torch.tensor([i % 2 for i in range(n)])
    familias = ordenes.clone() if familia_valida else torch.full((n,), SIN_FAMILIA_IDX)
    return [(imagenes, ordenes, familias)]


def test_fijar_semilla_hace_reproducible_el_azar():
    fijar_semilla(SEMILLA)
    a = torch.randn(3)
    fijar_semilla(SEMILLA)
    assert torch.equal(a, torch.randn(3))


def test_epoca_devuelve_las_tres_perdidas():
    modelo = ModeloFalso()
    resumen = epoca_entrenamiento(
        modelo, lote(), PerdidaCombinada(), torch.optim.SGD(modelo.parameters(), lr=0.1), "cpu"
    )
    assert set(resumen) == {"perdida", "perdida_orden", "perdida_familia"}
    assert all(isinstance(v, float) for v in resumen.values())


def test_una_epoca_cambia_los_pesos():
    modelo = ModeloFalso()
    antes = modelo.cabeza_orden.weight.clone()
    epoca_entrenamiento(
        modelo, lote(), PerdidaCombinada(), torch.optim.SGD(modelo.parameters(), lr=0.5), "cpu"
    )
    assert not torch.equal(antes, modelo.cabeza_orden.weight)


def test_lote_sin_familias_no_rompe_el_entrenamiento():
    modelo = ModeloFalso()
    resumen = epoca_entrenamiento(
        modelo,
        lote(familia_valida=False),
        PerdidaCombinada(),
        torch.optim.SGD(modelo.parameters(), lr=0.1),
        "cpu",
    )
    assert resumen["perdida_familia"] == 0.0
    assert resumen["perdida"] == resumen["perdida_orden"]


def test_evaluar_devuelve_las_metricas_esperadas():
    resumen = evaluar_cargador(ModeloFalso(), lote(n=8), ESPACIO, "cpu")
    esperadas = {
        "macro_f1_orden",
        "macro_f1_familia",
        "exactitud_orden",
        "exactitud_familia",
        "exactitud_jerarquica",
        "top3_familia",
    }
    assert esperadas <= set(resumen)


def test_evaluar_ignora_las_filas_sin_familia_en_metricas_de_familia():
    resumen = evaluar_cargador(ModeloFalso(), lote(n=4, familia_valida=False), ESPACIO, "cpu")
    assert resumen["macro_f1_familia"] == 0.0
    assert resumen["exactitud_orden"] >= 0.0


def test_evaluar_no_deja_el_modelo_en_modo_entrenamiento():
    modelo = ModeloFalso()
    evaluar_cargador(modelo, lote(), ESPACIO, "cpu")
    assert modelo.training is False
