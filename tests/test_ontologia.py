from pathlib import Path

import pytest

from pipeline.ontologia import ErrorOntologia, cargar_ontologia


def test_carga_ontologia_valida(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    assert onto.version == 1
    assert onto.minimo_familia_train == 150
    assert onto.minimo_familia_test == 30
    assert len(onto.ordenes) == 2


def test_nombres_en_orden_alfabetico_estable(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    assert onto.nombres_ordenes() == ["Coleoptera", "Odonata"]
    assert onto.nombres_familias() == [
        "Chrysomelidae",
        "Curculionidae",
        "Libellulidae",
    ]


def test_orden_de_familia(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    assert onto.orden_de_familia("Libellulidae") == "Odonata"


def test_orden_de_familia_desconocida_falla(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    with pytest.raises(ErrorOntologia):
        onto.orden_de_familia("Inexistente")


def test_matriz_pertenencia_una_sola_verdad_por_fila(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    matriz = onto.matriz_pertenencia()
    assert len(matriz) == 3          # tres familias
    assert len(matriz[0]) == 2       # dos ordenes
    for fila in matriz:
        assert sum(fila) == 1        # cada familia pertenece a exactamente un orden


def test_familia_repetida_en_dos_ordenes_falla(tmp_path: Path):
    (tmp_path / "c.yaml").write_text(
        """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: A
    inat_taxon_id: 1
    familias: [{nombre: X, inat_taxon_id: 10}]
  - nombre: B
    inat_taxon_id: 2
    familias: [{nombre: X, inat_taxon_id: 11}]
""",
        encoding="utf-8",
    )
    with pytest.raises(ErrorOntologia, match="X"):
        cargar_ontologia(tmp_path / "c.yaml")


def test_orden_sin_taxon_id_falla(tmp_path: Path):
    (tmp_path / "c.yaml").write_text(
        """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: A
    familias: []
""",
        encoding="utf-8",
    )
    with pytest.raises(ErrorOntologia, match="inat_taxon_id"):
        cargar_ontologia(tmp_path / "c.yaml")


def test_archivo_del_proyecto_es_valido():
    """La ontología real del repositorio debe cargar sin errores."""
    onto = cargar_ontologia(Path("ontologia/clases.yaml"))
    assert len(onto.ordenes) >= 1


def test_ningun_modulo_escribe_nombres_de_clase_literales():
    """Los nombres taxonómicos solo pueden vivir en la ontología, no en el código."""
    prohibidos = ("Coleoptera", "Lepidoptera", "Hymenoptera", "Odonata")
    for archivo in Path("pipeline").glob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        for palabra in prohibidos:
            assert palabra not in texto, f"{archivo} contiene el literal {palabra}"
