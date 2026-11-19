# Publicar INSECTIA: Google Cloud Run y túnel de respaldo

Fecha: 19 de noviembre de 2026.

- **Principal:** Google Cloud Run. Da una dirección `https://….run.app` estable, con HTTPS, que se abre desde cualquier celular.
- **Respaldo:** la laptop con `iniciar.bat` más un túnel de Cloudflare (`tunel.bat`). Sirve si Cloud Run falla o si no hay cuenta.

Por qué estas dos opciones, y no Hugging Face ni Render: ver la sección 4 de [`GUIA_BASE_DE_DATOS_Y_HOSTING.md`](GUIA_BASE_DE_DATOS_Y_HOSTING.md) y la nota del final.

## Lo que necesita el servidor (medido el 18-11-2026)

| Medida | Valor |
| --- | --- |
| RAM con el modelo cargado, sin uso | ≈195 MB |
| RAM máxima (pico) con fotos de 10 MB | ≈400 MB |
| Arranque: librerías + modelo | 2–3 s en la PC |
| Una predicción (1–2 hilos) | 0,2–0,3 s |
| **Contenedor con 1 GiB y 1 CPU (19-11-2026):** listo para responder | 2,9 s |
| Contenedor: predicción, foto normal / foto de 10 MB | 0,45 s / 1,3–1,5 s |
| Contenedor: RAM tras varias fotos de 10 MB | 322 MiB |

Con 1 vCPU y 1 GiB va holgado. El contenedor da exactamente las mismas predicciones que el servidor local.

---

## 1. Preparar los archivos que no están en Git

El modelo y la base no se versionan. La imagen los toma de la carpeta local:

- `modelo/v4_convnext_t_288/insectos.onnx` y `etiquetas.json`, de la corrida (ver CLAUDE.md);
- `bd/bd_insectos.sqlite`, que se genera así:

```powershell
.venv\Scripts\python -m pipeline.bd
```

La web (`frontend/dist`) no hace falta: el `Dockerfile` la construye.

## 2. Construir y probar la imagen en la PC

Con Docker Desktop abierto, en la carpeta `insectos-ia`:

```powershell
docker build -t insectia:local .
docker run --rm -m 1g --cpus 1 -p 8080:8080 insectia:local
```

Abrir http://localhost:8080 y hacer una identificación. Así se prueba exactamente lo que se publicará, con los mismos límites de memoria y CPU que en Cloud Run.

`.dockerignore` es una lista blanca: solo entran `backend/`, `pipeline/`, `ontologia/`, `frontend/`, la base y los dos archivos del modelo. La imagen ocupa unos 690 MB descomprimida; en el registro se guarda comprimida y ocupa bastante menos. Cuánto exactamente se ve en Artifact Registry después del primer `docker push`.

## 3. Preparar Google Cloud (una sola vez)

1. Crear la cuenta en https://cloud.google.com.
   - Pide una tarjeta para verificar la identidad. El nivel gratuito de Cloud Run no cobra mientras no se pase de la cuota.
2. En la consola, **Facturación → Presupuestos y alertas**: crear un presupuesto de 1 USD con aviso por correo.
3. Instalar la herramienta de línea de comandos:

```powershell
winget install --id Google.CloudSDK
```

4. Cerrar y volver a abrir PowerShell, y luego:

```powershell
gcloud init
gcloud projects create insectia-unap --name="INSECTIA"
gcloud config set project insectia-unap
gcloud billing projects link insectia-unap --billing-account=<ID de la cuenta de facturación>
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
gcloud artifacts repositories create insectia --repository-format=docker --location=us-central1
gcloud auth configure-docker us-central1-docker.pkg.dev
```

- El ID de facturación sale de `gcloud billing accounts list`.
- Si el nombre `insectia-unap` ya está tomado, usar otro y reemplazarlo en todos los comandos.
- Se usa **us-central1** porque está en la región de precios más barata (Tier 1), donde rige la cuota gratuita completa.

## 4. Publicar

```powershell
docker tag insectia:local us-central1-docker.pkg.dev/insectia-unap/insectia/web:v1
docker push us-central1-docker.pkg.dev/insectia-unap/insectia/web:v1

gcloud run deploy insectia `
  --image us-central1-docker.pkg.dev/insectia-unap/insectia/web:v1 `
  --region us-central1 `
  --cpu 1 --memory 1Gi `
  --min-instances 0 --max-instances 2 `
  --concurrency 8 `
  --cpu-boost `
  --set-env-vars ORT_HILOS=1 `
  --allow-unauthenticated
```

Al terminar, `gcloud` muestra la dirección `https://insectia-….run.app`.

Por qué estas opciones:
- `ORT_HILOS` debe coincidir con `--cpu`. onnxruntime podría ver los núcleos de la máquina anfitriona y lanzar más hilos de los que hay.
- `--max-instances 2` pone un techo: nadie puede multiplicar el gasto.
- `--cpu-boost` da más CPU durante el arranque y acorta el arranque en frío.

## 5. Comprobar desde el celular

1. Desconectar el wifi y usar **datos móviles**. Así se prueba internet de verdad y no la red de la casa.
2. Abrir `https://…run.app/salud`: debe decir `"estado":"ok"` y `"bd_disponible":true`.
3. Abrir la portada y luego **Identificar** → **Tomar foto**, con un insecto real o una foto impresa.
   - Medir cuánto tarda. Con el servidor despierto debe ser 1–3 s, según la señal.
4. Recorrer **Catálogo**, **Registros** (desde «Ver los N registros») y **Créditos**.
5. **Arranque en frío:** no abrir la página durante una hora, entrar de nuevo y medir la primera identificación.
   - Si tarda más de 90 s, la página corta y pide reintentar.
6. Preparar un QR con la dirección para el jurado.

## 6. El día de la defensa

Una hora antes, dejar una instancia siempre encendida, para que no haya arranque en frío:

```powershell
gcloud run services update insectia --region us-central1 --min-instances 1
```

Después de la defensa, volver a 0. Una instancia encendida de forma permanente gasta la cuota gratuita en pocos días:

```powershell
gcloud run services update insectia --region us-central1 --min-instances 0
```

Además:
- tener la laptop con `iniciar.bat` y `tunel.bat` listos (sección 8);
- revisar el gasto en **Facturación** al día siguiente.

## 7. Actualizar después

Para cambiar el modelo, la base o la web:

1. Regenerar lo que cambió.
2. `docker build`.
3. Etiquetar con una versión nueva (`web:v2`), hacer `docker push` y repetir `gcloud run deploy` con esa imagen.

El almacenamiento gratuito de Artifact Registry es de 0,5 GB, es decir, una sola imagen. Borrar las versiones viejas:

```powershell
gcloud artifacts docker images list us-central1-docker.pkg.dev/insectia-unap/insectia/web --include-tags
gcloud artifacts docker images delete us-central1-docker.pkg.dev/insectia-unap/insectia/web:v1
```

## 8. Respaldo: la laptop con túnel

Sirve si Cloud Run falla, o para mostrar el sistema sin cuenta en la nube.

1. Una sola vez: `winget install --id Cloudflare.cloudflared`.
2. Abrir `iniciar.bat` y esperar a que se abra el navegador.
3. Abrir `tunel.bat`. A los pocos segundos aparece una dirección `https://….trycloudflare.com`: esa es la pública.

Límites:
- la dirección **cambia cada vez**: hacer el QR en el momento;
- depende de que la laptop siga encendida y con internet;
- Cloudflare lo presenta como herramienta de pruebas: hasta 200 solicitudes a la vez, de sobra para un jurado.

La laptop identifica en unos 0,2 s, más rápido que Cloud Run con 1 vCPU.

---

## Nota: opciones descartadas (noviembre de 2026)

- **Hugging Face Spaces:** crear un Space con Docker o Gradio ahora exige el plan PRO (9 USD/mes). Solo los Spaces estáticos son gratuitos.
- **Render y Koyeb gratis:** 512 MB y 0,1 de CPU, y se duermen a los 15 min (Render) o a la hora (Koyeb). Despertar toma alrededor de un minuto.
- **Fly.io:** ya no tiene plan gratuito para cuentas nuevas. **Railway:** solo una prueba de 30 días.
- **Oracle Always Free:** potente (2 OCPU / 12 GB ARM), pero exige administrar un servidor. Queda como opción a largo plazo, junto con un servidor de la UNAP.
- **Reducir la foto en el navegador antes de subirla:** se probó y se descartó. Con fotos de más de 2000 px, cambió la familia en 1 de 31 fotos y la decisión de incertidumbre en 2. El servidor recibe la foto original, igual que en la evaluación.
