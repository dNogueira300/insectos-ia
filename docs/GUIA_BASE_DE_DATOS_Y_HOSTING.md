# Guía: la base de datos biológica y el hosting de INSECTIA

Fecha: 25 de septiembre de 2026.

Esta guía responde tres preguntas:
- de dónde salen las fichas que muestra la web;
- qué hacer con los Excel que llenan los alumnos;
- cómo se publicaría el sistema en un servidor, y qué pasa ahí con la base de datos.

---

## 1. De dónde salen las fichas

La web **no lee el Excel directamente**. En medio hay un paso de importación con validación:

```
bd/bd_insectos.xlsx  --(python -m pipeline.bd)-->  bd/bd_insectos.sqlite  -->  servidor  -->  web
     (el Excel)          valida y convierte           (la "base")
```

- **El Excel es la fuente.** Es `bd/bd_insectos.xlsx`, con una hoja llamada `BD_Insectos`. Se guarda en el repositorio.
- **La base es un archivo SQLite**, `bd/bd_insectos.sqlite`, generado a partir del Excel.
  - No es un servidor de base de datos ni hay nada que instalar: es un solo archivo.
  - No se guarda en Git porque siempre se puede volver a generar.
- **El servidor solo lee el SQLite.** Cuando la web dice "Aún no hay fichas" o "Sin fichas en la base todavía", significa que el SQLite no tiene filas para ese orden o esa familia.
- Hoy la base tiene 5 fichas de ejemplo.

**Por qué este paso intermedio:** la validación. Si alguien escribe una familia mal o en el orden equivocado, el sistema lo rechaza con el número de fila, en vez de mostrar datos incoherentes.

---

## 2. Qué hacer cuando lleguen los Excel de los alumnos

### Paso 1. Unirlos en un solo archivo

El archivo unido tiene que cumplir dos condiciones:
- tener una hoja llamada exactamente **`BD_Insectos`**;
- tener las **19 columnas** con estos nombres exactos:

`ID`, `Archivo_imagen`, `Vistas_fotograficas`, `Orden`, `Familia`, `Nombre_cientifico`, `Nombre_comun`, `Cultivo_asociado`, `Tipo_de_dano`, `Hospedero`, `Localidad`, `Coordenadas`, `Fecha`, `Colector`, `Importancia_economica`, `Estado_biologico`, `Fuente`, `Verificado_por`, `Observaciones`.

### Paso 2. Limpiarlo según lo que exige la validación

| Columna | Regla |
| --- | --- |
| `ID` | Obligatorio y sin repetirse. Al unir varios Excel es fácil que dos alumnos hayan usado "INS-0001": hay que renumerar. |
| `Orden` | Obligatorio, escrito igual que en el sistema: `Coleoptera`, `Isoptera`, etc. La lista está en `ontologia/clases.yaml`. |
| `Familia` | Puede ir vacía; el registro queda entonces solo al nivel de orden. Si se llena, tiene que ser una de las 38 familias del sistema y pertenecer a ese orden. |
| `Fecha` | Formato `AAAA-MM-DD`, por ejemplo `2026-09-01`. |
| `Coordenadas` | `latitud, longitud` en decimales, por ejemplo `-3.75, -73.25`. |

> **Cuidado con la fecha.** El importador lee todo como texto. Si la columna `Fecha` tiene formato de fecha de Excel, y no de texto, es muy probable que llegue como `2026-09-01 00:00:00` y se rechace. Todavía no se probó con un Excel real. Lo seguro es poner esa columna en formato **Texto** antes de escribir las fechas.

### Paso 3. Reemplazar el Excel del proyecto

Guardar el archivo unido como `bd/bd_insectos.xlsx`. Conviene conservar una copia del anterior.

### Paso 4. Importar

En PowerShell, dentro de la carpeta `insectos-ia`:

```powershell
.venv\Scripts\python -m pipeline.bd
```

Puede terminar de dos formas:
- **Todo bien:** dice `N registros importados en bd/bd_insectos.sqlite`.
- **Hay errores:** dice `NO se importó nada` y lista cada error con su fila. Por ejemplo: `fila 37: Familia 'Curculionidae' no pertenece al orden 'Hemiptera'`.
  - Basta **un solo error** para que no se importe nada. La base anterior queda intacta.
  - Se corrigen esas filas en el Excel y se repite el paso 4.

### Paso 5. Ver el resultado

No hace falta reiniciar el servidor: lee el SQLite en cada consulta, así que basta con recargar la página.
- En la herramienta, las fichas aparecen bajo el resultado de la familia.
- En el catálogo, las tarjetas de ese orden vuelven a ofrecer "Ver fichas".

### Paso 6. Guardar el Excel en Git

```powershell
git add bd/bd_insectos.xlsx
git commit -m "Base biológica: fichas de los alumnos"
git push
```

El SQLite no se sube; cualquier otra computadora lo genera con el paso 4.

### Qué muestra la web de cada ficha

- **Muestra:** nombre común, especie del registro, cultivo asociado, tipo de daño, hospedero, localidad y estado biológico.
- **`Importancia_economica`:** se muestra como etiqueta de color si dice "Plaga" o "Benéfico…"; si dice otra cosa, aparece como un dato más.
- **No muestra:** `Colector`, `Verificado_por`, `Coordenadas`, `Fecha` ni `Archivo_imagen`. La web no lleva nombres de personas y todavía no usa las fotos de la base.

---

## 3. Qué necesita un servidor para correr INSECTIA

El sistema es un solo programa: FastAPI con el modelo ONNX, que además sirve la web ya construida.

| Recurso | Qué necesita | Por qué |
| --- | --- | --- |
| Memoria RAM | **1 GB como mínimo, 2 GB para ir cómodo** | El modelo pesa 112 MB en disco y ocupa bastante más cargado en memoria. Un plan de 512 MB es muy probable que se quede corto. |
| Procesador | 1 o 2 núcleos, sin GPU | Cada identificación tarda alrededor de 1 s en CPU. Alcanza de sobra para una sustentación y para uso de campo moderado. |
| Disco | Menos de 1 GB | Modelo, web y base. |
| Software | Python 3.12 | Las dependencias están en `backend/requirements.txt`. |

**Dos detalles que cualquier servidor tiene que resolver:**

1. **El modelo no está en GitHub.** `insectos.onnx` pesa 112 MB y GitHub rechaza archivos de más de 100 MB. Hay que llevarlo al servidor por otro camino:
   - Git LFS;
   - subirlo como archivo de una "release" de GitHub;
   - subirlo a Hugging Face Hub;
   - o copiarlo a mano al servidor (por ejemplo con `scp`).
2. **La web se sirve ya construida.** Hay que ejecutar `npm run build` antes de publicar, o dentro del proceso de despliegue.

---

## 4. Opciones de hosting

Los precios cambian: los de abajo son una referencia aproximada y hay que verificarlos al contratar.

### Opción A. Hugging Face Spaces (recomendada para la sustentación y la difusión)

Es una plataforma pensada para publicar demos de modelos de IA.
- El plan gratuito con Docker trae CPU y memoria de sobra para este modelo.
- El modelo se aloja en el propio Hugging Face, sin el límite de 100 MB de GitHub.
- Da una dirección pública con HTTPS, que funciona desde cualquier celular.

**Contras:**
- El espacio "se duerme" tras un tiempo sin visitas. La primera visita después tarda en despertar mientras carga el modelo.
- El disco del plan gratuito no es persistente. En este sistema no importa, como se explica en la sección 5.

**Qué haría falta preparar:** un `Dockerfile` que instale las dependencias, construya la web, genere el SQLite desde el Excel y arranque el servidor.

### Opción B. Servidor de la universidad (recomendada a largo plazo, si existe)

Si la UNAP o la FISI tiene un servidor o una máquina virtual disponible, es la opción más natural para un proyecto institucional:
- no tiene costo;
- los datos quedan en la universidad;
- se puede administrar localmente.

Hay que pedir a TI:
- una máquina con 2 GB de RAM y Python 3.12;
- un dominio o subdominio, por ejemplo `insectia.unap.edu.pe`;
- un certificado HTTPS.

HTTPS importa para el celular: algunos navegadores limitan la cámara en sitios sin HTTPS.

### Opción C. Un VPS pequeño (servidor virtual propio)

Un servidor virtual con 2 GB de RAM en un proveedor como Hetzner, DigitalOcean o Contabo cuesta del orden de 5 a 12 USD al mes.
- **A favor:** control total, disco persistente y el sistema siempre despierto.
- **En contra:** alguien tiene que administrarlo (actualizaciones, reinicios, certificado HTTPS con Let's Encrypt).

### Opciones que no conviene usar

- **Planes gratuitos de Render, Railway y similares:** sus planes gratuitos suelen tener 512 MB de RAM, que probablemente no alcancen para el modelo, y se duermen a los pocos minutos.
- **Hosting "compartido" de páginas web** (el típico con cPanel para PHP): no corre aplicaciones Python con un modelo de IA.
- **Vercel, Netlify y GitHub Pages:** sirven páginas estáticas o funciones cortas, no un servidor con un modelo cargado en memoria.

### Resumen

| Situación | Opción |
| --- | --- |
| Sustentación o demo pública sin costo | Hugging Face Spaces |
| Uso continuo e institucional | Servidor de la UNAP |
| No hay servidor de la UNAP y se necesita estabilidad | VPS pequeño de 2 GB |
| Demo en el aula sin internet | La laptop con `iniciar.bat`; ver el README para abrirla desde celulares en la misma red |

---

## 5. Qué pasa con el SQLite en un servidor

**Hoy la web nunca escribe en la base: solo lee.** Todo lo que hay en el SQLite sale del Excel. Por eso, en un servidor, el SQLite **no se trata como un dato que hay que respaldar**, sino como algo que se regenera:

1. El Excel (`bd/bd_insectos.xlsx`) está en Git: es la única fuente de verdad.
2. En cada despliegue, el servidor ejecuta `python -m pipeline.bd` y genera el SQLite a partir de ese Excel.
3. Para actualizar las fichas publicadas:
   - se actualiza el Excel;
   - se valida localmente con el paso 4 de la sección 2;
   - se hace commit y push;
   - se vuelve a desplegar, y el servidor regenera el SQLite.

**Consecuencias:**
- No hace falta disco persistente ni copias de seguridad de la base en el servidor. Si el servidor se borra, se reconstruye igual desde el repositorio.
- No hace falta PostgreSQL ni MySQL: para unas decenas o miles de fichas que solo se leen, SQLite es más que suficiente.
- **Detalle técnico:** `pipeline.bd` usa pandas y openpyxl, que no están en `backend/requirements.txt`. En el despliegue hay dos caminos:
  - instalarlos también, aunque solo se usan al generar la base;
  - o generar el SQLite en la computadora del proyecto y subirlo junto con el modelo. Pesa unos 25 KB.

### Cuándo cambiaría esto

Si en el futuro la web **escribiera** datos, el SQLite dejaría de ser regenerable y pasaría a ser información que no se puede perder. Por ejemplo:
- que los técnicos de campo suban sus propias fichas desde el celular;
- que se guarde un historial de identificaciones;
- que haya usuarios con cuenta.

En ese caso:
- **Con un solo servidor y poco tráfico:** SQLite sigue sirviendo, pero en un **disco persistente** y con **copias de seguridad** periódicas. En un VPS o el servidor de la UNAP el disco ya es persistente; en Hugging Face habría que contratar almacenamiento persistente.
- **Con varios servidores, muchos usuarios escribiendo a la vez o un equipo que administre los datos:** conviene pasar a PostgreSQL.

Nada de eso existe hoy, así que no hace falta decidirlo todavía.
