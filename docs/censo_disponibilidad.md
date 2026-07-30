# Censo de disponibilidad de imágenes por clase

Umbral de admisión de una familia: **150 imágenes curadas en train y 30 en test**.

Factor de curación estimado: **1.5** (se asume que sobrevive ~67% de lo descargado tras deduplicar y filtrar). Por eso el objetivo de observaciones crudas es **270** por familia.

La columna *en lugar* filtra por la región configurada; sirve para ver cuánto del material disponible es realmente amazónico.

**Los conteos incluyen solo ejemplares adultos** (`solo_adultos=True` excluye larvas, orugas y ninfas por defecto en la consulta a iNaturalist). Quien compare estas cifras contra la web pública de iNaturalist verá números menores por esa razón; no es un error del censo.

**El veredicto se calcula solo con la columna *iNat global* (conteo mundial)**, no con *iNat en lugar*. Una clase abundante en el mundo pero casi ausente en la región configurada puede salir marcada como "suficiente" igual: no se debe leer "suficiente" como "suficiente material amazónico". Si el veredicto debe ponderar la columna regional es una decisión pendiente, todavía sin tomar.

**`N/D`** marca una celda que no se consultó, para no confundirla con un 0 real (0 significa "se consultó y no hay registros"). Las columnas GBIF de las familias siempre muestran `N/D`: la ontología solo asigna `gbif_key` a nivel de orden, así que GBIF nunca se consulta para una familia por sí sola. También aparece `N/D` en cualquier columna de una fila con veredicto `error_consulta`.

**`error_consulta`** marca una clase en la que la consulta a iNaturalist o a GBIF falló (red, límite de tasa, etc.). No equivale a "insuficiente": significa que no se sabe todavía y hay que reintentar esa clase.

| Nivel | Orden | Clase | iNat global | iNat en lugar | GBIF global | GBIF país | Objetivo | Veredicto |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| orden | Blattodea | Blattodea | 27508 | 78 | 195716 | 1469 | 270 | suficiente |
| orden | Coleoptera | Coleoptera | 1959855 | 3354 | 8830392 | 27867 | 270 | suficiente |
| orden | Dermaptera | Dermaptera | 12595 | 74 | 93468 | 141 | 270 | suficiente |
| orden | Diptera | Diptera | 1059830 | 464 | 10683476 | 161054 | 270 | suficiente |
| orden | Ephemeroptera | Ephemeroptera | 5690 | 2 | 96503 | 54 | 270 | suficiente |
| orden | Hemiptera | Hemiptera | 1554281 | 1739 | 5771832 | 24752 | 270 | suficiente |
| orden | Hymenoptera | Hymenoptera | 926746 | 2129 | 8406310 | 49312 | 270 | suficiente |
| orden | Lepidoptera | Lepidoptera | 13783238 | 14570 | 32525043 | 63977 | 270 | suficiente |
| orden | Mantodea | Mantodea | 69857 | 168 | 319588 | 517 | 270 | suficiente |
| orden | Neuroptera | Neuroptera | 61602 | 15 | 218408 | 142 | 270 | suficiente |
| orden | Odonata | Odonata | 751348 | 935 | 4845204 | 4310 | 270 | suficiente |
| orden | Orthoptera | Orthoptera | 461157 | 888 | 2146398 | 5074 | 270 | suficiente |
| orden | Phasmida | Phasmida | 16335 | 121 | 67634 | 210 | 270 | suficiente |
| orden | Thysanoptera | Thysanoptera | 487 | 0 | 140519 | 1534 | 270 | suficiente |
| orden | Trichoptera | Trichoptera | 14526 | 3 | 359884 | 600 | 270 | suficiente |

## Familias que no alcanzan el umbral

Ninguna: todas las familias censadas alcanzan el objetivo.

Estas familias no entran como clase propia. Se agrupan en `Otros_<Orden>` dentro de su orden, o se reemplazan por otras que la Facultad considere igual de relevantes y con más material disponible.
