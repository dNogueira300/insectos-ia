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


YAML_ORDEN_CON_OPCIONES = """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: A
    inat_taxon_id: 1
    excluir_taxon_ids: [2]
    familias: []
  - nombre: B
    inat_taxon_id: 2
    solo_adultos: false
    familias: []
"""


def test_orden_por_defecto_solo_adultos_y_sin_exclusiones(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    for orden in onto.ordenes:
        assert orden.solo_adultos is True
        assert orden.excluir_taxon_ids == ()


def test_orden_declara_exclusiones_y_filtro_de_adultos(tmp_path: Path):
    (tmp_path / "c.yaml").write_text(YAML_ORDEN_CON_OPCIONES, encoding="utf-8")
    a, b = cargar_ontologia(tmp_path / "c.yaml").ordenes
    assert a.excluir_taxon_ids == (2,)
    assert a.solo_adultos is True
    assert b.solo_adultos is False


@pytest.mark.parametrize(
    "linea, clave",
    [
        ("excluir_taxon_ids: 2", "excluir_taxon_ids"),
        ("excluir_taxon_ids: [dos]", "excluir_taxon_ids"),
        ("excluir_taxon_ids: [true]", "excluir_taxon_ids"),
        ("solo_adultos: 'no'", "solo_adultos"),
    ],
)
def test_opciones_de_orden_con_tipo_invalido_fallan(tmp_path: Path, linea: str, clave: str):
    """Un `solo_adultos: 'no'` leído como verdadero bajaría larvas sin avisar."""
    (tmp_path / "c.yaml").write_text(
        f"""
version: 1
minimos: {{familia_train: 10, familia_test: 5}}
ordenes:
  - nombre: A
    inat_taxon_id: 1
    {linea}
    familias: []
""",
        encoding="utf-8",
    )
    with pytest.raises(ErrorOntologia, match=clave):
        cargar_ontologia(tmp_path / "c.yaml")


def test_orden_que_se_excluye_a_si_mismo_falla(tmp_path: Path):
    """Excluir el propio taxón deja la clase vacía: es un error de escritura."""
    (tmp_path / "c.yaml").write_text(
        """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: A
    inat_taxon_id: 1
    excluir_taxon_ids: [1]
    familias: []
""",
        encoding="utf-8",
    )
    with pytest.raises(ErrorOntologia, match="excluir_taxon_ids"):
        cargar_ontologia(tmp_path / "c.yaml")
