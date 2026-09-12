import csv
import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pipeline.descarga import (
    COLUMNAS_MANIFIESTO,
    descargar_clase,
    descargar_todo,
    escribir_manifiesto,
    leer_manifiesto,
)
from pipeline.inat import Observacion
from pipeline.ontologia import cargar_ontologia


def bytes_imagen(lado=400):
    rng = np.random.default_rng(1)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(base).resize((lado, lado)).save(buffer, "JPEG")
    return buffer.getvalue()


class SesionImagenOK:
    def __init__(self, lado=400):
        self.contenido = bytes_imagen(lado)
        self.pedidos = []

    def get(self, url, timeout=None):
        self.pedidos.append(url)
        return type("R", (), {"content": self.contenido, "raise_for_status": lambda s: None})()


def obs(oid, licencia="cc-by", observador=None):
    return Observacion(
        id=oid,
        taxon_id=62956,
        taxon_nombre="Ejemplo sp.",
        rango="species",
        observador=observador or f"u{oid}",
        foto_url=f"https://x/{oid}/medium.jpg",
        licencia=licencia,
        atribucion="(c) alguien",
        latitud=-3.7,
        longitud=-73.2,
        fecha="2026-02-01",
    )


def falso_iterador(observaciones):
    def _iterar(taxon_id, *, limite, **kwargs):
        for i, o in enumerate(observaciones):
            if i >= limite:
                return
            yield o

    return _iterar


def test_descarga_guarda_archivos_y_devuelve_filas(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(1), obs(2)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert len(filas) == 2
    for fila in filas:
        assert set(fila) == set(COLUMNAS_MANIFIESTO)
        assert (tmp_path / fila["archivo"]).exists()


def test_ruta_de_archivo_refleja_orden_y_familia(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(7)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=1, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert filas[0]["archivo"] == "OrdenA/FamiliaX/7.jpg"


def test_sin_familia_va_a_carpeta_propia(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(8)]))
    filas = descargar_clase(
        "OrdenA", "", 47208,
        cupo=1, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert filas[0]["archivo"] == "OrdenA/_sin_familia/8.jpg"
    assert filas[0]["familia"] == ""


def test_descarta_licencias_no_permitidas(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(
        mod, "iterar_observaciones", falso_iterador([obs(1, licencia=""), obs(2, licencia="cc0")])
    )
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert [f["obs_id"] for f in filas] == [2]


def test_salta_observaciones_ya_descargadas(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(1), obs(2), obs(3)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados={1, 3},
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert [f["obs_id"] for f in filas] == [2]


def test_respeta_el_cupo(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(i) for i in range(1, 30)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=4, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert len(filas) == 4


def test_imagen_chica_no_entra_al_manifiesto(tmp_path: Path, monkeypatch):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(1)]))
    filas = descargar_clase(
        "OrdenA", "FamiliaX", 62956,
        cupo=5, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(lado=100), pausa=0,
    )
    assert filas == []


def test_manifiesto_ida_y_vuelta(tmp_path: Path):
    filas = [
        {c: "" for c in COLUMNAS_MANIFIESTO} | {"archivo": "A/B/1.jpg", "obs_id": 1, "observador": "u1"}
    ]
    ruta = tmp_path / "manifiesto.csv"
    escribir_manifiesto(filas, ruta)
    leidas = leer_manifiesto(ruta)
    assert leidas[0]["archivo"] == "A/B/1.jpg"
    assert leidas[0]["obs_id"] == "1"


def test_leer_manifiesto_inexistente_da_lista_vacia(tmp_path: Path):
    assert leer_manifiesto(tmp_path / "no_existe.csv") == []


def test_escritura_interrumpida_no_trunca_el_manifiesto_anterior(tmp_path: Path, monkeypatch):
    """Una escritura que revienta a mitad de camino no debe tocar el archivo anterior.

    `escribir_manifiesto` nunca debe escribir directamente sobre el destino:
    arma el CSV completo en un temporal y solo lo promueve con `os.replace`
    cuando termina sin errores. Se simula el corte parcheando
    `csv.DictWriter.writerows` (el paso que vuelca el cuerpo del CSV, ya con
    la cabecera escrita) para que falle, sin matar el proceso de verdad.
    """
    ruta = tmp_path / "manifiesto.csv"
    filas_previas = [
        {c: "" for c in COLUMNAS_MANIFIESTO} | {"archivo": f"A/B/{i}.jpg", "obs_id": str(i)}
        for i in range(1, 51)
    ]
    escribir_manifiesto(filas_previas, ruta)
    contenido_previo = ruta.read_text(encoding="utf-8")
    assert len(leer_manifiesto(ruta)) == 50

    def _revienta(self, filas):
        raise OSError("fallo de disco simulado a mitad de la reescritura")

    monkeypatch.setattr(csv.DictWriter, "writerows", _revienta)

    filas_nuevas = filas_previas + [
        {c: "" for c in COLUMNAS_MANIFIESTO} | {"archivo": "A/B/99.jpg", "obs_id": "99"}
    ]
    with pytest.raises(OSError):
        escribir_manifiesto(filas_nuevas, ruta)

    assert ruta.read_text(encoding="utf-8") == contenido_previo
    assert len(leer_manifiesto(ruta)) == 50


def test_escritura_interrumpida_no_deja_temporales_huerfanos(tmp_path: Path, monkeypatch):
    ruta = tmp_path / "manifiesto.csv"
    escribir_manifiesto([], ruta)

    def _revienta(self, filas):
        raise OSError("fallo de disco simulado a mitad de la reescritura")

    monkeypatch.setattr(csv.DictWriter, "writerows", _revienta)

    with pytest.raises(OSError):
        escribir_manifiesto([{c: "" for c in COLUMNAS_MANIFIESTO}], ruta)

    restantes = sorted(p.name for p in tmp_path.iterdir())
    assert restantes == ["manifiesto.csv"]


def iterador_por_taxon(por_taxon):
    """Iterador falso que responde distinto según el taxón pedido.

    Reproduce la relación real: una familia es un subconjunto de su orden, y
    `iterar_observaciones` pagina siempre desde la observación más antigua,
    así que ambas cuotas se disputan exactamente las mismas observaciones.
    """

    def _iterar(taxon_id, *, limite, **kwargs):
        for i, o in enumerate(por_taxon.get(taxon_id, [])):
            if i >= limite:
                return
            yield o

    return _iterar


def test_la_cuota_de_orden_no_consume_observaciones_de_familias_declaradas(
    tmp_path: Path, ruta_ontologia: Path, monkeypatch
):
    """Las familias se descargan ANTES que la cuota de orden.

    Si el orden va primero se lleva las observaciones más antiguas —que son
    justo las que la familia pediría después—, las archiva bajo
    `_sin_familia` con la etiqueta de familia vacía, y `ya_descargados` hace
    que la familia ya no pueda recuperarlas nunca. Cada observación robada es
    un ejemplar que la familia pierde, y en una familia escasa eso la empuja
    bajo el umbral de admisión.
    """
    import pipeline.descarga as mod

    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    monkeypatch.setattr(
        mod,
        "iterar_observaciones",
        iterador_por_taxon(
            {
                47208: [obs(i) for i in range(1, 11)],  # orden completo
                62956: [obs(i) for i in (1, 2, 3, 4)],  # familia: subconjunto
                50340: [obs(i) for i in (5, 6)],  # otra familia: subconjunto
                47792: [obs(i) for i in (20, 21, 22)],
                49279: [obs(i) for i in (20,)],
            }
        ),
    )

    manifiesto = descargar_todo(
        cargar_ontologia(ruta_ontologia),
        raiz=tmp_path,
        cupo_orden=4,
        cupo_familia=2,
        sesion_api=None,
        sesion_img=SesionImagenOK(),
    )

    por_familia = {}
    for fila in manifiesto:
        por_familia.setdefault(fila["familia"], []).append(fila["obs_id"])

    assert sorted(por_familia.get("Curculionidae", [])) == [1, 2]
    assert sorted(por_familia.get("Chrysomelidae", [])) == [5, 6]
    assert sorted(por_familia.get("Libellulidae", [])) == [20]

    # Ninguna observación que una familia declarada podía reclamar terminó
    # archivada sin etiqueta de familia.
    reclamables = {1, 2, 3, 4, 5, 6, 20}
    sin_familia = {oid for oid in por_familia.get("", []) if oid in reclamables}
    assert sin_familia == {3, 4}, (
        "solo 3 y 4 sobran de Curculionidae (cupo 2 de 4 disponibles); "
        f"se perdieron además {sin_familia - {3, 4}}"
    )


def test_manifiesto_se_persiste_a_mitad_de_una_clase(tmp_path: Path, monkeypatch):
    """Un corte a mitad de una clase no debe dejar el manifiesto vacío.

    Se fuerza un fallo en `guardar_jpeg` (no capturado por `descargar_clase`,
    a diferencia de los fallos de descarga de imagen) después de la quinta
    observación, simulando que el proceso muere ahí. Con
    `intervalo_persistencia=2` deben quedar en disco las filas de los dos
    últimos volcados parciales completados (4), no ninguna.
    """
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(i) for i in range(1, 6)]))

    contador = {"n": 0}
    guardar_original = mod.imagenes.guardar_jpeg

    def guardar_que_revienta_en_la_quinta(img, ruta):
        contador["n"] += 1
        if contador["n"] == 5:
            raise RuntimeError("corte simulado a mitad de la clase")
        guardar_original(img, ruta)

    monkeypatch.setattr(mod.imagenes, "guardar_jpeg", guardar_que_revienta_en_la_quinta)

    with pytest.raises(RuntimeError):
        descargar_clase(
            "OrdenA", "FamiliaX", 62956,
            cupo=5, raiz=tmp_path, ya_descargados=set(),
            sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
            intervalo_persistencia=2,
        )

    filas_persistidas = leer_manifiesto(tmp_path / "manifiesto.csv")
    assert len(filas_persistidas) == 4
    assert [f["obs_id"] for f in filas_persistidas] == ["1", "2", "3", "4"]


def test_descargar_todo_aplica_las_opciones_del_orden(tmp_path: Path, monkeypatch):
    """Las familias heredan el filtro de adultos y la exclusión de su orden.

    Sin esto, las termitas bajarían también dentro de la cuota de su orden
    taxonómico y la misma foto quedaría con dos etiquetas de orden.
    """
    import pipeline.descarga as mod

    (tmp_path / "c.yaml").write_text(
        """
version: 1
minimos: {familia_train: 10, familia_test: 5}
ordenes:
  - nombre: OrdenA
    inat_taxon_id: 1
    excluir_taxon_ids: [2]
    familias: [{nombre: FamiliaX, inat_taxon_id: 11}]
  - nombre: OrdenB
    inat_taxon_id: 2
    solo_adultos: false
    familias: [{nombre: FamiliaY, inat_taxon_id: 21}]
""",
        encoding="utf-8",
    )
    pedidos = {}

    def _iterar(taxon_id, *, limite, **kwargs):
        pedidos[taxon_id] = kwargs
        return iter(())

    monkeypatch.setattr(mod, "iterar_observaciones", _iterar)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    descargar_todo(
        cargar_ontologia(tmp_path / "c.yaml"),
        raiz=tmp_path / "crudo", cupo_orden=1, cupo_familia=1,
        sesion_api=None, sesion_img=SesionImagenOK(),
    )

    for taxon in (1, 11):
        assert pedidos[taxon]["excluir_taxon_ids"] == (2,)
        assert pedidos[taxon]["solo_adultos"] is True
    for taxon in (2, 21):
        assert pedidos[taxon]["excluir_taxon_ids"] == ()
        assert pedidos[taxon]["solo_adultos"] is False


def test_las_observaciones_ya_descargadas_no_consumen_el_margen(tmp_path: Path, monkeypatch):
    """La cuota de orden corre después de sus familias y pagina desde las
    observaciones más antiguas, que las familias ya se llevaron. Si esas
    repetidas cuentan contra el margen de 3x, el orden se queda corto aunque
    la fuente tenga material de sobra (medido: Coleoptera 1099 de 1200)."""
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(i) for i in range(1, 13)]))
    filas = descargar_clase(
        "OrdenA", "", 1,
        cupo=2, raiz=tmp_path, ya_descargados=set(range(1, 11)),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert [f["obs_id"] for f in filas] == [11, 12]


def test_el_margen_sigue_acotando_las_observaciones_nuevas(tmp_path: Path, monkeypatch):
    """Sin licencia utilizable no se pagina toda la fuente: el margen de 3x
    sigue aplicando a las observaciones nuevas."""
    import pipeline.descarga as mod

    vistas = []

    def _iterar(taxon_id, *, limite, **kwargs):
        for i in range(1, min(limite, 1000) + 1):
            vistas.append(i)
            yield obs(i, licencia="")

    monkeypatch.setattr(mod, "iterar_observaciones", _iterar)
    filas = descargar_clase(
        "OrdenA", "", 1,
        cupo=2, raiz=tmp_path, ya_descargados=set(),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert filas == []
    assert len(vistas) <= 7  # 6 del margen, más a lo sumo una de lectura


def test_el_aviso_no_culpa_al_margen_si_la_fuente_se_agoto(tmp_path: Path, monkeypatch, caplog):
    import pipeline.descarga as mod

    monkeypatch.setattr(mod, "iterar_observaciones", falso_iterador([obs(i) for i in range(1, 11)]))
    descargar_clase(
        "OrdenA", "", 1,
        cupo=2, raiz=tmp_path, ya_descargados=set(range(1, 11)),
        sesion_api=None, sesion_img=SesionImagenOK(), pausa=0,
    )
    assert "la fuente no tenía más observaciones" in caplog.text
