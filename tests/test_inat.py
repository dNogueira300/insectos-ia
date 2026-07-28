import pytest

from pipeline.inat import (
    Observacion,
    contar_observaciones,
    iterar_observaciones,
)


class RespuestaFalsa:
    def __init__(self, cuerpo):
        self._cuerpo = cuerpo

    def raise_for_status(self):
        return None

    def json(self):
        return self._cuerpo


class SesionFalsa:
    """Devuelve páginas predefinidas y registra los parámetros recibidos."""

    def __init__(self, paginas):
        self.paginas = list(paginas)
        self.llamadas = []

    def get(self, url, params=None, timeout=None):
        self.llamadas.append(params)
        cuerpo = self.paginas.pop(0) if self.paginas else {"results": []}
        return RespuestaFalsa(cuerpo)


def obs_cruda(oid, con_foto=True, licencia="cc-by"):
    return {
        "id": oid,
        "taxon": {"id": 999, "name": "Especie ejemplo", "rank": "species"},
        "user": {"login": f"usuario{oid % 3}"},
        "location": "-3.75,-73.25",
        "observed_on": "2026-01-15",
        "photos": (
            [
                {
                    "url": "https://inaturalist-open-data.s3.amazonaws.com/photos/1/square.jpg",
                    "license_code": licencia,
                    "attribution": "(c) alguien, algunos derechos reservados",
                }
            ]
            if con_foto
            else []
        ),
    }


def test_contar_pide_per_page_cero():
    sesion = SesionFalsa([{"total_results": 4321, "results": []}])
    total = contar_observaciones(47208, sesion=sesion)
    assert total == 4321
    assert sesion.llamadas[0]["per_page"] == 0
    assert sesion.llamadas[0]["quality_grade"] == "research"


def test_contar_incluye_filtro_de_adultos_por_defecto():
    sesion = SesionFalsa([{"total_results": 10, "results": []}])
    contar_observaciones(47208, sesion=sesion)
    assert sesion.llamadas[0]["term_id"] == 1
    assert sesion.llamadas[0]["term_value_id"] == 2


def test_contar_sin_filtro_de_adultos_omite_los_terminos():
    sesion = SesionFalsa([{"total_results": 10, "results": []}])
    contar_observaciones(47208, solo_adultos=False, sesion=sesion)
    assert "term_id" not in sesion.llamadas[0]


def test_contar_con_lugar_agrega_place_id():
    sesion = SesionFalsa([{"total_results": 10, "results": []}])
    contar_observaciones(47208, lugar_id=7041, sesion=sesion)
    assert sesion.llamadas[0]["place_id"] == 7041


def test_iterar_convierte_la_observacion():
    sesion = SesionFalsa([{"results": [obs_cruda(100)]}])
    obs = list(iterar_observaciones(47208, limite=1, sesion=sesion, pausa=0))
    assert len(obs) == 1
    o = obs[0]
    assert isinstance(o, Observacion)
    assert o.id == 100
    assert o.observador == "usuario1"
    assert o.latitud == pytest.approx(-3.75)
    assert o.longitud == pytest.approx(-73.25)
    assert o.fecha == "2026-01-15"
    assert o.licencia == "cc-by"


def test_iterar_pide_la_foto_en_tamano_medium():
    sesion = SesionFalsa([{"results": [obs_cruda(100)]}])
    o = next(iter(iterar_observaciones(47208, limite=1, sesion=sesion, pausa=0)))
    assert o.foto_url.endswith("medium.jpg")


def test_iterar_respeta_el_limite():
    pagina = {"results": [obs_cruda(i) for i in range(1, 51)]}
    sesion = SesionFalsa([pagina, pagina])
    obs = list(iterar_observaciones(47208, limite=10, sesion=sesion, pausa=0))
    assert len(obs) == 10


def test_iterar_avanza_el_cursor_id_above():
    p1 = {"results": [obs_cruda(i) for i in range(1, 6)]}
    p2 = {"results": [obs_cruda(i) for i in range(6, 11)]}
    sesion = SesionFalsa([p1, p2, {"results": []}])
    list(iterar_observaciones(47208, limite=100, sesion=sesion, pausa=0))
    assert sesion.llamadas[0]["id_above"] == 0
    assert sesion.llamadas[1]["id_above"] == 5
    assert sesion.llamadas[2]["id_above"] == 10


def test_iterar_descarta_observaciones_sin_foto():
    sesion = SesionFalsa(
        [{"results": [obs_cruda(1, con_foto=False), obs_cruda(2)]}, {"results": []}]
    )
    obs = list(iterar_observaciones(47208, limite=100, sesion=sesion, pausa=0))
    assert [o.id for o in obs] == [2]


def test_iterar_termina_con_pagina_vacia():
    sesion = SesionFalsa([{"results": []}])
    assert list(iterar_observaciones(47208, limite=100, sesion=sesion, pausa=0)) == []


def test_iterar_tolera_ubicacion_ausente():
    cruda = obs_cruda(1)
    del cruda["location"]
    sesion = SesionFalsa([{"results": [cruda]}, {"results": []}])
    o = next(iter(iterar_observaciones(47208, limite=1, sesion=sesion, pausa=0)))
    assert o.latitud is None and o.longitud is None
