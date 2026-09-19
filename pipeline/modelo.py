"""Arquitectura multi-tarea: un backbone, dos cabezas.

La cabeza de orden entrena con muchas más imágenes que la de familia y actúa
como regularizador de la representación compartida. Las imágenes sin familia
conocida solo aportan pérdida a la cabeza de orden.
"""
from __future__ import annotations

import timm
import torch
from torch import nn

from pipeline.etiquetas import SIN_FAMILIA_IDX

BACKBONE_POR_DEFECTO = "efficientnet_b0"


class ModeloJerarquico(nn.Module):
    """Devuelve logits crudos de orden y de familia, sin enmascarar.

    El enmascaramiento jerárquico es lógica de aplicación (`pipeline.inferencia`)
    y no entra al grafo: así el mismo ONNX sirve para evaluar ambas cabezas por
    separado y para servir predicciones enmascaradas.
    """

    def __init__(
        self,
        n_ordenes: int,
        n_familias: int,
        backbone: str = BACKBONE_POR_DEFECTO,
        preentrenado: bool = True,
        abandono: float = 0.2,
    ) -> None:
        super().__init__()
        self.backbone = timm.create_model(backbone, pretrained=preentrenado, num_classes=0)
        rasgos = self.backbone.num_features
        self.abandono = nn.Dropout(abandono)
        self.cabeza_orden = nn.Linear(rasgos, n_ordenes)
        self.cabeza_familia = nn.Linear(rasgos, n_familias)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        rasgos = self.abandono(self.backbone(x))
        return self.cabeza_orden(rasgos), self.cabeza_familia(rasgos)

    def congelar_backbone(self) -> None:
        for parametro in self.backbone.parameters():
            parametro.requires_grad = False

    def descongelar_backbone(self) -> None:
        for parametro in self.backbone.parameters():
            parametro.requires_grad = True


class PerdidaCombinada(nn.Module):
    """`L = L_orden + lambda * L_familia`, ignorando familias desconocidas."""

    def __init__(
        self, pesos_familia: torch.Tensor | None = None, lambda_familia: float = 1.0
    ) -> None:
        super().__init__()
        self.lambda_familia = lambda_familia
        self.perdida_orden = nn.CrossEntropyLoss()
        self.perdida_familia = nn.CrossEntropyLoss(
            weight=pesos_familia, ignore_index=SIN_FAMILIA_IDX
        )

    def forward(
        self,
        logits_orden: torch.Tensor,
        logits_familia: torch.Tensor,
        y_orden: torch.Tensor,
        y_familia: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        de_orden = self.perdida_orden(logits_orden, y_orden)

        # Si el lote entero viene sin familia, CrossEntropyLoss devuelve NaN.
        if (y_familia != SIN_FAMILIA_IDX).any():
            de_familia = self.perdida_familia(logits_familia, y_familia) * self.lambda_familia
        else:
            de_familia = torch.zeros((), device=logits_orden.device, dtype=logits_orden.dtype)

        return de_orden + de_familia, de_orden, de_familia
