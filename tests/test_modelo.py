import torch

from pipeline.etiquetas import SIN_FAMILIA_IDX
from pipeline.modelo import ModeloJerarquico, PerdidaCombinada


def modelo_pequeno(n_ordenes=3, n_familias=5):
    """Backbone diminuto y sin pesos preentrenados: las pruebas no bajan nada."""
    return ModeloJerarquico(
        n_ordenes, n_familias, backbone="resnet10t", preentrenado=False
    )


def test_forward_devuelve_dos_salidas_con_la_forma_correcta():
    modelo = modelo_pequeno()
    salida_orden, salida_familia = modelo(torch.randn(2, 3, 224, 224))
    assert salida_orden.shape == (2, 3)
    assert salida_familia.shape == (2, 5)


def test_las_dos_cabezas_comparten_el_backbone():
    modelo = modelo_pequeno()
    nombres = {n for n, _ in modelo.named_parameters()}
    assert any(n.startswith("cabeza_orden") for n in nombres)
    assert any(n.startswith("cabeza_familia") for n in nombres)
    assert any(n.startswith("backbone") for n in nombres)


def test_congelar_backbone_deja_las_cabezas_entrenables():
    modelo = modelo_pequeno()
    modelo.congelar_backbone()
    assert all(not p.requires_grad for p in modelo.backbone.parameters())
    assert all(p.requires_grad for p in modelo.cabeza_orden.parameters())
    assert all(p.requires_grad for p in modelo.cabeza_familia.parameters())


def test_descongelar_backbone_lo_reactiva():
    modelo = modelo_pequeno()
    modelo.congelar_backbone()
    modelo.descongelar_backbone()
    assert all(p.requires_grad for p in modelo.backbone.parameters())


def test_perdida_devuelve_total_orden_y_familia():
    perdida = PerdidaCombinada()
    total, de_orden, de_familia = perdida(
        torch.randn(4, 3), torch.randn(4, 5), torch.tensor([0, 1, 2, 0]), torch.tensor([1, 2, 3, 4])
    )
    assert total.ndim == 0
    assert torch.allclose(total, de_orden + de_familia)


def test_lambda_pondera_la_cabeza_de_familia():
    logits_orden, logits_familia = torch.randn(4, 3), torch.randn(4, 5)
    y_orden, y_familia = torch.tensor([0, 1, 2, 0]), torch.tensor([1, 2, 3, 4])
    _, _, f1 = PerdidaCombinada(lambda_familia=1.0)(logits_orden, logits_familia, y_orden, y_familia)
    total2, o2, f2 = PerdidaCombinada(lambda_familia=0.5)(
        logits_orden, logits_familia, y_orden, y_familia
    )
    assert torch.allclose(f2, f1 * 0.5)
    assert torch.allclose(total2, o2 + f2)


def test_familia_ignorada_no_aporta_perdida():
    logits_orden, logits_familia = torch.randn(2, 3), torch.randn(2, 5)
    y_orden = torch.tensor([0, 1])
    todas_ignoradas = torch.tensor([SIN_FAMILIA_IDX, SIN_FAMILIA_IDX])
    _, _, de_familia = PerdidaCombinada()(logits_orden, logits_familia, y_orden, todas_ignoradas)
    assert torch.allclose(de_familia, torch.tensor(0.0))


def test_lote_mixto_usa_solo_las_familias_conocidas():
    torch.manual_seed(0)
    logits_orden, logits_familia = torch.randn(2, 3), torch.randn(2, 5)
    y_orden = torch.tensor([0, 1])
    perdida = PerdidaCombinada()
    _, _, mixto = perdida(logits_orden, logits_familia, y_orden, torch.tensor([2, SIN_FAMILIA_IDX]))
    _, _, solo_uno = perdida(
        logits_orden[:1], logits_familia[:1], y_orden[:1], torch.tensor([2])
    )
    assert torch.allclose(mixto, solo_uno)


def test_pesos_de_clase_cambian_la_perdida():
    torch.manual_seed(0)
    logits_orden, logits_familia = torch.randn(4, 3), torch.randn(4, 5)
    y_orden, y_familia = torch.tensor([0, 1, 2, 0]), torch.tensor([0, 0, 0, 4])
    sin_pesos = PerdidaCombinada()(logits_orden, logits_familia, y_orden, y_familia)[2]
    con_pesos = PerdidaCombinada(pesos_familia=torch.tensor([0.2, 1.0, 1.0, 1.0, 5.0]))(
        logits_orden, logits_familia, y_orden, y_familia
    )[2]
    assert not torch.allclose(sin_pesos, con_pesos)


def test_el_gradiente_llega_al_backbone():
    modelo = modelo_pequeno()
    salida_orden, salida_familia = modelo(torch.randn(2, 3, 224, 224))
    total, _, _ = PerdidaCombinada()(
        salida_orden, salida_familia, torch.tensor([0, 1]), torch.tensor([1, 2])
    )
    total.backward()
    primer_parametro = next(modelo.backbone.parameters())
    assert primer_parametro.grad is not None
