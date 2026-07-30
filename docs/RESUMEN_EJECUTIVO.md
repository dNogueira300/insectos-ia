# Resumen ejecutivo — Sistema de identificación de insectos amazónicos

**Fecha:** 30 de julio de 2026
**Estado:** fase de datos construida y auditada. No lista para dar por cerrada.
**Repositorio:** https://github.com/dNogueira300/insectos-ia — rama `plan-01-fase-datos`

---

## Qué es este proyecto

Un sistema que, a partir de la fotografía de un insecto, propone a qué **orden** y a qué **familia** pertenece, y muestra la información biológica asociada: nombre común, cultivo al que afecta, tipo de daño e importancia económica.

El trabajo se dividió en tres etapas. Esta primera construye **la maquinaria que prepara los datos**: consigue las fotografías, las limpia, y las organiza de forma que el sistema pueda aprender de ellas sin engañarse a sí mismo. Las otras dos etapas —entrenar el modelo y construir la página web de consulta— están planificadas en detalle pero aún no ejecutadas.

## Qué se completó

Las nueve piezas de la etapa de datos están escritas y probadas: 129 pruebas automáticas, todas en verde. En concreto, el sistema ya sabe:

- **Consultar cuántas fotografías existen** de cada grupo de insectos en los repositorios científicos internacionales, antes de descargar nada.
- **Descargar esas fotografías** registrando de dónde vino cada una, quién la tomó y bajo qué licencia, que es una obligación legal.
- **Limpiar el material**: descartar duplicados, fotos demasiado pequeñas y archivos dañados.
- **Repartir las fotos** entre el material de aprendizaje y el de examen, con una precaución que se explica más abajo.
- **Validar la base de datos biológica** que llena el equipo de Agronomía, rechazando registros inconsistentes.
- **Recibir las fotografías de campo** que aporte la Facultad y comprobar que no se solapen con el material de aprendizaje.

## El primer resultado concreto: el censo

Se ejecutó el censo real contra los repositorios internacionales. El documento está en `docs/censo_disponibilidad.md` y es el insumo para la reunión de decisión.

**Los 15 órdenes de insectos superan holgadamente el mínimo necesario.** A nivel de orden no hay que descartar nada. Dos observaciones:

**Los trips (Thysanoptera) están al límite.** 487 fotografías disponibles en todo el mundo frente a un objetivo de 270. Pasa, pero con tan poco margen que al repartirlas entre aprendizaje y examen quedan muy pocas de cada lado. Como son una plaga agrícola relevante, conviene que el entomólogo decida si vale la pena incluirlos.

**Casi no hay material fotografiado en Perú.** Trips: 0. Efímeras: 2. Frigáneas: 3. Crisopas: 15. Esto no impide entrenar —el sistema aprenderá con fotografías de todo el mundo— pero sí anticipa que **habrá una diferencia entre lo bien que funcione con fotos de catálogo y lo bien que funcione con una foto tomada con celular en una parcela amazónica**. Medir esa diferencia honestamente es exactamente para lo que sirve el conjunto de fotografías de campo.

## Lo que está esperando a la Facultad

**La lista de familias.** Los 15 órdenes son un conjunto cerrado y estándar; se pudieron determinar sin consultar a nadie. Pero **qué familias de importancia económica interesan para la Amazonía peruana es una decisión del entomólogo**, y sin ella no se puede descargar el material definitivo: serían decenas de miles de imágenes contra una lista que puede cambiar.

Todo el código para hacerlo está escrito y probado. El día que se cierre esa lista, ejecutar la descarga es cuestión de configurar un archivo y dejar el proceso corriendo.

**La base de datos biológica necesita reconciliarse.** Se probó importar el Excel de la reunión y fue rechazado con tres errores: las familias *Apidae*, *Coccinellidae* y *Libellulidae* no figuran en la lista de clases del sistema. Los cuatro órdenes usados sí estaban. Ese rechazo es el comportamiento correcto —el sistema no acepta datos que no puede interpretar— y la lista de errores dice exactamente qué hay que poner de acuerdo.

## Sobre la calidad del trabajo

Cada una de las nueve piezas pasó por una revisión independiente, y varias necesitaron hasta cuatro rondas de corrección. Se detectaron y corrigieron problemas que no eran evidentes:

- **Dos casos en que el sistema destruía información buena antes de tener la nueva.** Al reimportar la base de datos biológica, si algo fallaba a mitad de camino se perdían los datos anteriores *y* los nuevos. Lo mismo con el registro de las fotografías descargadas: una interrupción a mitad de una descarga de horas podía borrar el registro de todo lo ya bajado, incluida la información de licencias sin la cual las imágenes no se pueden usar legalmente.

- **Una herramienta que podía borrar archivos personales.** El módulo de limpieza borra material obsoleto de su carpeta de trabajo. Si alguien escribía mal la ruta y apuntaba, por ejemplo, a su carpeta de Documentos, podía perder archivos. Se cerró tras cuatro rondas, cada una tapando una vía distinta.

- **Fotografías que desaparecían sin avisar.** Las fotos en formato de iPhone se descartaban en silencio. El escenario realista: la Facultad entrega 200 fotografías de campo, la pantalla dice "60 procesadas", y nadie se entera de que faltan 140 del único conjunto que mide la calidad real del sistema.

## Lo que falta antes de dar la etapa por cerrada

Una revisión final del conjunto completo —distinta de las revisiones pieza por pieza— encontró **cuatro problemas que solo se ven mirando cómo encajan los módulos entre sí**. Son reales y están medidos:

**1. El reparto de fotos no tiene en cuenta las familias.** Al separar el material de aprendizaje del de examen, el sistema equilibra el total pero no vigila que cada familia quede representada en ambos lados. En una simulación, **36 de cada 100 familias con material abundante quedaron marcadas como "sin datos suficientes"** cuando en realidad tenían 600 fotografías. Peor: el informe recomienda entonces "conseguir más imágenes", que es justo lo contrario de lo que hace falta. Esto afecta directamente al documento con el que la Facultad decidirá qué clases entran al sistema.

**2. La verificación de las fotos de campo se puede saltar sin darse cuenta.** Si el archivo con el que debe compararse no está donde se espera, el programa continúa, informa éxito y no avisa de nada. Esa verificación es la que garantiza que las fotos de examen no estén también en el material de aprendizaje.

**3. Repetir el reparto reorganiza las fotos.** Si el proceso se ejecuta dos veces —cosa que va a pasar, porque la lista de clases todavía va a cambiar— fotógrafos que estaban en el grupo de aprendizaje pasan al de examen y viceversa. Un modelo entrenado antes del cambio quedaría evaluado con material que ya había visto, y su calificación sería falsamente buena.

**4. Al descargar, las fotos de orden le quitan etiqueta a las de familia.** Un ajuste de dos líneas en el orden de las operaciones. Hoy provoca que fotografías correctamente identificadas hasta el nivel de familia se archiven como "familia desconocida", lo que agrava el problema 1.

Ninguno impide seguir trabajando, pero **los cuatro deben corregirse antes de considerar terminada la etapa de datos**, porque los cuatro afectan a la promesa central del proyecto: que la calificación final del sistema sea honesta.

También se recomendó añadir dos cosas que nadie pidió y que harán falta: un manual de uso que explique en qué orden se ejecutan las nueve herramientas, y un verificador que compruebe sobre los datos reales —no solo en pruebas— que no hay contaminación entre el material de aprendizaje y el de examen.

## Situación general

| | |
|---|---|
| Etapa de datos | Construida y auditada. Cuatro correcciones pendientes. |
| Entrenamiento del modelo | Planificado en detalle. Sin empezar. |
| Página web de consulta | Planificada en detalle. Sin empezar. |
| Bloqueo externo | La lista de familias del entomólogo. |

El proyecto está donde debería estar: la infraestructura funciona, sabemos con datos qué material hay disponible, y los problemas que quedan están identificados y medidos en lugar de escondidos.
