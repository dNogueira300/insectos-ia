"""Fixtures compartidas por todas las pruebas."""
from pathlib import Path

import pytest

YAML_MINIMO = """
version: 1
minimos:
  familia_train: 150
  familia_test: 30
ordenes:
  - nombre: Coleoptera
    inat_taxon_id: 47208
    nombre_comun: escarabajos
    familias:
      - nombre: Curculionidae
        inat_taxon_id: 62956
      - nombre: Chrysomelidae
        inat_taxon_id: 50340
  - nombre: Odonata
    inat_taxon_id: 47792
    nombre_comun: libelulas
    familias:
      - nombre: Libellulidae
        inat_taxon_id: 49279
"""


@pytest.fixture
def ruta_ontologia(tmp_path: Path) -> Path:
    """Escribe una ontología válida mínima y devuelve su ruta."""
    ruta = tmp_path / "clases.yaml"
    ruta.write_text(YAML_MINIMO, encoding="utf-8")
    return ruta
