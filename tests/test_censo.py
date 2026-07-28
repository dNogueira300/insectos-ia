from pathlib import Path

from pipeline import censo
from pipeline.censo import SIN_DATO, VEREDICTO_ERROR, FilaCenso, a_markdown, censar
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


class SesionQueFalla:
    """Como SesionContadora, pero un taxon_id concreto revienta la llamada.

    Simula un fallo de red (timeout, 5xx, conexión caída) al consultar una
    sola clase, para probar que el resto del censo sobrevive.
    """

    def __init__(self, conteos, taxon_que_falla, clave="total_results"):
        self.conteos = conteos
        self.taxon_que_falla = taxon_que_falla
        self.clave = clave

    def get(self, url, params=None, timeout=None):
        taxon = params.get("taxon_id") or params.get("taxonKey")
        if taxon == self.taxon_que_falla:
            raise ConnectionError("fallo de red simulado")
        total = self.conteos.get(taxon, 0)
        clave = self.clave
        return type(
            "R", (), {"raise_for_status": lambda s: None, "json": lambda s: {clave: total}}
        )()


def test_censa_ordenes_y_familias(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    inat = SesionContadora({47208: 50000, 47792: 30000, 62956: 900, 50340: 400, 49279: 5000})
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
    niveles = [f.nivel for f in filas]
    assert niveles.count("orden") == 2
    assert niveles.count("familia") == 3


def test_veredicto_suficiente_cuando_supera_el_objetivo(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    # objetivo = (150 + 30) * 1.5 = 270
    inat = SesionContadora({47208: 9999, 47792: 9999, 62956: 900, 50340: 100, 49279: 5000})
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
    por_nombre = {f.nombre: f for f in filas}
    assert por_nombre["Curculionidae"].veredicto == "suficiente"
    assert por_nombre["Chrysomelidae"].veredicto == "insuficiente"


def test_objetivo_se_calcula_desde_los_minimos_de_la_ontologia(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    inat = SesionContadora({})
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
    familia = next(f for f in filas if f.nivel == "familia")
    assert familia.objetivo == 270


def test_censo_con_lugar_consulta_dos_veces_por_taxon(ruta_ontologia: Path):
    onto = cargar_ontologia(ruta_ontologia)
    inat = SesionContadora({47208: 1000, 47792: 1000, 62956: 1000, 50340: 1000, 49279: 1000})
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=7041, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
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


def test_fallo_de_red_en_una_clase_no_aborta_el_censo(ruta_ontologia: Path):
    """Hallazgo 1: una clase que falla no debe tumbar el censo completo."""
    onto = cargar_ontologia(ruta_ontologia)
    # 62956 = Curculionidae: su consulta revienta; las otras cuatro clases
    # (2 órdenes + Chrysomelidae + Libellulidae) deben censarse con normalidad.
    inat = SesionQueFalla(
        {47208: 50000, 47792: 30000, 50340: 400, 49279: 5000}, taxon_que_falla=62956
    )
    gbif = SesionContadora({}, clave="count")
    filas = censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat, sesion_gbif=gbif, pausa_segundos=0
    )
    assert len(filas) == 5  # ninguna clase se pierde por el fallo de una sola

    por_nombre = {f.nombre: f for f in filas}
    fallida = por_nombre["Curculionidae"]
    assert fallida.veredicto == VEREDICTO_ERROR
    assert fallida.veredicto != "insuficiente"  # no confundir "no se sabe" con "no alcanza"
    assert fallida.inat_global == SIN_DATO

    # las demás clases se censaron con normalidad, sin contagiarse del fallo
    assert por_nombre["Chrysomelidae"].veredicto in ("suficiente", "insuficiente")
    assert por_nombre["Chrysomelidae"].inat_global == 400


def test_pausa_es_parametrizable_y_no_duerme_con_cero(ruta_ontologia: Path, monkeypatch):
    """Hallazgo 2: la pausa entre consultas se reutiliza de pipeline.inat y
    puede desactivarse para que las pruebas sean instantáneas."""
    onto = cargar_ontologia(ruta_ontologia)
    inat_ses = SesionContadora({47208: 100, 47792: 100, 62956: 100, 50340: 100, 49279: 100})
    gbif_ses = SesionContadora({}, clave="count")
    pausas: list[float] = []
    monkeypatch.setattr(censo.time, "sleep", lambda segundos: pausas.append(segundos))

    censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat_ses, sesion_gbif=gbif_ses,
        pausa_segundos=0,
    )
    assert pausas == []  # con 0 no debe invocarse time.sleep en absoluto

    censar(
        onto, lugar_id=None, pais_gbif=None, sesion_inat=inat_ses, sesion_gbif=gbif_ses,
        pausa_segundos=2,
    )
    assert pausas  # con un valor positivo sí se pausa entre clases
    assert all(p == 2 for p in pausas)


def test_markdown_declara_los_supuestos_de_gbif_veredicto_y_adultos(ruta_ontologia: Path):
    """Hallazgo 3: el reporte debe advertir sobre N/D, el alcance del
    veredicto y el filtro de adultos, para no inducir a error en la reunión
    de decisión con la Facultad."""
    onto = cargar_ontologia(ruta_ontologia)
    filas = [
        FilaCenso("orden", "Coleoptera", "Coleoptera", 5000, 500, 900, 90, 270, "suficiente"),
        FilaCenso(
            "familia", "Coleoptera", "Curculionidae", 100, 10, SIN_DATO, SIN_DATO, 270,
            "insuficiente",
        ),
        FilaCenso(
            "familia", "Odonata", "Libellulidae", SIN_DATO, SIN_DATO, SIN_DATO, SIN_DATO, 270,
            VEREDICTO_ERROR,
        ),
    ]
    texto = a_markdown(filas, onto)

    # N/D en vez de -1 para lo no consultado (GBIF de familia y filas con error)
    assert "N/D" in texto
    assert "-1" not in texto

    # el filtro de adultos queda declarado
    assert "adultos" in texto.lower()

    # el reporte aclara que el veredicto no pondera la columna regional
    assert "iNat global" in texto
    assert "amazónic" in texto.lower() or "regional" in texto.lower()

    # error_consulta queda explicado y no se confunde con insuficiente
    assert VEREDICTO_ERROR in texto
    assert "reintentar" in texto.lower()
