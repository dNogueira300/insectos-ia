from pathlib import Path

import pytest
from PIL import Image

from pipeline.catalogo_web import (
    clases_del_catalogo,
    credito,
    elegir_demostracion,
    elegir_foto,
    leer_desempeno,
    optimizar_foto,
    rango_licencia,
    verificar_origen,
)
from pipeline.ontologia import cargar_ontologia

YAML = """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: OrdA
    inat_taxon_id: 1
    nombre_comun: los A
    familias:
      - {nombre: FamA1, inat_taxon_id: 11, nombre_comun: uno}
      - {nombre: FamA2, inat_taxon_id: 12, provisional: true}
  - nombre: OrdB
    inat_taxon_id: 2
    familias:
      - {nombre: FamB1, inat_taxon_id: 21}
  - nombre: OrdC
    inat_taxon_id: 3
    nombre_comun: los C
    familias: []
"""

DESEMPENO = """# Desempeño por clase — prueba

## Órdenes

| Clase | F1 | Imágenes | Confusión principal |
| --- | ---: | ---: | --- |
| OrdA | 0.91 | 100 | OrdB (3) |
| OrdC | 0.87 | 50 | OrdA (2) |

## Familias

| Clase | F1 | Imágenes | Confusión principal |
| --- | ---: | ---: | --- |
| FamA1 | 0.95 | 40 | FamA2 (1) |
| FamA2 | 0.80 | 30 | — |

## Cobertura contra confianza (familias)

| Umbral | Responde | Acierta cuando responde |
| --- | ---: | ---: |
| 0.0 | 100% | 92.1% |
| 0.7 | 94% | 95.5% |
"""


@pytest.fixture
def onto(tmp_path: Path):
    ruta = tmp_path / "clases.yaml"
    ruta.write_text(YAML, encoding="utf-8")
    return cargar_ontologia(ruta)


def fila(archivo, orden, familia="", licencia="cc-by-nc", atribucion="(c) Ana"):
    return {"archivo": archivo, "orden": orden, "familia": familia, "licencia": licencia,
            "atribucion": atribucion, "url": f"https://x/{archivo}"}


def test_rango_licencia_prefiere_las_libres():
    assert rango_licencia("cc0") < rango_licencia("CC-BY") < rango_licencia("cc-by-sa")
    assert rango_licencia("cc-by-sa") < rango_licencia("cc-by-nc") == rango_licencia("")


def test_credito_sin_atribucion_no_queda_vacio():
    assert credito(fila("a.jpg", "OrdA", atribucion="  ")) == "Autor no registrado"
    assert credito(fila("a.jpg", "OrdA")) == "(c) Ana"


def test_leer_desempeno_toma_f1_y_cobertura():
    datos = leer_desempeno(DESEMPENO)
    assert datos["ordenes"] == {"OrdA": 0.91, "OrdC": 0.87}
    assert datos["familias"] == {"FamA1": 0.95, "FamA2": 0.80}
    assert datos["cobertura"][0.7] == pytest.approx((0.94, 0.955))


def test_elegir_foto_prefiere_licencia_libre_y_despues_la_mas_grande():
    filas = [
        fila("chica_libre.jpg", "OrdA", "FamA1", "cc0"),
        fila("grande_libre.jpg", "OrdA", "FamA1", "cc0"),
        fila("enorme_nc.jpg", "OrdA", "FamA1", "cc-by-nc"),
    ]
    areas = {"chica_libre.jpg": 100, "grande_libre.jpg": 900, "enorme_nc.jpg": 10_000}
    assert elegir_foto(filas, areas.__getitem__)["archivo"] == "grande_libre.jpg"


def test_clases_del_catalogo_incluye_familias_y_ordenes_sin_familias(onto):
    conteos = {"FamA1": 7, "FamA2": 3, "FamB1": 5, "orden:OrdC": 9}
    clases = clases_del_catalogo(onto, leer_desempeno(DESEMPENO), conteos)
    assert [c["id"] for c in clases] == ["familia-FamA1", "familia-FamA2", "familia-FamB1", "orden-OrdC"]
    a2 = clases[1]
    assert a2["provisional"] is True and a2["orden"] == "OrdA" and a2["f1"] == 0.80
    c = clases[3]
    assert c["tipo"] == "orden" and c["orden"] == "OrdC" and c["f1"] == 0.87
    assert c["nombre_comun"] == "los C" and c["fotos_entrenamiento"] == 9
    assert clases[2]["f1"] is None      # sin fila en el informe: no se inventa


def test_optimizar_foto_reduce_a_webp(tmp_path: Path):
    origen = tmp_path / "grande.jpg"
    Image.new("RGB", (1600, 1200), (40, 120, 60)).save(origen)
    destino = tmp_path / "salida" / "x.webp"
    ancho, alto = optimizar_foto(origen, destino)
    assert (ancho, alto) == (640, 480)
    with Image.open(destino) as img:
        assert img.format == "WEBP"


def pred(orden, familia, conf=0.97, incierta=False):
    return {"orden": orden, "confianza_orden": 0.99, "familia": familia, "confianza_familia": conf,
            "familia_incierta": incierta, "top_familias": [{"familia": familia, "confianza": conf}]}


def test_elegir_demostracion_da_tres_afirmados_de_ordenes_distintos_y_un_incierto():
    entradas = [
        ({"tipo": "familia", "nombre": "FamA1", "orden": "OrdA"}, [fila("a1.jpg", "OrdA", "FamA1")]),
        ({"tipo": "familia", "nombre": "FamA2", "orden": "OrdA"}, [fila("a2.jpg", "OrdA", "FamA2")]),
        ({"tipo": "familia", "nombre": "FamB1", "orden": "OrdB"}, [fila("b1.jpg", "OrdB", "FamB1")]),
        ({"tipo": "familia", "nombre": "FamD1", "orden": "OrdD"}, [fila("d1.jpg", "OrdD", "FamD1")]),
        ({"tipo": "familia", "nombre": "FamE1", "orden": "OrdE"}, [fila("e1.jpg", "OrdE", "FamE1")]),
    ]
    respuestas = {
        "a1.jpg": pred("OrdA", "FamA1"),
        "a2.jpg": pred("OrdA", "FamA1", 0.4, True),        # incierta, orden correcto
        "b1.jpg": pred("OrdB", "FamB1"),
        "d1.jpg": pred("OrdD", "FamD1", 0.75),             # afirmada pero bajo 0.9: no sirve
        "e1.jpg": pred("OrdE", "FamE1"),
    }
    demo = elegir_demostracion(entradas, lambda f: respuestas[f["archivo"]], fijadas={})
    assert [f["archivo"] for f, _ in demo["afirmados"]] == ["a1.jpg", "b1.jpg", "e1.jpg"]
    assert demo["incierto"][0]["archivo"] == "a2.jpg"
    assert demo["principal"][0]["archivo"] == "a1.jpg"


def test_elegir_demostracion_respeta_la_foto_fijada():
    entradas = [
        ({"tipo": "familia", "nombre": "FamA1", "orden": "OrdA"},
         [fila("a1.jpg", "OrdA", "FamA1"), fila("a1b.jpg", "OrdA", "FamA1")]),
        ({"tipo": "familia", "nombre": "FamA2", "orden": "OrdA"}, [fila("a2.jpg", "OrdA", "FamA2")]),
    ]
    respuestas = {"a1.jpg": pred("OrdA", "FamA1"), "a1b.jpg": pred("OrdA", "FamA1"),
                  "a2.jpg": pred("OrdA", "FamA1", 0.4, True)}
    demo = elegir_demostracion(entradas, lambda f: respuestas[f["archivo"]],
                               fijadas={"principal": "a1b.jpg"}, cantidad_afirmados=1)
    assert demo["principal"][0]["archivo"] == "a1b.jpg"


def test_verificar_origen_rechaza_fotos_que_no_son_de_prueba():
    verificar_origen(["t1.jpg"], {"t1.jpg", "t2.jpg"})
    with pytest.raises(ValueError, match="entrenamiento"):
        verificar_origen(["x.jpg"], {"t1.jpg"})


def test_elegir_demostracion_rechaza_un_incierto_fijado_que_el_modelo_afirma():
    """Si el modelo cambia o la foto se recodifica, la foto fijada puede dejar de
    ser incierta; publicarla como caso incierto sería falso."""
    entradas = [
        ({"tipo": "familia", "nombre": "FamA1", "orden": "OrdA"},
         [fila("a1.jpg", "OrdA", "FamA1"), fila("a2.jpg", "OrdA", "FamA1")]),
    ]
    respuestas = {"a1.jpg": pred("OrdA", "FamA1"), "a2.jpg": pred("OrdA", "FamA2", 0.78)}
    with pytest.raises(ValueError, match="incierto"):
        elegir_demostracion(entradas, lambda f: respuestas[f["archivo"]],
                            fijadas={"incierto": "a2.jpg"}, cantidad_afirmados=1)


def test_elegir_demostracion_rechaza_una_principal_fijada_que_el_modelo_no_acierta():
    entradas = [
        ({"tipo": "familia", "nombre": "FamA1", "orden": "OrdA"},
         [fila("a1.jpg", "OrdA", "FamA1"), fila("a2.jpg", "OrdA", "FamA1")]),
    ]
    respuestas = {"a1.jpg": pred("OrdA", "FamA2"), "a2.jpg": pred("OrdA", "FamA1", 0.4, True)}
    with pytest.raises(ValueError, match="principal"):
        elegir_demostracion(entradas, lambda f: respuestas[f["archivo"]],
                            fijadas={"principal": "a1.jpg"}, cantidad_afirmados=1)
