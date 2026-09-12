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
| orden | Blattodea | Blattodea | 28445 | 82 | 204646 | 1486 | 270 | suficiente |
| familia | Blattodea | Blaberidae | 4216 | 23 | N/D | N/D | 270 | suficiente |
| familia | Blattodea | Blattidae | 9720 | 29 | N/D | N/D | 270 | suficiente |
| orden | Coleoptera | Coleoptera | 2017619 | 3424 | 9190885 | 28198 | 270 | suficiente |
| familia | Coleoptera | Carabidae | 129699 | 30 | N/D | N/D | 270 | suficiente |
| familia | Coleoptera | Cerambycidae | 155853 | 330 | N/D | N/D | 270 | suficiente |
| familia | Coleoptera | Chrysomelidae | 239774 | 1015 | N/D | N/D | 270 | suficiente |
| familia | Coleoptera | Coccinellidae | 572483 | 694 | N/D | N/D | 270 | suficiente |
| familia | Coleoptera | Curculionidae | 86012 | 73 | N/D | N/D | 270 | suficiente |
| familia | Coleoptera | Scarabaeidae | 198125 | 411 | N/D | N/D | 270 | suficiente |
| orden | Dermaptera | Dermaptera | 13304 | 86 | 100065 | 161 | 270 | suficiente |
| orden | Diptera | Diptera | 1108218 | 475 | 10876962 | 161107 | 270 | suficiente |
| familia | Diptera | Agromyzidae | 229 | 1 | N/D | N/D | 270 | insuficiente |
| familia | Diptera | Anthomyiidae | 2359 | 1 | N/D | N/D | 270 | suficiente |
| familia | Diptera | Culicidae | 18447 | 5 | N/D | N/D | 270 | suficiente |
| familia | Diptera | Drosophilidae | 5198 | 5 | N/D | N/D | 270 | suficiente |
| familia | Diptera | Tephritidae | 15151 | 10 | N/D | N/D | 270 | suficiente |
| orden | Ephemeroptera | Ephemeroptera | 5851 | 2 | 98999 | 54 | 270 | suficiente |
| orden | Hemiptera | Hemiptera | 1607769 | 1776 | 6003905 | 24882 | 270 | suficiente |
| familia | Hemiptera | Aphididae | 3420 | 2 | N/D | N/D | 270 | suficiente |
| familia | Hemiptera | Cicadellidae | 186214 | 395 | N/D | N/D | 270 | suficiente |
| familia | Hemiptera | Coreidae | 182963 | 687 | N/D | N/D | 270 | suficiente |
| familia | Hemiptera | Pentatomidae | 423867 | 98 | N/D | N/D | 270 | suficiente |
| familia | Hemiptera | Reduviidae | 99961 | 114 | N/D | N/D | 270 | suficiente |
| orden | Hymenoptera | Hymenoptera | 967274 | 2156 | 8692161 | 49565 | 270 | suficiente |
| familia | Hymenoptera | Apidae | 342189 | 445 | N/D | N/D | 270 | suficiente |
| familia | Hymenoptera | Chalcididae | 348 | 0 | N/D | N/D | 270 | suficiente |
| familia | Hymenoptera | Formicidae | 219640 | 1419 | N/D | N/D | 270 | suficiente |
| familia | Hymenoptera | Ichneumonidae | 17951 | 12 | N/D | N/D | 270 | suficiente |
| familia | Hymenoptera | Vespidae | 150909 | 146 | N/D | N/D | 270 | suficiente |
| orden | Isoptera | Isoptera | 1540 | 9 | N/D | N/D | 270 | suficiente |
| familia | Isoptera | Heterotermitidae | 311 | 0 | N/D | N/D | 270 | suficiente |
| familia | Isoptera | Kalotermitidae | 332 | 3 | N/D | N/D | 270 | suficiente |
| familia | Isoptera | Mastotermitidae | 13 | 0 | N/D | N/D | 270 | insuficiente |
| familia | Isoptera | Rhinotermitidae | 10 | 1 | N/D | N/D | 270 | insuficiente |
| familia | Isoptera | Termitidae | 447 | 5 | N/D | N/D | 270 | suficiente |
| orden | Lepidoptera | Lepidoptera | 14326996 | 16251 | 34754299 | 65752 | 270 | suficiente |
| familia | Lepidoptera | Noctuidae | 1292334 | 128 | N/D | N/D | 270 | suficiente |
| familia | Lepidoptera | Papilionidae | 648113 | 356 | N/D | N/D | 270 | suficiente |
| familia | Lepidoptera | Pieridae | 767333 | 330 | N/D | N/D | 270 | suficiente |
| familia | Lepidoptera | Pyralidae | 189532 | 69 | N/D | N/D | 270 | suficiente |
| familia | Lepidoptera | Sphingidae | 451768 | 615 | N/D | N/D | 270 | suficiente |
| orden | Mantodea | Mantodea | 73752 | 172 | 344541 | 543 | 270 | suficiente |
| orden | Neuroptera | Neuroptera | 64219 | 15 | 230159 | 145 | 270 | suficiente |
| orden | Odonata | Odonata | 781620 | 941 | 5069045 | 4399 | 270 | suficiente |
| familia | Odonata | Aeshnidae | 51230 | 82 | N/D | N/D | 270 | suficiente |
| familia | Odonata | Calopterygidae | 44311 | 17 | N/D | N/D | 270 | suficiente |
| familia | Odonata | Coenagrionidae | 180556 | 167 | N/D | N/D | 270 | suficiente |
| familia | Odonata | Gomphidae | 28924 | 18 | N/D | N/D | 270 | suficiente |
| familia | Odonata | Libellulidae | 401293 | 589 | N/D | N/D | 270 | suficiente |
| orden | Orthoptera | Orthoptera | 477536 | 901 | 2259508 | 5139 | 270 | suficiente |
| familia | Orthoptera | Acrididae | 191510 | 202 | N/D | N/D | 270 | suficiente |
| familia | Orthoptera | Gryllidae | 16558 | 10 | N/D | N/D | 270 | suficiente |
| familia | Orthoptera | Tettigoniidae | 195639 | 536 | N/D | N/D | 270 | suficiente |
| orden | Phasmida | Phasmida | 17042 | 132 | 71870 | 210 | 270 | suficiente |
| orden | Psocodea | Psocodea | 29049 | 5 | 244808 | 2448 | 270 | suficiente |
| orden | Thysanoptera | Thysanoptera | 514 | 0 | 140855 | 1534 | 270 | suficiente |
| orden | Trichoptera | Trichoptera | 15211 | 3 | 367095 | 600 | 270 | suficiente |

## Familias que no alcanzan el umbral

Agromyzidae, Mastotermitidae, Rhinotermitidae

Estas familias no entran como clase propia. Se agrupan en `Otros_<Orden>` dentro de su orden, o se reemplazan por otras que la Facultad considere igual de relevantes y con más material disponible.
