"""Reanudación del entrenamiento entre sesiones de Colab (adenda del Plan 02).

Colab gratuito corta sesiones sin aviso, y el equipo alterna dos cuentas sobre
la misma carpeta de Drive. Estas pruebas fijan que una corrida cortada y
reanudada es indistinguible de una corrida sin cortes, y que el checkpoint
nunca queda corrupto ni se pisa por error.
"""
import csv
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from pipeline import entrenar as mod
from pipeline.entrenar import ErrorCorrida, entrenar


class ModeloDiminuto(torch.nn.Module):
    """Mismo contrato que ModeloJerarquico, sin timm ni pesos preentrenados."""

    def __init__(self, n_ordenes: int, n_familias: int):
        super().__init__()
        self.backbone = torch.nn.Sequential(
            torch.nn.AdaptiveAvgPool2d(4), torch.nn.Flatten(), torch.nn.Linear(48, 8)
        )
        self.abandono = torch.nn.Dropout(0.2)
        self.cabeza_orden = torch.nn.Linear(8, n_ordenes)
        self.cabeza_familia = torch.nn.Linear(8, n_familias)

    def forward(self, x):
        rasgos = self.abandono(self.backbone(x))
        return self.cabeza_orden(rasgos), self.cabeza_familia(rasgos)

    def congelar_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = False

    def descongelar_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = True


def _fabricar(n_ordenes, n_familias, backbone):
    return ModeloDiminuto(n_ordenes, n_familias)


CLASES = [("Coleoptera", "Curculionidae"), ("Coleoptera", "Chrysomelidae"), ("Odonata", "Libellulidae")]


def _preparar(tmp_path: Path) -> dict:
    imagenes = tmp_path / "curado"
    splits = tmp_path / "splits"
    splits.mkdir(parents=True)
    rng = np.random.default_rng(0)
    for split, n in (("train", 4), ("val", 2)):
        filas = []
        for orden, familia in CLASES:
            for i in range(n):
                archivo = f"{orden}/{familia}/{split}{i}.jpg"
                ruta = imagenes / archivo
                ruta.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(rng.integers(0, 255, (40, 40, 3), dtype=np.uint8)).save(ruta)
                filas.append({"archivo": archivo, "orden": orden, "familia": familia})
        with (splits / f"{split}.csv").open("w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=["archivo", "orden", "familia"])
            escritor.writeheader()
            escritor.writerows(filas)
    return {"raiz_imagenes": imagenes, "ruta_splits": splits}


@pytest.fixture
def base(tmp_path: Path, ruta_ontologia: Path) -> dict:
    return dict(
        ruta_ontologia=ruta_ontologia,
        epocas=3,
        lote=4,
        trabajadores=0,
        fabricar_modelo=_fabricar,
        **_preparar(tmp_path),
    )


class Corte(Exception):
    """Simula que Colab mata la sesión justo después de guardar una época."""


def _cortar_tras(epoca_de_corte: int):
    def _al_terminar(epoca: int) -> None:
        if epoca == epoca_de_corte:
            raise Corte

    return _al_terminar


def test_cortar_y_reanudar_da_el_mismo_historial_que_sin_cortes(tmp_path: Path, base: dict):
    """El corte cae en la frontera congelado/descongelado (época 2): la
    reanudación debe rearmar el optimizador de la fase correcta."""
    seguida = entrenar(destino=tmp_path / "seguida", **base)

    with pytest.raises(Corte):
        entrenar(destino=tmp_path / "cortada", al_terminar_epoca=_cortar_tras(1), **base)
    reanudada = entrenar(destino=tmp_path / "cortada", reanudar=True, **base)

    assert len(reanudada["historial"]) == 3
    for a, b in zip(seguida["historial"], reanudada["historial"], strict=True):
        assert a.keys() == b.keys()
        for clave in a:
            assert a[clave] == pytest.approx(b[clave], abs=1e-6), clave


def test_el_checkpoint_de_cada_epoca_es_atomico(tmp_path: Path, base: dict, monkeypatch):
    """Si la sesión muere mientras escribe `ultimo.pth`, el anterior sigue sano."""
    destino = tmp_path / "corrida"
    with pytest.raises(Corte):
        entrenar(destino=destino, al_terminar_epoca=_cortar_tras(0), **base)
    antes = torch.load(destino / "ultimo.pth", weights_only=False)["epoca"]

    guardar_original = torch.save

    def guardar_que_muere(objeto, ruta, *args, **kwargs):
        guardar_original(objeto, ruta, *args, **kwargs)
        if Path(ruta).name.startswith("ultimo"):
            raise Corte  # muere tras escribir el temporal, antes de reemplazar

    monkeypatch.setattr(torch, "save", guardar_que_muere)
    with pytest.raises(Corte):
        entrenar(destino=destino, reanudar=True, **base)
    monkeypatch.setattr(torch, "save", guardar_original)

    assert torch.load(destino / "ultimo.pth", weights_only=False)["epoca"] == antes


def test_reanudar_con_otra_configuracion_falla(tmp_path: Path, base: dict):
    destino = tmp_path / "corrida"
    with pytest.raises(Corte):
        entrenar(destino=destino, al_terminar_epoca=_cortar_tras(0), **base)
    with pytest.raises(ErrorCorrida, match="lote"):
        entrenar(destino=destino, reanudar=True, **{**base, "lote": 2})


def test_sin_reanudar_no_pisa_una_corrida_existente(tmp_path: Path, base: dict):
    """En una carpeta de Drive compartida, pisar la corrida del compañero por
    olvidar --reanudar borraría horas de GPU."""
    destino = tmp_path / "corrida"
    with pytest.raises(Corte):
        entrenar(destino=destino, al_terminar_epoca=_cortar_tras(0), **base)
    with pytest.raises(ErrorCorrida, match="--reanudar"):
        entrenar(destino=destino, **base)


def test_reanudar_una_corrida_terminada_no_vuelve_a_entrenar(tmp_path: Path, base: dict):
    destino = tmp_path / "corrida"
    primero = entrenar(destino=destino, **base)
    epocas_vistas = []
    segundo = entrenar(
        destino=destino, reanudar=True, al_terminar_epoca=epocas_vistas.append, **base
    )
    assert epocas_vistas == []
    assert segundo["historial"] == primero["historial"]


def test_reanudar_sin_checkpoint_empieza_de_cero(tmp_path: Path, base: dict):
    """El cuaderno de Colab siempre pasa --reanudar: la primera vez no hay nada."""
    epocas_vistas = []
    entrenar(destino=tmp_path / "nueva", reanudar=True, al_terminar_epoca=epocas_vistas.append, **base)
    assert epocas_vistas == [0, 1, 2]


def test_se_guardan_mejor_pth_y_metricas(tmp_path: Path, base: dict):
    destino = tmp_path / "corrida"
    entrenar(destino=destino, **base)
    assert (destino / "mejor.pth").is_file()
    assert (destino / "metricas.json").is_file()
    assert (destino / "etiquetas.json").is_file()
    assert (destino / "config.json").is_file()


def test_la_linea_de_comandos_acepta_reanudar():
    assert "--reanudar" in mod.construir_parser().format_help()
