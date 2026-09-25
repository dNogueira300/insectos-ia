"""Contenido estático del catálogo y de la demostración de la web.

La portada y la herramienta muestran fotos y cifras: aquí se eligen y se
calculan, para que ninguna se escriba a mano.

- Catálogo: una foto por familia (y por orden sin familias) del conjunto de
  entrenamiento, prefiriendo licencias libres y fotos grandes, con su F1 de la
  corrida vigente y su crédito.
- Demostración: fotos del conjunto de PRUEBA, que el modelo nunca vio, pasadas
  por el mismo ONNX y el mismo servicio que usa el backend.

    python -m pipeline.catalogo_web
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageOps

from pipeline.inferencia import UMBRAL_FAMILIA
from pipeline.ontologia import Ontologia, cargar_ontologia

RANGO_LICENCIA = {"cc0": 0, "cc-by": 1, "cc-by-sa": 2}
LADO_FOTO = 640
CALIDAD_WEBP = 80
CONFIANZA_DEMO = 0.9          # familia afirmada con holgura, para la portada
CANDIDATAS_POR_CLASE = 3
MAXIMO_INFERENCIAS = 200


def rango_licencia(licencia: str) -> int:
    return RANGO_LICENCIA.get((licencia or "").strip().lower(), len(RANGO_LICENCIA))


# "(c) Nombre, some rights reserved (CC BY)": el nombre puede tener comas.
_ATRIBUCION = re.compile(r"^\(c\)\s*(.+),\s*(?:some|all) rights reserved", re.IGNORECASE)


def credito(fila: dict) -> str:
    """El nombre del autor, sin el texto en inglés ni la licencia, que va aparte.

    Las fotos CC0 dicen solo "no rights reserved": se nombra al observador, que
    es quien la publicó, porque la web promete el crédito de cada autor.
    """
    atribucion = (fila.get("atribucion") or "").strip()
    hallado = _ATRIBUCION.match(atribucion)
    if hallado:
        return hallado.group(1).strip()
    if atribucion and "no rights reserved" not in atribucion.lower():
        return atribucion
    return (fila.get("observador") or "").strip() or "Autor no registrado"


def url_origen(fila: dict) -> str:
    """La página de la observación en iNaturalist, donde está el autor y la licencia."""
    obs_id = (fila.get("obs_id") or "").strip()
    return f"https://www.inaturalist.org/observations/{obs_id}" if obs_id else ""


def leer_desempeno(texto: str) -> dict:
    """F1 por clase y tabla de cobertura del informe de `pipeline.desempeno`."""
    datos: dict = {"ordenes": {}, "familias": {}, "cobertura": {}}
    seccion = None
    for linea in texto.splitlines():
        if linea.startswith("## "):
            titulo = linea[3:].lower()
            seccion = (
                "ordenes" if titulo.startswith("órdenes")
                else "familias" if titulo.startswith("familias")
                else "cobertura" if titulo.startswith("cobertura")
                else None
            )
            continue
        if seccion in ("ordenes", "familias"):
            m = re.match(r"\|\s*(\w+)\s*\|\s*([0-9.]+)\s*\|", linea)
            if m:
                datos[seccion][m.group(1)] = float(m.group(2))
        elif seccion == "cobertura":
            m = re.match(r"\|\s*([0-9.]+)\s*\|\s*([0-9.]+)%\s*\|\s*([0-9.]+)%\s*\|", linea)
            if m:
                datos["cobertura"][float(m.group(1))] = (
                    float(m.group(2)) / 100, float(m.group(3)) / 100
                )
    return datos


def clave_de(fila: dict) -> str:
    return fila["familia"] or f"orden:{fila['orden']}"


def clases_del_catalogo(onto: Ontologia, desempeno: dict, conteos: dict) -> list[dict]:
    clases = []
    for orden in onto.ordenes:
        if orden.familias:
            for familia in orden.familias:
                clases.append({
                    "id": f"familia-{familia.nombre}", "tipo": "familia",
                    "nombre": familia.nombre, "nombre_comun": familia.nombre_comun,
                    "orden": orden.nombre, "provisional": familia.provisional,
                    "f1": desempeno["familias"].get(familia.nombre),
                    "fotos_entrenamiento": conteos.get(familia.nombre, 0),
                })
        else:
            clases.append({
                "id": f"orden-{orden.nombre}", "tipo": "orden",
                "nombre": orden.nombre, "nombre_comun": orden.nombre_comun,
                "orden": orden.nombre, "provisional": False,
                "f1": desempeno["ordenes"].get(orden.nombre),
                "fotos_entrenamiento": conteos.get(f"orden:{orden.nombre}", 0),
            })
    return clases


def candidatas_de(filas: list[dict], clase: dict) -> list[dict]:
    if clase["tipo"] == "familia":
        return [f for f in filas if f["familia"] == clase["nombre"]]
    return [f for f in filas if f["orden"] == clase["nombre"] and not f["familia"]]


def elegir_foto(candidatas: list[dict], area_de: Callable[[str], int]) -> dict:
    """La de licencia más libre; entre esas, la de más píxeles."""
    mejor = min(rango_licencia(f["licencia"]) for f in candidatas)
    grupo = sorted(
        (f for f in candidatas if rango_licencia(f["licencia"]) == mejor),
        key=lambda f: f["archivo"],
    )
    return max(grupo, key=lambda f: area_de(f["archivo"]))


def ordenar_para_demo(candidatas: list[dict]) -> list[dict]:
    return sorted(candidatas, key=lambda f: (rango_licencia(f["licencia"]), f["archivo"]))


def optimizar_foto(origen: Path, destino: Path, lado: int = LADO_FOTO) -> tuple[int, int]:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(origen) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((lado, lado), Image.LANCZOS)
        img.save(destino, "WEBP", quality=CALIDAD_WEBP, method=6)
        return img.size


def elegir_demostracion(
    entradas: list[tuple[dict, list[dict]]],
    predecir: Callable[[dict], dict],
    fijadas: dict,
    cantidad_afirmados: int = 3,
) -> dict:
    """Afirmados de órdenes distintos, un incierto real y la foto de portada.

    `entradas` son (clase, filas de PRUEBA ordenadas); `predecir` pasa una fila
    por el modelo. `fijadas` permite elegir a mano 'principal' e 'incierto'.
    """
    por_archivo = {f["archivo"]: f for _, filas in entradas for f in filas}
    inferencias = 0

    def consultar(fila: dict) -> dict:
        nonlocal inferencias
        inferencias += 1
        if inferencias > MAXIMO_INFERENCIAS:
            raise RuntimeError("demasiadas inferencias buscando la demostración")
        return predecir(fila)

    afirmados: list[tuple[dict, dict]] = []
    if fijadas.get("principal"):
        fila = por_archivo[fijadas["principal"]]
        p = consultar(fila)
        # Una foto fijada a mano se valida igual que una elegida: la portada
        # dice "resultado real", así que tiene que ser un acierto afirmado.
        if p["familia"] != fila["familia"] or p["familia_incierta"]:
            raise ValueError(f"la foto principal fijada no es un acierto afirmado: {fila['archivo']}")
        afirmados.append((fila, p))
    ordenes_usados = {f["orden"] for f, _ in afirmados}
    for clase, filas in entradas:
        if len(afirmados) >= cantidad_afirmados:
            break
        if clase["tipo"] != "familia" or clase["orden"] in ordenes_usados:
            continue
        for fila in filas[:CANDIDATAS_POR_CLASE]:
            p = consultar(fila)
            if (p["familia"] == clase["nombre"] and not p["familia_incierta"]
                    and p["confianza_familia"] >= CONFIANZA_DEMO):
                afirmados.append((fila, p))
                ordenes_usados.add(clase["orden"])
                break

    incierto = None
    if fijadas.get("incierto"):
        fila = por_archivo[fijadas["incierto"]]
        p = consultar(fila)
        if p["orden"] != fila["orden"] or not p["familia_incierta"]:
            raise ValueError(f"la foto fijada como incierto no es incierta para el modelo: {fila['archivo']}")
        incierto = (fila, p)
    else:
        for clase, filas in entradas:
            if clase["tipo"] != "familia":
                continue
            for fila in filas[:CANDIDATAS_POR_CLASE]:
                p = consultar(fila)
                if p["orden"] == clase["orden"] and p["familia_incierta"]:
                    incierto = (fila, p)
                    break
            if incierto:
                break
    if not afirmados or incierto is None:
        raise RuntimeError("no se encontró una demostración completa")
    return {"principal": afirmados[0], "afirmados": afirmados, "incierto": incierto}


def verificar_origen(archivos: list[str], archivos_prueba: set[str]) -> None:
    ajenos = [a for a in archivos if a not in archivos_prueba]
    if ajenos:
        raise ValueError(
            f"la demostración usaría fotos de entrenamiento o validación: {ajenos}"
        )


def prediccion_a_dict(prediccion) -> dict:
    """La misma forma que devuelve /predecir (backend/app.py), sin las fichas."""
    return {
        "orden": prediccion.orden,
        "confianza_orden": prediccion.confianza_orden,
        "familia": prediccion.familia,
        "confianza_familia": prediccion.confianza_familia,
        "familia_incierta": prediccion.familia_incierta,
        "top_familias": [
            {"familia": nombre, "confianza": valor} for nombre, valor in prediccion.top_familias
        ],
    }


def hoja_de_contactos(clases: list[dict], publico: Path, destino: Path) -> None:
    """Todas las fotos del catálogo en una sola imagen, para revisarlas de un vistazo."""
    lado, columnas = 200, 8
    filas_hoja = (len(clases) + columnas - 1) // columnas
    hoja = Image.new("RGB", (columnas * lado, filas_hoja * (lado + 24)), (246, 248, 245))
    dibujo = ImageDraw.Draw(hoja)
    for i, clase in enumerate(clases):
        x, y = (i % columnas) * lado, (i // columnas) * (lado + 24)
        with Image.open(publico / clase["foto"]["archivo"].lstrip("/")) as img:
            miniatura = ImageOps.fit(img.convert("RGB"), (lado - 8, lado - 8))
        hoja.paste(miniatura, (x + 4, y + 4))
        dibujo.text((x + 6, y + lado), clase["id"], fill=(46, 46, 46))
    destino.parent.mkdir(parents=True, exist_ok=True)
    hoja.save(destino, quality=85)


def _leer_csv(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _ejemplo(fila: dict, prediccion: dict, archivo_publico: str) -> dict:
    return {
        "archivo": archivo_publico, "credito": credito(fila), "licencia": fila["licencia"],
        "url_origen": url_origen(fila),
        "real": {"orden": fila["orden"], "familia": fila["familia"]},
        "prediccion": prediccion,
    }


def main() -> None:
    from backend.app import CORRIDA_VIGENTE
    from backend.servicio import ServicioInsectos

    parser = argparse.ArgumentParser(description="Genera el catálogo y la demostración de la web")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--splits", default="datos/splits")
    parser.add_argument("--curado", default="datos/curado")
    parser.add_argument("--corrida", default=f"modelo/{CORRIDA_VIGENTE}")
    parser.add_argument("--desempeno", required=True,
                        help="informe por clase de la corrida, p. ej. docs/desempeno_por_clase_v4.md")
    parser.add_argument("--preferencias", default="frontend/catalogo_preferencias.yaml")
    parser.add_argument("--publico", default="frontend/public")
    parser.add_argument("--contactos", default="datos/catalogo_contactos.jpg")
    args = parser.parse_args()

    corrida, curado, publico = Path(args.corrida), Path(args.curado), Path(args.publico)
    onto = cargar_ontologia(Path(args.ontologia))
    desempeno = leer_desempeno(Path(args.desempeno).read_text(encoding="utf-8"))
    evaluacion = json.loads((corrida / "evaluacion.json").read_text(encoding="utf-8"))["test"]
    preferencias = yaml.safe_load(Path(args.preferencias).read_text(encoding="utf-8")) or {}
    fijadas_catalogo = preferencias.get("catalogo") or {}
    fijadas_demo = preferencias.get("demostracion") or {}

    train = _leer_csv(Path(args.splits) / "train.csv")
    prueba = _leer_csv(Path(args.splits) / "test.csv")
    conteos = Counter(clave_de(f) for f in train)
    clases = clases_del_catalogo(onto, desempeno, conteos)

    def area(archivo: str) -> int:
        with Image.open(curado / archivo) as img:
            return img.width * img.height

    por_archivo_train = {f["archivo"]: f for f in train}
    for clase in clases:
        fijada = fijadas_catalogo.get(clase["id"])
        fila = por_archivo_train[fijada] if fijada else elegir_foto(candidatas_de(train, clase), area)
        destino = publico / "catalogo" / "fotos" / f"{clase['id']}.webp"
        ancho, alto = optimizar_foto(curado / fila["archivo"], destino)
        clase["foto"] = {
            "archivo": f"/catalogo/fotos/{clase['id']}.webp", "ancho": ancho, "alto": alto,
            "credito": credito(fila), "licencia": fila["licencia"], "url_origen": url_origen(fila),
        }
        print(f"{clase['id']}: {fila['archivo']} ({fila['licencia']})")

    servicio = ServicioInsectos(corrida / "insectos.onnx", corrida / "etiquetas.json")
    demo_dir = publico / "catalogo" / "demo"

    def predecir(fila: dict) -> dict:
        # Se predice sobre el mismo WebP que se publica: el que el visitante envía.
        destino = demo_dir / (Path(fila["archivo"]).stem + ".webp")
        if not destino.exists():
            optimizar_foto(curado / fila["archivo"], destino)
        return prediccion_a_dict(servicio.predecir_bytes(destino.read_bytes()))

    entradas = [(c, ordenar_para_demo(candidatas_de(prueba, c))) for c in clases]
    demo = elegir_demostracion(entradas, predecir, fijadas_demo)
    usados = [demo["incierto"], *demo["afirmados"]]
    verificar_origen([f["archivo"] for f, _ in usados], {f["archivo"] for f in prueba})

    def publico_de(fila: dict) -> str:
        return f"/catalogo/demo/{Path(fila['archivo']).stem}.webp"

    principal, incierto = demo["principal"], demo["incierto"]
    demostracion = {
        "principal": _ejemplo(principal[0], principal[1], publico_de(principal[0])),
        "incierto": _ejemplo(incierto[0], incierto[1], publico_de(incierto[0])),
        "ejemplos": [_ejemplo(f, p, publico_de(f)) for f, p in [*demo["afirmados"], incierto]],
    }
    # Quedan en demo/ solo las fotos usadas; las probadas y descartadas se borran.
    conservar = {Path(e["archivo"]).name for e in demostracion["ejemplos"]}
    for sobrante in demo_dir.glob("*.webp"):
        if sobrante.name not in conservar:
            sobrante.unlink()

    responde, acierta = desempeno["cobertura"][UMBRAL_FAMILIA]
    catalogo = {
        "corrida": corrida.name,
        "metricas": {
            "n_prueba": evaluacion["n"],
            "exactitud_familia": evaluacion["exactitud_familia"],
            "top3_familia": evaluacion["top3_familia"],
            "f1_orden": evaluacion["macro_f1_orden"],
            "f1_familia": evaluacion["macro_f1_familia"],
            "umbral": UMBRAL_FAMILIA,
            "responde": responde,
            "acierta_cuando_responde": acierta,
        },
        "ordenes": [
            {"nombre": o.nombre, "nombre_comun": o.nombre_comun, "tiene_familias": bool(o.familias)}
            for o in onto.ordenes
        ],
        "clases": clases,
    }
    salida = publico / "catalogo"
    (salida / "catalogo.json").write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (salida / "demostracion.json").write_text(
        json.dumps(demostracion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    hoja_de_contactos(clases, publico, Path(args.contactos))
    print(f"Catálogo: {len(clases)} clases. Hoja de contactos en {args.contactos}")


if __name__ == "__main__":
    main()
