import json
from pathlib import Path

import pytest

from pipeline.corrida import ErrorCorridaIncompleta, config_de_corrida, opcion_de_corrida


def _config(tmp_path: Path, **datos) -> Path:
    pesos = tmp_path / "mejor.pth"
    pesos.write_bytes(b"")
    (tmp_path / "config.json").write_text(json.dumps(datos), encoding="utf-8")
    return pesos


def test_lee_la_config_que_esta_junto_a_los_pesos(tmp_path: Path):
    pesos = _config(tmp_path, lado=288, backbone="efficientnet_b2")
    assert config_de_corrida(pesos) == {"lado": 288, "backbone": "efficientnet_b2"}


def test_sin_config_devuelve_vacio(tmp_path: Path):
    pesos = tmp_path / "mejor.pth"
    pesos.write_bytes(b"")
    assert config_de_corrida(pesos) == {}


def test_la_corrida_manda_sobre_el_valor_por_defecto(tmp_path: Path):
    """Entrenar a 288 y exportar a 224 daría un modelo que en producción recibe
    imágenes distintas de las que aprendió, sin ningún aviso."""
    pesos = _config(tmp_path, lado=288)
    assert opcion_de_corrida(pesos, "lado", pedido=None, defecto=224) == 288


def test_lo_pedido_a_mano_manda_sobre_la_corrida(tmp_path: Path):
    pesos = _config(tmp_path, lado=288)
    assert opcion_de_corrida(pesos, "lado", pedido=160, defecto=224) == 160


def test_sin_corrida_ni_peticion_queda_el_defecto(tmp_path: Path):
    pesos = tmp_path / "mejor.pth"
    pesos.write_bytes(b"")
    assert opcion_de_corrida(pesos, "lado", pedido=None, defecto=224) == 224


def test_una_config_ilegible_es_un_error_y_no_un_silencio(tmp_path: Path):
    pesos = tmp_path / "mejor.pth"
    pesos.write_bytes(b"")
    (tmp_path / "config.json").write_text("{esto no es json", encoding="utf-8")
    with pytest.raises(ErrorCorridaIncompleta, match="config.json"):
        config_de_corrida(pesos)
