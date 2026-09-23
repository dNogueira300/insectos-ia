# Desempeño por clase — v4_convnext_t_288

Conjunto: `datos/splits/test.csv` (5165 imágenes), resolución 288 px.

## Órdenes

| Clase | F1 | Imágenes | Confusión principal |
| --- | ---: | ---: | --- |
| Thysanoptera | 0.86 | 58 | Coleoptera (2) |
| Mantodea | 0.87 | 175 | Orthoptera (7) |
| Phasmida | 0.90 | 165 | Mantodea (8) |
| Psocodea | 0.92 | 151 | Diptera (5) |
| Hymenoptera | 0.93 | 533 | Isoptera (8) |
| Hemiptera | 0.94 | 600 | Coleoptera (12) |
| Orthoptera | 0.94 | 440 | Blattodea (4) |
| Isoptera | 0.94 | 334 | Hymenoptera (6) |
| Neuroptera | 0.94 | 174 | Mantodea (3) |
| Diptera | 0.95 | 491 | Hymenoptera (14) |
| Dermaptera | 0.95 | 174 | Isoptera (4) |
| Coleoptera | 0.95 | 674 | Hemiptera (7) |
| Blattodea | 0.97 | 354 | Coleoptera (2) |
| Odonata | 0.98 | 367 | Orthoptera (2) |
| Lepidoptera | 0.98 | 475 | Coleoptera (2) |

## Familias

Una familia de otro orden como "confusión principal" suele indicar que falló el orden y el enmascaramiento jerárquico forzó la familia dentro del orden equivocado.

| Clase | F1 | Imágenes | Confusión principal |
| --- | ---: | ---: | --- |
| Termitidae | 0.78 | 50 | Heterotermitidae (5) |
| Acrididae | 0.81 | 88 | Tettigoniidae (2) |
| Formicidae | 0.82 | 82 | Acrididae (4) |
| Heterotermitidae | 0.83 | 55 | Kalotermitidae (5) |
| Reduviidae | 0.86 | 86 | Acrididae (3) |
| Tettigoniidae | 0.88 | 86 | Acrididae (7) |
| Apidae | 0.88 | 80 | Vespidae (3) |
| Chrysomelidae | 0.89 | 89 | Acrididae (2) |
| Scarabaeidae | 0.89 | 89 | Chrysomelidae (5) |
| Kalotermitidae | 0.91 | 88 | Heterotermitidae (5) |
| Cerambycidae | 0.92 | 87 | Acrididae (4) |
| Noctuidae | 0.92 | 60 | Pyralidae (6) |
| Curculionidae | 0.92 | 70 | Cerambycidae (3) |
| Pyralidae | 0.92 | 72 | Sphingidae (3) |
| Carabidae | 0.93 | 80 | Cerambycidae (1) |
| Blaberidae | 0.93 | 88 | Blattidae (2) |
| Gryllidae | 0.93 | 87 | Acrididae (2) |
| Tephritidae | 0.93 | 88 | Drosophilidae (2) |
| Chalcididae | 0.94 | 39 | Acrididae (1) |
| Libellulidae | 0.94 | 38 | Aeshnidae (1) |
| Vespidae | 0.94 | 86 | Ichneumonidae (2) |
| Aeshnidae | 0.94 | 57 | Acrididae (1) |
| Coreidae | 0.94 | 82 | Reduviidae (4) |
| Papilionidae | 0.94 | 80 | Apidae (1) |
| Aphididae | 0.94 | 86 | Acrididae (2) |
| Pentatomidae | 0.94 | 90 | Acrididae (4) |
| Coenagrionidae | 0.95 | 38 | Calopterygidae (1) |
| Blattidae | 0.95 | 89 | Blaberidae (3) |
| Cicadellidae | 0.95 | 82 | Acrididae (2) |
| Coccinellidae | 0.95 | 87 | Acrididae (1) |
| Ichneumonidae | 0.96 | 90 | Blattidae (1) |
| Gomphidae | 0.96 | 48 | Acrididae (1) |
| Anthomyiidae | 0.96 | 90 | Aeshnidae (1) |
| Drosophilidae | 0.96 | 78 | Anthomyiidae (1) |
| Sphingidae | 0.97 | 86 | Papilionidae (1) |
| Pieridae | 0.97 | 77 | Papilionidae (3) |
| Culicidae | 0.97 | 78 | — |
| Calopterygidae | 0.98 | 82 | Coenagrionidae (1) |

## Cobertura contra confianza (familias)

| Umbral | Responde | Acierta cuando responde |
| --- | ---: | ---: |
| 0.0 | 100% | 92.1% |
| 0.5 | 98% | 93.6% |
| 0.6 | 96% | 94.4% |
| 0.7 | 94% | 95.5% |
| 0.8 | 92% | 96.2% |
| 0.9 | 88% | 97.3% |
