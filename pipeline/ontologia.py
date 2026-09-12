"""Carga y validación de la ontología de clases.

Es la única fuente de verdad sobre qué órdenes y familias existen en el
sistema. Ningún otro módulo debe escribir un nombre taxonómico literal.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class ErrorOntologia(Exception):
    """La ontología es inválida, está incompleta o es inconsistente."""


# Prefijo de las clases que agrupan familias por debajo del umbral de admisión.
# Vive aquí, y no en splits.py, porque es una convención de nombres de clase:
# el backend necesita interpretarla sin importar el pipeline de datos.
PREFIJO_OTROS = "Otros_"


@dataclass(frozen=True)
class Familia:
    nombre: str
    inat_taxon_id: int
    nombre_comun: str = ""
    importancia: str = ""


@dataclass(frozen=True)
class Orden:
    nombre: str
    inat_taxon_id: int
    nombre_comun: str = ""
    gbif_key: int | None = None
    familias: tuple[Familia, ...] = ()
    # Filtro "Life Stage = Adult" de iNaturalist. Se desactiva en órdenes
    # cuyas castas o estados inmaduros son lo que se ve en campo (termitas).
    solo_adultos: bool = True
    # Subtaxones que no deben bajar con este orden porque el sistema los trata
    # como un orden propio (p. ej. las termitas dentro de Blattodea). Sin
    # esto, la misma foto quedaría con dos etiquetas de orden. Las familias
    # del orden heredan la exclusión y el filtro de adultos.
    excluir_taxon_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class Ontologia:
    version: int
    minimo_familia_train: int
    minimo_familia_test: int
    ordenes: tuple[Orden, ...]

    def nombres_ordenes(self) -> list[str]:
        """Nombres de orden en alfabético: fija los índices del modelo."""
        return sorted(o.nombre for o in self.ordenes)

    def nombres_familias(self) -> list[str]:
        """Nombres de familia en alfabético: fija los índices del modelo."""
        return sorted(f.nombre for o in self.ordenes for f in o.familias)

    def orden_de_familia(self, familia: str) -> str:
        for orden in self.ordenes:
            for fam in orden.familias:
                if fam.nombre == familia:
                    return orden.nombre
        raise ErrorOntologia(f"familia desconocida: {familia}")

    def matriz_pertenencia(self) -> list[list[bool]]:
        """Matriz [familia][orden] usada para enmascarar en inferencia."""
        ordenes = self.nombres_ordenes()
        return [
            [self.orden_de_familia(fam) == orden for orden in ordenes]
            for fam in self.nombres_familias()
        ]


def _entero_obligatorio(dic: dict, clave: str, contexto: str) -> int:
    valor = dic.get(clave)
    if not isinstance(valor, int):
        raise ErrorOntologia(f"{contexto}: falta '{clave}' entero")
    return valor


def _opciones_de_orden(bruto: dict, nombre: str) -> tuple[bool, tuple[int, ...]]:
    solo_adultos = bruto.get("solo_adultos", True)
    if not isinstance(solo_adultos, bool):
        raise ErrorOntologia(f"orden {nombre}: 'solo_adultos' debe ser true o false")

    excluir = bruto.get("excluir_taxon_ids", [])
    # bool es subclase de int: un `[true]` no debe pasar por un identificador.
    if not isinstance(excluir, list) or not all(
        isinstance(t, int) and not isinstance(t, bool) for t in excluir
    ):
        raise ErrorOntologia(f"orden {nombre}: 'excluir_taxon_ids' debe ser una lista de enteros")
    if bruto.get("inat_taxon_id") in excluir:
        raise ErrorOntologia(f"orden {nombre}: 'excluir_taxon_ids' contiene su propio inat_taxon_id")
    return solo_adultos, tuple(excluir)


def cargar_ontologia(ruta: Path) -> Ontologia:
    """Lee el YAML de clases y devuelve una Ontologia validada."""
    datos = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))
    if not isinstance(datos, dict):
        raise ErrorOntologia("el archivo no contiene un mapa YAML")

    minimos = datos.get("minimos") or {}
    ordenes: list[Orden] = []
    vistos_orden: set[str] = set()
    vistas_familia: dict[str, str] = {}

    for bruto in datos.get("ordenes") or []:
        nombre = bruto.get("nombre")
        if not nombre:
            raise ErrorOntologia("hay un orden sin 'nombre'")
        if nombre in vistos_orden:
            raise ErrorOntologia(f"orden repetido: {nombre}")
        vistos_orden.add(nombre)

        familias: list[Familia] = []
        for fam in bruto.get("familias") or []:
            fnombre = fam.get("nombre")
            if not fnombre:
                raise ErrorOntologia(f"orden {nombre}: hay una familia sin 'nombre'")
            if fnombre in vistas_familia:
                raise ErrorOntologia(
                    f"familia {fnombre} declarada en {vistas_familia[fnombre]} y en {nombre}"
                )
            vistas_familia[fnombre] = nombre
            familias.append(
                Familia(
                    nombre=fnombre,
                    inat_taxon_id=_entero_obligatorio(fam, "inat_taxon_id", f"familia {fnombre}"),
                    nombre_comun=fam.get("nombre_comun", ""),
                    importancia=fam.get("importancia", ""),
                )
            )

        solo_adultos, excluir = _opciones_de_orden(bruto, nombre)
        ordenes.append(
            Orden(
                nombre=nombre,
                inat_taxon_id=_entero_obligatorio(bruto, "inat_taxon_id", f"orden {nombre}"),
                nombre_comun=bruto.get("nombre_comun", ""),
                gbif_key=bruto.get("gbif_key"),
                familias=tuple(familias),
                solo_adultos=solo_adultos,
                excluir_taxon_ids=excluir,
            )
        )

    if not ordenes:
        raise ErrorOntologia("la ontología no declara ningún orden")

    return Ontologia(
        version=_entero_obligatorio(datos, "version", "raíz"),
        minimo_familia_train=_entero_obligatorio(minimos, "familia_train", "minimos"),
        minimo_familia_test=_entero_obligatorio(minimos, "familia_test", "minimos"),
        ordenes=tuple(ordenes),
    )
