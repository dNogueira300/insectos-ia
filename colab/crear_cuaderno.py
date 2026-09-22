"""Genera colab/entrenar.ipynb. Editar este archivo, no el .ipynb, y regenerar:

    python colab/crear_cuaderno.py

Ojo con las barras invertidas: dentro de los bloques py('''...''') una
continuación de línea de shell se escribe como dos barras.
"""
import json
from pathlib import Path

celdas = []


def md(texto):
    celdas.append({"cell_type": "markdown", "metadata": {}, "source": texto.strip("\n").splitlines(keepends=True)})


def py(texto):
    celdas.append({
        "cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
        "source": texto.strip("\n").splitlines(keepends=True),
    })


md("""
# Entrenamiento del modelo de insectos — Google Colab

**Antes de empezar:** menú *Entorno de ejecución → Cambiar tipo de entorno de ejecución → GPU T4*.

Ejecuta las celdas en orden (*Entorno de ejecución → Ejecutar todas*).

**Si Colab se desconecta a mitad del entrenamiento:** vuelve a abrir este cuaderno y ejecuta todas las celdas otra vez.
El entrenamiento continúa desde la última época guardada en tu Google Drive; no se pierde más de una época.

Qué necesitas en tu Google Drive, en la carpeta `MyDrive/insectos-ia-colab/`:

- `dataset_v1.zip`
- `dataset_v1.sha256`

**Si esa carpeta es de otra cuenta y la compartieron contigo**, agrégale primero un acceso directo
en tu Drive: *Compartido conmigo → clic derecho → Organizar → Añadir acceso directo → Mi unidad*.
Lo que está solo en *Compartido conmigo* no aparece al montar Drive.
""")

md("## 1. Configuración")
py('''
# Nombre de la corrida: cámbialo solo si quieres empezar un entrenamiento NUEVO
# desde cero (por ejemplo, para probar otro backbone). Para continuar una
# corrida cortada, deja el mismo nombre.
CORRIDA = "v3_b2_288"
BACKBONE = "efficientnet_b2"
# Resolución de entrada en píxeles. Más resolución distingue mejor detalles
# finos (antenas, cintura de hormiga, mandíbulas), pero cada época tarda más.
# Exportar y evaluar la leen solas de la corrida: no hay que repetirla.
LADO = 288
RAMA = "main"

# Carpeta con dataset_v1.zip y dataset_v1.sha256. Si la carpeta es de OTRA
# cuenta y está compartida contigo, agrégale primero un acceso directo en tu
# Drive: "Compartido conmigo" -> clic derecho -> Organizar -> Añadir acceso
# directo -> Mi unidad. Lo que está solo en "Compartido conmigo" no aparece al
# montar Drive.
CARPETA_DATOS = "/content/drive/MyDrive/insectos-ia-colab"

# Dónde se guardan los checkpoints y el modelo. Por defecto, junto a los datos;
# cámbialo a una carpeta de tu propio Drive si los datos son de otra cuenta y
# prefieres no ocupar su espacio (unos 50 MB por corrida).
CARPETA_CORRIDAS = f"{CARPETA_DATOS}/corridas"

REPO = "https://github.com/dNogueira300/insectos-ia.git"
''')

md("## 2. Verificar la GPU")
py('''
import torch
assert torch.cuda.is_available(), (
    "No hay GPU. Menú Entorno de ejecución -> Cambiar tipo de entorno de ejecución -> T4 GPU"
)
print("GPU:", torch.cuda.get_device_name(0))
''')

md("## 3. Conectar Google Drive")
py('''
import os

from google.colab import drive

drive.mount("/content/drive")  # si dice "already mounted", está bien

faltan = [a for a in ("dataset_v1.zip", "dataset_v1.sha256")
          if not os.path.isfile(f"{CARPETA_DATOS}/{a}")]
if faltan:
    visible = sorted(os.listdir("/content/drive/MyDrive"))[:20] if os.path.isdir(
        "/content/drive/MyDrive") else []
    raise SystemExit(
        f"No encuentro {', '.join(faltan)} en {CARPETA_DATOS}." + chr(10) +
        "Si la carpeta es de otra cuenta y la ves en 'Compartido conmigo', Drive NO la "
        "muestra al montarse: agrégale un acceso directo en tu Mi unidad (clic derecho -> "
        "Organizar -> Añadir acceso directo -> Mi unidad), reinicia la sesión y reintenta." + chr(10) +
        f"En Mi unidad veo ahora: {visible}"
    )

DESTINO = f"{CARPETA_CORRIDAS}/{CORRIDA}"
os.makedirs(DESTINO, exist_ok=True)
print("Datos:", CARPETA_DATOS)
print("Las corridas se guardan en:", DESTINO)
''')

md("## 4. Descargar el código e instalar dependencias")
py('''
import os, subprocess
if os.path.isdir("/content/insectos-ia"):
    subprocess.run(["git", "-C", "/content/insectos-ia", "pull", "--ff-only"], check=True)
else:
    subprocess.run(["git", "clone", "-b", RAMA, REPO, "/content/insectos-ia"], check=True)
# Entrenar solo necesita timm. onnx y onnxruntime se instalan en la celda 7:
# arrastran una version de protobuf que choca con paquetes preinstalados de
# Colab (avisos inofensivos, pero innecesarios durante el entrenamiento).
!pip install -q timm
''')

md("""
## 5. Copiar el dataset al disco de la sesión

Se copia desde Drive a `/content` y se verifica que llegó entero antes de descomprimir.
Leer miles de fotos directamente desde Drive haría el entrenamiento muchas veces más lento.
""")
py('''
import hashlib, shutil, zipfile, os

if not os.path.isdir("/content/datos/curado"):
    shutil.copy(f"{CARPETA_DATOS}/dataset_v1.zip", "/content/dataset_v1.zip")
    esperada = open(f"{CARPETA_DATOS}/dataset_v1.sha256").read().split()[0]
    h = hashlib.sha256()
    with open("/content/dataset_v1.zip", "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    assert h.hexdigest() == esperada, "La copia del dataset está incompleta: vuelve a ejecutar esta celda."
    with zipfile.ZipFile("/content/dataset_v1.zip") as z:
        z.extractall("/content/datos")
    os.remove("/content/dataset_v1.zip")
print("Imágenes listas:", sum(len(a) for _, _, a in os.walk("/content/datos/curado")))
''')

md("""
## 6. Entrenar (o continuar)

Cada época deja un checkpoint en Drive. Si esta celda se corta, vuelve a ejecutar todo el cuaderno.
""")
py('''
%cd /content/insectos-ia
!python -m pipeline.entrenar --reanudar \\
    --backbone {BACKBONE} --lado {LADO} \\
    --ontologia /content/datos/ontologia/clases.yaml \\
    --imagenes /content/datos/curado \\
    --splits /content/datos/splits \\
    --destino "{DESTINO}" \\
    --trabajadores 2
''')

md("## 7. Exportar a ONNX y evaluar contra el conjunto de prueba")
py('''
!pip install -q onnx onnxruntime
%cd /content/insectos-ia
!python -m pipeline.exportar \\
    --pesos "{DESTINO}/mejor.pth" --etiquetas "{DESTINO}/etiquetas.json" \\
    --salida "{DESTINO}/insectos.onnx" \\
    --muestra /content/datos/splits/val.csv --imagenes /content/datos/curado
!python -m pipeline.evaluar \\
    --pesos "{DESTINO}/mejor.pth" --etiquetas "{DESTINO}/etiquetas.json" \\
    --splits /content/datos/splits --curado /content/datos/curado \\
    --salida "{DESTINO}/informe_metricas.md"
print(open(f"{DESTINO}/informe_metricas.md", encoding="utf-8").read())
''')

md("""
## Qué entregar al terminar

Descarga desde `<CARPETA_CORRIDAS>/<CORRIDA>/` estos archivos:

- `insectos.onnx`
- `etiquetas.json`
- `metricas.json`
- `informe_metricas.md`
""")

cuaderno = {
    "cells": celdas,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"gpuType": "T4", "provenance": []},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}
destino = Path("colab/entrenar.ipynb")
destino.parent.mkdir(exist_ok=True)
destino.write_text(json.dumps(cuaderno, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(destino, len(celdas), "celdas")
