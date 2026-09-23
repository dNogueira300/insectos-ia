# Desempeño por clase — v3_b2_288

Conjunto: `datos\splits\test.csv` (5165 imágenes), resolución 288 px.

## Órdenes

| Clase | F1 | Imágenes | Confusión principal |
| --- | ---: | ---: | --- |
| Mantodea | 0.85 | 175 | Phasmida (6) |
| Phasmida | 0.86 | 165 | Mantodea (11) |
| Psocodea | 0.86 | 151 | Isoptera (7) |
| Thysanoptera | 0.86 | 58 | Hemiptera (4) |
| Hymenoptera | 0.87 | 533 | Diptera (15) |
| Hemiptera | 0.88 | 600 | Coleoptera (23) |
| Orthoptera | 0.90 | 440 | Hemiptera (9) |
| Neuroptera | 0.91 | 174 | Hymenoptera (5) |
| Isoptera | 0.91 | 334 | Hymenoptera (7) |
| Coleoptera | 0.91 | 674 | Hymenoptera (15) |
| Dermaptera | 0.91 | 174 | Isoptera (8) |
| Diptera | 0.92 | 491 | Hymenoptera (17) |
| Blattodea | 0.94 | 354 | Coleoptera (10) |
| Lepidoptera | 0.95 | 475 | Hymenoptera (6) |
| Odonata | 0.97 | 367 | Lepidoptera (4) |

## Familias

Una familia de otro orden como "confusión principal" suele indicar que falló el orden y el enmascaramiento jerárquico forzó la familia dentro del orden equivocado.

| Clase | F1 | Imágenes | Confusión principal |
| --- | ---: | ---: | --- |
| Termitidae | 0.67 | 50 | Heterotermitidae (6) |
| Formicidae | 0.72 | 82 | Termitidae (6) |
| Heterotermitidae | 0.74 | 55 | Kalotermitidae (7) |
| Acrididae | 0.75 | 88 | Tettigoniidae (5) |
| Reduviidae | 0.80 | 86 | Coreidae (6) |
| Cerambycidae | 0.80 | 87 | Acrididae (4) |
| Tettigoniidae | 0.81 | 86 | Acrididae (8) |
| Chrysomelidae | 0.82 | 89 | Coccinellidae (5) |
| Aphididae | 0.84 | 86 | Acrididae (6) |
| Kalotermitidae | 0.85 | 88 | Heterotermitidae (6) |
| Pentatomidae | 0.85 | 90 | Scarabaeidae (3) |
| Scarabaeidae | 0.85 | 89 | Apidae (3) |
| Curculionidae | 0.86 | 70 | Cerambycidae (4) |
| Apidae | 0.86 | 80 | Coccinellidae (3) |
| Coccinellidae | 0.86 | 87 | Chrysomelidae (2) |
| Coreidae | 0.88 | 82 | Reduviidae (3) |
| Noctuidae | 0.89 | 60 | Pyralidae (3) |
| Tephritidae | 0.89 | 88 | Acrididae (2) |
| Blaberidae | 0.89 | 88 | Scarabaeidae (3) |
| Libellulidae | 0.89 | 38 | Gomphidae (2) |
| Chalcididae | 0.90 | 39 | Aphididae (1) |
| Aeshnidae | 0.90 | 57 | Gomphidae (2) |
| Pyralidae | 0.90 | 72 | Acrididae (2) |
| Gryllidae | 0.91 | 87 | Tettigoniidae (4) |
| Vespidae | 0.91 | 86 | Formicidae (2) |
| Ichneumonidae | 0.91 | 90 | Acrididae (3) |
| Culicidae | 0.92 | 78 | Aphididae (2) |
| Drosophilidae | 0.92 | 78 | Anthomyiidae (2) |
| Papilionidae | 0.93 | 80 | Pieridae (2) |
| Gomphidae | 0.93 | 48 | Libellulidae (2) |
| Pieridae | 0.93 | 77 | Papilionidae (4) |
| Blattidae | 0.93 | 89 | Blaberidae (7) |
| Carabidae | 0.94 | 80 | Cerambycidae (1) |
| Anthomyiidae | 0.94 | 90 | Drosophilidae (2) |
| Coenagrionidae | 0.95 | 38 | Carabidae (1) |
| Sphingidae | 0.95 | 86 | Noctuidae (2) |
| Cicadellidae | 0.96 | 82 | Acrididae (1) |
| Calopterygidae | 0.98 | 82 | Aeshnidae (2) |

## Cobertura contra confianza (familias)

| Umbral | Responde | Acierta cuando responde |
| --- | ---: | ---: |
| 0.0 | 100% | 87.4% |
| 0.5 | 96% | 90.1% |
| 0.6 | 93% | 92.0% |
| 0.7 | 89% | 93.6% |
| 0.8 | 84% | 95.1% |
| 0.9 | 75% | 96.7% |
