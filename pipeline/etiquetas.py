"""Espacio de etiquetas del modelo y matriz de pertenencia familia→orden.

Las familias se derivan de los datos de entrenamiento, no de la ontología:
tras la regla de admisión existen clases `Otros_<Orden>` que la ontología no
declara, y familias declaradas que se quedaron sin imágenes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pipeline.ontologia import PREFIJO_OTROS, Ontologia

SIN_FAMILIA_IDX = -1  # torch lo interpreta como "ignorar" en la pérdida


@dataclass(frozen=True)
class EspacioEtiquetas:
    ordenes: tuple[str, ...]
    familias: tuple[str, ...]
    matriz: tuple[tuple[bool, ...], ...]  # [familia][orden]

    def indice_orden(self, nombre: str) -> int:
        return self.ordenes.index(nombre)

    def indice_familia(self, nombre: str) -> int:
        if not nombre:
            return SIN_FAMILIA_IDX
        return self.familias.index(nombre)

    def guardar(self, ruta: Path) -> None:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            json.dumps(
                {
                    "ordenes": list(self.ordenes),
                    "familias": list(self.familias),
                    "matriz": [list(r) for r in self.matriz],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


def _orden_de(familia: str, onto: Ontologia) -> str:
    """Resuelve el orden de una familia, incluidas las clases `Otros_<Orden>`."""
    if familia.startswith(PREFIJO_OTROS):
        return familia[len(PREFIJO_OTROS) :]
    return onto.orden_de_familia(familia)


def construir_espacio(filas_train: list[dict], onto: Ontologia) -> EspacioEtiquetas:
    """Construye el espacio de etiquetas a partir de las filas de entrenamiento."""
    ordenes = tuple(onto.nombres_ordenes())

    for fila in filas_train:
        if fila["orden"] not in ordenes:
            raise KeyError(f"orden fuera de la ontología: {fila['orden']}")

    familias = tuple(sorted({f["familia"] for f in filas_train if f["familia"]}))

    matriz = []
    for familia in familias:
        try:
            propietario = _orden_de(familia, onto)
        except Exception as error:
            raise KeyError(f"familia sin orden resoluble: {familia}") from error
        if propietario not in ordenes:
            raise KeyError(f"familia {familia} apunta a un orden inexistente: {propietario}")
        matriz.append(tuple(propietario == o for o in ordenes))

    return EspacioEtiquetas(ordenes=ordenes, familias=familias, matriz=tuple(matriz))


def cargar_espacio(ruta: Path) -> EspacioEtiquetas:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return EspacioEtiquetas(
        ordenes=tuple(datos["ordenes"]),
        familias=tuple(datos["familias"]),
        matriz=tuple(tuple(bool(v) for v in r) for r in datos["matriz"]),
    )
