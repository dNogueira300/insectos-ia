from pathlib import Path

from pipeline.censo import FilaCenso, a_markdown, censar
from pipeline.ontologia import cargar_ontologia


class SesionContadora:
    """Devuelve un conteo fijo por taxon_id consultado."""

    def __init__(self, conteos, clave="total_results"):
        self.conteos = conteos
        self.clave = clave
        self.llamadas = []

    def get(self, url, params=None, timeout=None):
        self.llamadas.append(params)
        taxon = params.get("taxon_id") or params.get("taxonKey")
        total = self.conteos.get(taxon, 0)
        if params.get("place_id") or params.get("country"):
            total = total // 10
        clave = self.clave
        return type(
            "R", (), {"raise_for_status": lambda s: None, "json": lambda s: {clave: total}}
        )()


def test_censa_ordenes_y_familias(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    inat = SesionContadora({47208: 50000, 47792: 30000, 62956: 900, 50340: 400, 49279: 5000})
    gbif = SesionContadora({}, clave="count")
    filas = censar(onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif)
    niveles = [f.nivel for f in filas]
    assert niveles.count("orden") == 2
    assert niveles.count("familia") == 3


def test_veredicto_suficiente_cuando_supera_el_objetivo(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    # objetivo = (150 + 30) * 1.5 = 270
    inat = SesionContadora({47208: 9999, 47792: 9999, 62956: 900, 50340: 100, 49279: 5000})
    gbif = SesionContadora({}, clave="count")
    filas = censar(onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif)
    por_nombre = {f.nombre: f for f in filas}
    assert por_nombre["Curculionidae"].veredicto == "suficiente"
    assert por_nombre["Chrysomelidae"].veredicto == "insuficiente"


def test_objetivo_se_calcula_desde_los_minimos_de_la_ontologia(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    inat = SesionContadora({})
    gbif = SesionContadora({}, clave="count")
    filas = censar(onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif)
    familia = next(f for f in filas if f.nivel == "familia")
    assert familia.objetivo == 270


def test_censo_con_lugar_consulta_dos_veces_por_taxon(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    inat = SesionContadora({47208: 1000, 47792: 1000, 62956: 1000, 50340: 1000, 49279: 1000})
    gbif = SesionContadora({}, clave="count")
    filas = censar(onto, lugar_id=7041, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif)
    fila = filas[0]
    assert fila.inat_global == 1000
    assert fila.inat_lugar == 100


def test_markdown_incluye_todas_las_filas_y_el_factor(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    filas = [
        FilaCenso("orden", "Coleoptera", "Coleoptera", 5000, 500, 900, 90, 270, "suficiente"),
        FilaCenso("familia", "Coleoptera", "Curculionidae", 100, 10, 20, 2, 270, "insuficiente"),
    ]
    texto = a_markdown(filas, onto)
    assert "Curculionidae" in texto
    assert "insuficiente" in texto
    assert "1.5" in texto  # el factor de curación debe estar declarado
