from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.curacion import COLUMNAS_CURADO, curar, deduplicar, hashes_de, reporte_markdown
from pipeline.descarga import COLUMNAS_MANIFIESTO, escribir_manifiesto, leer_manifiesto


def fila(archivo, obs_id, orden="OrdenA", familia="FamX", hash_=None):
    base = {c: "" for c in COLUMNAS_MANIFIESTO}
    base.update(archivo=archivo, obs_id=str(obs_id), orden=orden, familia=familia,
                observador=f"u{obs_id}", licencia="cc-by")
    if hash_ is not None:
        base["hash"] = hash_
    return base


def escribir_imagen(raiz: Path, relativo: str, semilla: int, lado: int = 300):
    rng = np.random.default_rng(semilla)
    base = rng.integers(0, 255, size=(10, 10, 3), dtype=np.uint8)
    destino = raiz / relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(base).resize((lado, lado), Image.BICUBIC).save(destino, "JPEG", quality=90)


def test_deduplicar_conserva_una_de_dos_identicas():
    filas = [fila("a.jpg", 1, hash_="ffff0000ffff0000"), fila("b.jpg", 2, hash_="ffff0000ffff0000")]
    conservadas, descartadas = deduplicar(filas)
    assert len(conservadas) == 1
    assert len(descartadas) == 1
    assert descartadas[0]["motivo"] == "duplicado"


def test_deduplicar_no_toca_imagenes_distintas():
    filas = [fila("a.jpg", 1, hash_="ffff0000ffff0000"), fila("b.jpg", 2, hash_="0000ffff0000ffff")]
    conservadas, descartadas = deduplicar(filas)
    assert len(conservadas) == 2
    assert descartadas == []


def test_deduplicar_prefiere_la_fila_con_familia():
    filas = [
        fila("sin.jpg", 1, familia="", hash_="ffff0000ffff0000"),
        fila("con.jpg", 2, familia="FamX", hash_="ffff0000ffff0000"),
    ]
    conservadas, _ = deduplicar(filas)
    assert conservadas[0]["familia"] == "FamX"


def test_deduplicar_descarta_contra_hashes_externos():
    filas = [fila("a.jpg", 1, hash_="ffff0000ffff0000")]
    conservadas, descartadas = deduplicar(filas, hashes_externos={"ffff0000ffff0000"})
    assert conservadas == []
    assert descartadas[0]["motivo"] == "duplicado_externo"


def test_hashes_de_marca_los_archivos_ilegibles(tmp_path: Path):
    escribir_imagen(tmp_path, "ok.jpg", 1)
    (tmp_path / "roto.jpg").write_bytes(b"no soy una imagen")
    filas = [fila("ok.jpg", 1), fila("roto.jpg", 2)]
    resultado = hashes_de(filas, tmp_path)
    assert resultado[0]["hash"]
    assert resultado[1]["hash"] == ""


def test_curar_copia_solo_las_conservadas(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 1)   # misma semilla: duplicada
    escribir_imagen(crudo, "OrdenA/FamX/3.jpg", 77)  # distinta
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2), fila("OrdenA/FamX/3.jpg", 3)],
        crudo / "manifiesto.csv",
    )

    resumen = curar(crudo, curado)

    assert resumen["entrada"] == 3
    assert resumen["conservadas"] == 2
    assert (curado / "manifiesto_curado.csv").exists()
    copiadas = list(curado.rglob("*.jpg"))
    assert len(copiadas) == 2


def test_manifiesto_curado_incluye_la_columna_hash(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 5)
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")
    curar(crudo, curado)
    texto = (curado / "manifiesto_curado.csv").read_text(encoding="utf-8")
    assert "hash" in texto.splitlines()[0]
    assert set(COLUMNAS_CURADO) == set(COLUMNAS_MANIFIESTO) | {"hash"}


def test_curar_descarta_archivos_ilegibles(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 6)
    (crudo / "OrdenA/FamX/2.jpg").write_bytes(b"basura")
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2)], crudo / "manifiesto.csv"
    )
    resumen = curar(crudo, curado)
    assert resumen["conservadas"] == 1
    assert resumen["por_motivo"]["ilegible"] == 1


def test_segunda_corrida_elimina_archivos_que_el_manifiesto_ya_no_incluye(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 77)
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2)],
        crudo / "manifiesto.csv",
    )
    curar(crudo, curado)
    assert (curado / "OrdenA/FamX/2.jpg").exists()

    # La descarga se corrige y el manifiesto de origen ya no trae la obs. 2.
    escribir_manifiesto([fila("OrdenA/FamX/1.jpg", 1)], crudo / "manifiesto.csv")
    curar(crudo, curado)

    assert not (curado / "OrdenA/FamX/2.jpg").exists()
    assert (curado / "OrdenA/FamX/1.jpg").exists()


def test_destino_coincide_exactamente_con_el_manifiesto_curado(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 1)   # duplicada de la 1
    escribir_imagen(crudo, "OrdenA/FamX/3.jpg", 77)
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2), fila("OrdenA/FamX/3.jpg", 3)],
        crudo / "manifiesto.csv",
    )

    curar(crudo, curado)

    conservadas = leer_manifiesto(curado / "manifiesto_curado.csv")
    rutas_del_manifiesto = {(curado / c["archivo"]).resolve() for c in conservadas}
    rutas_en_disco = {p.resolve() for p in curado.rglob("*.jpg")}
    assert rutas_en_disco == rutas_del_manifiesto


def test_curar_es_idempotente_en_corridas_repetidas(tmp_path: Path):
    crudo, curado = tmp_path / "crudo", tmp_path / "curado"
    escribir_imagen(crudo, "OrdenA/FamX/1.jpg", 1)
    escribir_imagen(crudo, "OrdenA/FamX/2.jpg", 1)   # duplicada de la 1
    escribir_imagen(crudo, "OrdenA/FamX/3.jpg", 77)
    escribir_manifiesto(
        [fila("OrdenA/FamX/1.jpg", 1), fila("OrdenA/FamX/2.jpg", 2), fila("OrdenA/FamX/3.jpg", 3)],
        crudo / "manifiesto.csv",
    )

    resumen_1 = curar(crudo, curado)
    archivos_1 = sorted(p.relative_to(curado) for p in curado.rglob("*.jpg"))

    resumen_2 = curar(crudo, curado)
    archivos_2 = sorted(p.relative_to(curado) for p in curado.rglob("*.jpg"))

    assert resumen_1 == resumen_2
    assert archivos_1 == archivos_2


def test_reporte_menciona_el_factor_real_de_curacion():
    resumen = {
        "entrada": 100,
        "conservadas": 60,
        "por_motivo": {"duplicado": 30, "ilegible": 10},
        "por_clase": {"OrdenA/FamX": 60},
    }
    texto = reporte_markdown(resumen)
    assert "1.67" in texto  # 100/60, el factor a comparar con el estimado del censo
