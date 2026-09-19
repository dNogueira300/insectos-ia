# Reporte de particionado

Total de imágenes: **34360**

| Split | Imágenes |
| --- | ---: |
| train | 24032 |
| val | 5163 |
| test | 5165 |

Se aplicó un **tope de 20 imágenes por fotógrafo y clase**: quedaron fuera 4400 imágenes, para que unos pocos fotógrafos muy activos no dominen ni el aprendizaje ni el examen.

El particionado agrupa por **observador**: ninguna persona aparece en dos splits. Es la defensa contra la fuga de datos descrita en el diseño (§7). La asignación se estratifica además por clase, para que los fotógrafos de una misma familia no caigan todos del mismo lado.

De los observadores de esta corrida, **0** conservan el split que ya tenían y **7974** se repartieron ahora. La asignación vive en `asignacion_observadores.yaml`, junto a los CSV de los splits: es lo que mantiene el conjunto de examen igual entre corridas. No es un archivo temporal.

## Decisiones de admisión de familias

| Familia | Decisión |
| --- | --- |
| Acrididae | admitida |
| Aeshnidae | admitida |
| Anthomyiidae | admitida |
| Aphididae | admitida |
| Apidae | admitida |
| Blaberidae | admitida |
| Blattidae | admitida |
| Calopterygidae | admitida |
| Carabidae | admitida |
| Cerambycidae | admitida |
| Chalcididae | admitida |
| Chrysomelidae | admitida |
| Cicadellidae | admitida |
| Coccinellidae | admitida |
| Coenagrionidae | admitida |
| Coreidae | admitida |
| Culicidae | admitida |
| Curculionidae | admitida |
| Drosophilidae | admitida |
| Formicidae | admitida |
| Gomphidae | admitida |
| Gryllidae | admitida |
| Heterotermitidae | admitida |
| Ichneumonidae | admitida |
| Kalotermitidae | admitida |
| Libellulidae | admitida |
| Noctuidae | admitida |
| Papilionidae | admitida |
| Pentatomidae | admitida |
| Pieridae | admitida |
| Pyralidae | admitida |
| Reduviidae | admitida |
| Scarabaeidae | admitida |
| Sphingidae | admitida |
| Tephritidae | admitida |
| Termitidae | admitida |
| Tettigoniidae | admitida |
| Vespidae | admitida |

Todas las familias alcanzaron el umbral.

## Distribución por clase

Cada celda muestra **imágenes / observadores distintos**: si el número de observadores es bajo —sobre todo en test— el número de imágenes por sí solo engaña sobre qué tan bien evaluada está esa clase.

| Clase | train | val | test |
| --- | ---: | ---: | ---: |
| Blattodea/Blaberidae | 408 img / 303 obs | 88 img / 62 obs | 88 img / 58 obs |
| Blattodea/Blattidae | 415 img / 307 obs | 89 img / 63 obs | 89 img / 57 obs |
| Blattodea/_sin_familia | 827 img / 520 obs | 177 img / 97 obs | 177 img / 108 obs |
| Coleoptera/Carabidae | 369 img / 219 obs | 80 img / 41 obs | 80 img / 42 obs |
| Coleoptera/Cerambycidae | 407 img / 194 obs | 87 img / 43 obs | 87 img / 41 obs |
| Coleoptera/Chrysomelidae | 414 img / 205 obs | 89 img / 49 obs | 89 img / 39 obs |
| Coleoptera/Coccinellidae | 405 img / 205 obs | 87 img / 42 obs | 87 img / 39 obs |
| Coleoptera/Curculionidae | 326 img / 172 obs | 70 img / 33 obs | 70 img / 32 obs |
| Coleoptera/Scarabaeidae | 413 img / 252 obs | 89 img / 46 obs | 89 img / 50 obs |
| Coleoptera/_sin_familia | 800 img / 311 obs | 172 img / 64 obs | 172 img / 59 obs |
| Dermaptera/_sin_familia | 810 img / 540 obs | 174 img / 111 obs | 174 img / 107 obs |
| Diptera/Anthomyiidae | 416 img / 241 obs | 90 img / 46 obs | 90 img / 46 obs |
| Diptera/Culicidae | 360 img / 197 obs | 78 img / 41 obs | 78 img / 30 obs |
| Diptera/Drosophilidae | 363 img / 188 obs | 78 img / 33 obs | 78 img / 34 obs |
| Diptera/Tephritidae | 411 img / 234 obs | 89 img / 42 obs | 88 img / 47 obs |
| Diptera/_sin_familia | 729 img / 200 obs | 156 img / 41 obs | 157 img / 36 obs |
| Hemiptera/Aphididae | 399 img / 239 obs | 86 img / 47 obs | 86 img / 45 obs |
| Hemiptera/Cicadellidae | 380 img / 138 obs | 82 img / 29 obs | 82 img / 29 obs |
| Hemiptera/Coreidae | 381 img / 205 obs | 82 img / 33 obs | 82 img / 41 obs |
| Hemiptera/Pentatomidae | 417 img / 216 obs | 90 img / 49 obs | 90 img / 42 obs |
| Hemiptera/Reduviidae | 397 img / 203 obs | 85 img / 42 obs | 86 img / 47 obs |
| Hemiptera/_sin_familia | 809 img / 350 obs | 174 img / 74 obs | 174 img / 65 obs |
| Hymenoptera/Apidae | 371 img / 152 obs | 80 img / 31 obs | 80 img / 23 obs |
| Hymenoptera/Chalcididae | 183 img / 129 obs | 39 img / 20 obs | 39 img / 29 obs |
| Hymenoptera/Formicidae | 379 img / 184 obs | 81 img / 29 obs | 82 img / 31 obs |
| Hymenoptera/Ichneumonidae | 419 img / 225 obs | 90 img / 46 obs | 90 img / 42 obs |
| Hymenoptera/Vespidae | 401 img / 171 obs | 86 img / 37 obs | 86 img / 37 obs |
| Hymenoptera/_sin_familia | 728 img / 316 obs | 156 img / 63 obs | 156 img / 55 obs |
| Isoptera/Heterotermitidae | 253 img / 187 obs | 55 img / 40 obs | 55 img / 41 obs |
| Isoptera/Kalotermitidae | 411 img / 311 obs | 88 img / 65 obs | 88 img / 65 obs |
| Isoptera/Termitidae | 233 img / 173 obs | 50 img / 32 obs | 50 img / 28 obs |
| Isoptera/_sin_familia | 658 img / 459 obs | 141 img / 92 obs | 141 img / 96 obs |
| Lepidoptera/Noctuidae | 278 img / 64 obs | 60 img / 18 obs | 60 img / 10 obs |
| Lepidoptera/Papilionidae | 373 img / 118 obs | 80 img / 21 obs | 80 img / 22 obs |
| Lepidoptera/Pieridae | 360 img / 100 obs | 77 img / 17 obs | 77 img / 16 obs |
| Lepidoptera/Pyralidae | 332 img / 87 obs | 72 img / 18 obs | 72 img / 17 obs |
| Lepidoptera/Sphingidae | 397 img / 158 obs | 86 img / 29 obs | 86 img / 24 obs |
| Lepidoptera/_sin_familia | 467 img / 80 obs | 100 img / 16 obs | 100 img / 14 obs |
| Mantodea/_sin_familia | 817 img / 510 obs | 175 img / 108 obs | 175 img / 103 obs |
| Neuroptera/_sin_familia | 813 img / 386 obs | 174 img / 81 obs | 174 img / 77 obs |
| Odonata/Aeshnidae | 267 img / 126 obs | 58 img / 20 obs | 57 img / 26 obs |
| Odonata/Calopterygidae | 383 img / 181 obs | 82 img / 35 obs | 82 img / 33 obs |
| Odonata/Coenagrionidae | 173 img / 49 obs | 37 img / 10 obs | 38 img / 6 obs |
| Odonata/Gomphidae | 225 img / 79 obs | 48 img / 5 obs | 48 img / 17 obs |
| Odonata/Libellulidae | 178 img / 54 obs | 38 img / 9 obs | 38 img / 6 obs |
| Odonata/_sin_familia | 483 img / 136 obs | 104 img / 25 obs | 104 img / 20 obs |
| Orthoptera/Acrididae | 410 img / 191 obs | 88 img / 39 obs | 88 img / 32 obs |
| Orthoptera/Gryllidae | 405 img / 258 obs | 87 img / 49 obs | 87 img / 49 obs |
| Orthoptera/Tettigoniidae | 401 img / 235 obs | 86 img / 46 obs | 86 img / 42 obs |
| Orthoptera/_sin_familia | 833 img / 459 obs | 179 img / 86 obs | 179 img / 91 obs |
| Phasmida/_sin_familia | 770 img / 483 obs | 165 img / 96 obs | 165 img / 101 obs |
| Psocodea/_sin_familia | 705 img / 296 obs | 151 img / 68 obs | 151 img / 65 obs |
| Thysanoptera/_sin_familia | 270 img / 143 obs | 58 img / 26 obs | 58 img / 26 obs |

## Alerta: clases cuyo test depende de un solo fotógrafo

Ninguna clase depende de un único fotógrafo en su conjunto de test.

## Observaciones sin fotógrafo identificado

No hubo observaciones sin fotógrafo identificado.
