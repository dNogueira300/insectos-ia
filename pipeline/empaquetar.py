"""Empaqueta el dataset para entrenar en Google Colab.

Colab lee muy lento miles de archivos chicos desde Drive: se sube un solo zip,
se copia al disco local de la sesión y se descomprime ahí. El paquete lleva
los splits, la ontología y solo las imágenes que los splits referencian (no
todo `datos/curado`, que incluye lo descartado por el filtro de contenido y el
tope por fotógrafo). Junto al zip se escribe su sha256, para detectar en Colab
una copia incompleta antes de gastar GPU en ella.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import zipfile
from pathlib import Path

SPLITS = ("train", "val", "test")


class ErrorEmpaquetado(Exception):
    """El paquete no se puede armar completo."""


def _referenciadas(ruta_splits: Path) -> list[str]:
    archivos: list[str] = []
    for split in SPLITS:
        with (ruta_splits / f"{split}.csv").open(encoding="utf-8", newline="") as f:
            archivos += [fila["archivo"] for fila in csv.DictReader(f)]
    return sorted(set(archivos))


def _sha256(ruta: Path) -> str:
    huella = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            huella.update(bloque)
    return huella.hexdigest()


def empaquetar(
    *, ruta_splits: Path, raiz_imagenes: Path, ruta_ontologia: Path, destino: Path
) -> dict:
    ruta_splits, raiz_imagenes, destino = Path(ruta_splits), Path(raiz_imagenes), Path(destino)
    archivos = _referenciadas(ruta_splits)

    faltantes = [a for a in archivos if not (raiz_imagenes / a).is_file()]
    if faltantes:
        muestra = ", ".join(faltantes[:5])
        raise ErrorEmpaquetado(
            f"faltan {len(faltantes)} imágenes referenciadas por los splits (p. ej. {muestra}). "
            "No se escribió ningún paquete."
        )

    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(destino.name + ".tmp")
    try:
        # Las imágenes ya son JPEG: comprimirlas no ahorra espacio y hace más
        # lenta la descompresión en Colab. Se guardan tal cual.
        with zipfile.ZipFile(temporal, "w", compression=zipfile.ZIP_STORED) as z:
            for split in SPLITS:
                z.write(ruta_splits / f"{split}.csv", f"splits/{split}.csv")
            z.write(ruta_ontologia, "ontologia/clases.yaml")
            for archivo in archivos:
                z.write(raiz_imagenes / archivo, f"curado/{archivo}")
        os.replace(temporal, destino)
    except BaseException:
        temporal.unlink(missing_ok=True)
        raise

    huella = _sha256(destino)
    destino.with_suffix(".sha256").write_text(f"{huella}  {destino.name}\n", encoding="utf-8")
    return {"imagenes": len(archivos), "sha256": huella, "bytes": destino.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser(description="Empaqueta el dataset para Colab")
    parser.add_argument("--splits", default="datos/splits")
    parser.add_argument("--imagenes", default="datos/curado")
    parser.add_argument("--ontologia", default="ontologia/clases.yaml")
    parser.add_argument("--destino", default="datos/paquete/dataset_v1.zip")
    args = parser.parse_args()

    resumen = empaquetar(
        ruta_splits=Path(args.splits),
        raiz_imagenes=Path(args.imagenes),
        ruta_ontologia=Path(args.ontologia),
        destino=Path(args.destino),
    )
    print(
        f"{args.destino}: {resumen['imagenes']} imágenes, "
        f"{resumen['bytes'] / 1e9:.2f} GB, sha256 {resumen['sha256'][:12]}..."
    )


if __name__ == "__main__":
    main()
