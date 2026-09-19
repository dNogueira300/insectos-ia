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


def test_paridad_no_da_falsa_alarma_con_logits_grandes(tmp_path: Path):
    """Con pesos entrenados y una entrada de ruido, los logits llegan a ~500 y
    el redondeo normal de float32 acumulado en decenas de capas da diferencias
    absolutas de ~1 aunque el ONNX sea fiel (visto en la prueba de humo del
    2026-09-19, con 100% de coincidencia de clase sobre imágenes reales). La
    paridad debe juzgar lo que usa el sistema: probabilidades y clase elegida."""
    modelo = modelo_pequeno()
    with torch.no_grad():
        modelo.cabeza_orden.weight.mul_(1e5)
        modelo.cabeza_familia.weight.mul_(1e5)
    ruta = tmp_path / "m.onnx"
    exportar_onnx(modelo, ruta)
    resultado = verificar_paridad(modelo, ruta)
    assert resultado["coincide"] is True, resultado


def test_paridad_informa_la_diferencia_de_logits_y_la_clase(tmp_path: Path):
    modelo = modelo_pequeno()
    ruta = tmp_path / "m.onnx"
    exportar_onnx(modelo, ruta)
    resultado = verificar_paridad(modelo, ruta)
    assert resultado["misma_clase"] is True
    assert resultado["diferencia_logits"] < 1e-3


def test_paridad_acepta_una_entrada_de_fotos_reales(tmp_path: Path):
    modelo = modelo_pequeno()
    ruta = tmp_path / "m.onnx"
    exportar_onnx(modelo, ruta)
    resultado = verificar_paridad(modelo, ruta, entrada=torch.zeros(3, 3, 224, 224))
    assert resultado["coincide"] is True


def test_muestra_real_carga_las_fotos_con_la_transformacion_de_evaluacion(tmp_path: Path):
    from PIL import Image

    from pipeline.exportar import muestra_real

    for i in range(5):
        Image.new("RGB", (300, 260), (i * 40, 90, 20)).save(tmp_path / f"{i}.jpg")
    csv = tmp_path / "val.csv"
    csv.write_text("archivo\n" + "".join(f"{i}.jpg\n" for i in range(5)), encoding="utf-8")
    lote = muestra_real(csv, tmp_path, n=3)
    assert lote.shape == (3, 3, 224, 224)
    assert lote.min() < 0  # normalizada como en evaluación
