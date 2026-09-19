# Reporte del filtro de contenido

- Imágenes de entrada: **39542**
- Conservadas: **38760**
- Umbral de puntaje: **0.5**

El puntaje es la probabilidad, según un modelo de visión zero-shot, de que la foto muestre un insecto visible. Lo descartado queda listado con su puntaje en `descartes_contenido.csv`; las imágenes no se borran.

| Clase | Entrada | Descartadas | % |
| --- | ---: | ---: | ---: |
| Blattodea/Blaberidae | 599 | 15 | 3% |
| Blattodea/Blattidae | 598 | 5 | 1% |
| Blattodea/_sin_familia | 1195 | 10 | 1% |
| Coleoptera/Carabidae | 600 | 6 | 1% |
| Coleoptera/Cerambycidae | 599 | 0 | 0% |
| Coleoptera/Chrysomelidae | 597 | 5 | 1% |
| Coleoptera/Coccinellidae | 592 | 6 | 1% |
| Coleoptera/Curculionidae | 599 | 0 | 0% |
| Coleoptera/Scarabaeidae | 599 | 4 | 1% |
| Coleoptera/_sin_familia | 1191 | 18 | 2% |
| Dermaptera/_sin_familia | 1194 | 9 | 1% |
| Diptera/Anthomyiidae | 597 | 0 | 0% |
| Diptera/Culicidae | 598 | 1 | 0% |
| Diptera/Drosophilidae | 596 | 2 | 0% |
| Diptera/Tephritidae | 598 | 1 | 0% |
| Diptera/_sin_familia | 1197 | 1 | 0% |
| Hemiptera/Aphididae | 600 | 0 | 0% |
| Hemiptera/Cicadellidae | 599 | 0 | 0% |
| Hemiptera/Coreidae | 549 | 4 | 1% |
| Hemiptera/Pentatomidae | 600 | 3 | 0% |
| Hemiptera/Reduviidae | 597 | 2 | 0% |
| Hemiptera/_sin_familia | 1198 | 17 | 1% |
| Hymenoptera/Apidae | 596 | 7 | 1% |
| Hymenoptera/Chalcididae | 261 | 0 | 0% |
| Hymenoptera/Formicidae | 599 | 42 | 7% |
| Hymenoptera/Ichneumonidae | 600 | 1 | 0% |
| Hymenoptera/Vespidae | 600 | 6 | 1% |
| Hymenoptera/_sin_familia | 1199 | 19 | 2% |
| Isoptera/Heterotermitidae | 600 | 44 | 7% |
| Isoptera/Kalotermitidae | 597 | 10 | 2% |
| Isoptera/Termitidae | 596 | 263 | 44% |
| Isoptera/_sin_familia | 1195 | 191 | 16% |
| Lepidoptera/Noctuidae | 597 | 2 | 0% |
| Lepidoptera/Papilionidae | 595 | 10 | 2% |
| Lepidoptera/Pieridae | 597 | 8 | 1% |
| Lepidoptera/Pyralidae | 597 | 1 | 0% |
| Lepidoptera/Sphingidae | 598 | 1 | 0% |
| Lepidoptera/_sin_familia | 1199 | 2 | 0% |
| Mantodea/_sin_familia | 1200 | 6 | 0% |
| Neuroptera/_sin_familia | 1196 | 4 | 0% |
| Odonata/Aeshnidae | 598 | 0 | 0% |
| Odonata/Calopterygidae | 600 | 1 | 0% |
| Odonata/Coenagrionidae | 597 | 0 | 0% |
| Odonata/Gomphidae | 600 | 0 | 0% |
| Odonata/Libellulidae | 599 | 2 | 0% |
| Odonata/_sin_familia | 1198 | 4 | 0% |
| Orthoptera/Acrididae | 595 | 7 | 1% |
| Orthoptera/Gryllidae | 598 | 19 | 3% |
| Orthoptera/Tettigoniidae | 597 | 7 | 1% |
| Orthoptera/_sin_familia | 1198 | 7 | 1% |
| Phasmida/_sin_familia | 1198 | 6 | 1% |
| Psocodea/_sin_familia | 1197 | 3 | 0% |
| Thysanoptera/_sin_familia | 453 | 0 | 0% |
