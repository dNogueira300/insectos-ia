# Reporte de particionado

Total de imágenes: **38760**

| Split | Imágenes |
| --- | ---: |
| train | 26811 |
| val | 6109 |
| test | 5840 |

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
| Blattodea/Blaberidae | 409 img / 302 obs | 87 img / 59 obs | 88 img / 62 obs |
| Blattodea/Blattidae | 416 img / 305 obs | 88 img / 58 obs | 89 img / 64 obs |
| Blattodea/_sin_familia | 831 img / 512 obs | 176 img / 109 obs | 178 img / 104 obs |
| Coleoptera/Carabidae | 408 img / 248 obs | 87 img / 44 obs | 99 img / 10 obs |
| Coleoptera/Cerambycidae | 420 img / 180 obs | 89 img / 47 obs | 90 img / 51 obs |
| Coleoptera/Chrysomelidae | 415 img / 212 obs | 88 img / 37 obs | 89 img / 44 obs |
| Coleoptera/Coccinellidae | 411 img / 203 obs | 87 img / 40 obs | 88 img / 43 obs |
| Coleoptera/Curculionidae | 399 img / 187 obs | 84 img / 43 obs | 116 img / 7 obs |
| Coleoptera/Scarabaeidae | 418 img / 258 obs | 88 img / 48 obs | 89 img / 42 obs |
| Coleoptera/_sin_familia | 823 img / 315 obs | 174 img / 60 obs | 176 img / 59 obs |
| Dermaptera/_sin_familia | 831 img / 545 obs | 176 img / 105 obs | 178 img / 108 obs |
| Diptera/Anthomyiidae | 418 img / 240 obs | 89 img / 50 obs | 90 img / 43 obs |
| Diptera/Culicidae | 418 img / 202 obs | 89 img / 43 obs | 90 img / 23 obs |
| Diptera/Drosophilidae | 417 img / 200 obs | 88 img / 35 obs | 89 img / 20 obs |
| Diptera/Tephritidae | 418 img / 226 obs | 89 img / 54 obs | 90 img / 43 obs |
| Diptera/_sin_familia | 839 img / 204 obs | 177 img / 36 obs | 180 img / 37 obs |
| Hemiptera/Aphididae | 421 img / 232 obs | 89 img / 51 obs | 90 img / 48 obs |
| Hemiptera/Cicadellidae | 420 img / 143 obs | 89 img / 25 obs | 90 img / 28 obs |
| Hemiptera/Coreidae | 382 img / 190 obs | 81 img / 45 obs | 82 img / 44 obs |
| Hemiptera/Pentatomidae | 418 img / 227 obs | 89 img / 37 obs | 90 img / 43 obs |
| Hemiptera/Reduviidae | 418 img / 214 obs | 88 img / 32 obs | 89 img / 46 obs |
| Hemiptera/_sin_familia | 829 img / 346 obs | 175 img / 72 obs | 177 img / 71 obs |
| Hymenoptera/Apidae | 413 img / 157 obs | 87 img / 24 obs | 89 img / 25 obs |
| Hymenoptera/Chalcididae | 183 img / 125 obs | 39 img / 28 obs | 39 img / 25 obs |
| Hymenoptera/Formicidae | 390 img / 184 obs | 83 img / 22 obs | 84 img / 38 obs |
| Hymenoptera/Ichneumonidae | 420 img / 227 obs | 89 img / 40 obs | 90 img / 46 obs |
| Hymenoptera/Vespidae | 417 img / 170 obs | 88 img / 36 obs | 89 img / 39 obs |
| Hymenoptera/_sin_familia | 828 img / 300 obs | 175 img / 67 obs | 177 img / 67 obs |
| Isoptera/Heterotermitidae | 389 img / 155 obs | 83 img / 51 obs | 84 img / 62 obs |
| Isoptera/Kalotermitidae | 412 img / 318 obs | 87 img / 60 obs | 88 img / 63 obs |
| Isoptera/Termitidae | 233 img / 167 obs | 50 img / 32 obs | 50 img / 34 obs |
| Isoptera/_sin_familia | 704 img / 462 obs | 149 img / 90 obs | 151 img / 95 obs |
| Lepidoptera/Noctuidae | 372 img / 79 obs | 98 img / 10 obs | 125 img / 3 obs |
| Lepidoptera/Papilionidae | 410 img / 117 obs | 87 img / 23 obs | 88 img / 21 obs |
| Lepidoptera/Pieridae | 411 img / 111 obs | 87 img / 14 obs | 91 img / 8 obs |
| Lepidoptera/Pyralidae | 404 img / 96 obs | 105 img / 10 obs | 87 img / 16 obs |
| Lepidoptera/Sphingidae | 418 img / 148 obs | 89 img / 25 obs | 90 img / 38 obs |
| Lepidoptera/_sin_familia | 821 img / 94 obs | 201 img / 3 obs | 175 img / 13 obs |
| Mantodea/_sin_familia | 838 img / 520 obs | 177 img / 97 obs | 179 img / 104 obs |
| Neuroptera/_sin_familia | 836 img / 387 obs | 177 img / 75 obs | 179 img / 82 obs |
| Odonata/Aeshnidae | 299 img / 145 obs | 235 img / 3 obs | 64 img / 24 obs |
| Odonata/Calopterygidae | 420 img / 198 obs | 89 img / 16 obs | 90 img / 35 obs |
| Odonata/Coenagrionidae | 348 img / 49 obs | 174 img / 3 obs | 75 img / 13 obs |
| Odonata/Gomphidae | 365 img / 90 obs | 154 img / 2 obs | 81 img / 9 obs |
| Odonata/Libellulidae | 430 img / 49 obs | 72 img / 12 obs | 95 img / 8 obs |
| Odonata/_sin_familia | 812 img / 147 obs | 208 img / 5 obs | 174 img / 29 obs |
| Orthoptera/Acrididae | 413 img / 189 obs | 87 img / 37 obs | 88 img / 36 obs |
| Orthoptera/Gryllidae | 406 img / 252 obs | 86 img / 56 obs | 87 img / 48 obs |
| Orthoptera/Tettigoniidae | 413 img / 233 obs | 88 img / 50 obs | 89 img / 40 obs |
| Orthoptera/_sin_familia | 835 img / 455 obs | 177 img / 87 obs | 179 img / 94 obs |
| Phasmida/_sin_familia | 836 img / 475 obs | 177 img / 101 obs | 179 img / 104 obs |
| Psocodea/_sin_familia | 838 img / 301 obs | 177 img / 65 obs | 179 img / 63 obs |
| Thysanoptera/_sin_familia | 318 img / 163 obs | 67 img / 25 obs | 68 img / 7 obs |

## Alerta: clases cuyo test depende de un solo fotógrafo

Ninguna clase depende de un único fotógrafo en su conjunto de test.

## Observaciones sin fotógrafo identificado

No hubo observaciones sin fotógrafo identificado.
