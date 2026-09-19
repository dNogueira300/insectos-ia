from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch

from pipeline.exportar import exportar_onnx, verificar_paridad
from pipeline.modelo import ModeloJerarquico


def modelo_pequeno():
    return ModeloJerarquico(3, 5, backbone="resnet10t", preentrenado=False)


def test_exportar_crea_el_archivo(tmp_path: Path):
    ruta = tmp_path / "m.onnx"
    exportar_onnx(modelo_pequeno(), ruta)
    assert ruta.exists() and ruta.stat().st_size > 0


def test_el_onnx_declara_dos_salidas(tmp_path: Path):
    ruta = tmp_path / "m.onnx"
    exportar_onnx(modelo_pequeno(), ruta)
    sesion = ort.InferenceSession(str(ruta), providers=["CPUExecutionProvider"])
    nombres = [s.name for s in sesion.get_outputs()]
    assert nombres == ["logits_orden", "logits_familia"]


def test_el_onnx_acepta_lotes_de_cualquier_tamano(tmp_path: Path):
    ruta = tmp_path / "m.onnx"
    exportar_onnx(modelo_pequeno(), ruta)
    sesion = ort.InferenceSession(str(ruta), providers=["CPUExecutionProvider"])
    for n in (1, 4):
        salidas = sesion.run(None, {"imagen": np.random.randn(n, 3, 224, 224).astype(np.float32)})
        assert salidas[0].shape == (n, 3)
        assert salidas[1].shape == (n, 5)


def test_paridad_entre_torch_y_onnx(tmp_path: Path):
    modelo = modelo_pequeno()
    ruta = tmp_path / "m.onnx"
    exportar_onnx(modelo, ruta)
    resultado = verificar_paridad(modelo, ruta)
    assert resultado["coincide"] is True
    assert resultado["diferencia_maxima"] < 1e-4


def test_paridad_detecta_un_modelo_distinto(tmp_path: Path):
    ruta = tmp_path / "m.onnx"
    exportar_onnx(modelo_pequeno(), ruta)
    otro = modelo_pequeno()  # otra inicialización aleatoria
    resultado = verificar_paridad(otro, ruta)
    assert resultado["coincide"] is False


def test_exportar_deja_el_modelo_en_modo_evaluacion(tmp_path: Path):
    modelo = modelo_pequeno()
    modelo.train()
    exportar_onnx(modelo, tmp_path / "m.onnx")
    assert modelo.training is False
