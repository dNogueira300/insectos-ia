# Resumen ejecutivo — Sistema de identificación de insectos amazónicos

**Fecha:** 19 de septiembre de 2026
**Estado:** la etapa de datos está **cerrada sobre el material real** y el **código del modelo está terminado y probado**. Falta el entrenamiento en Google Colab.
**Repositorio:** https://github.com/dNogueira300/insectos-ia (todo en la rama `main`)

---

## Qué es este proyecto

Un sistema que, a partir de la fotografía de un insecto, propone a qué **orden** y a qué **familia** pertenece, y muestra la información biológica asociada. El trabajo tiene tres etapas:

1. Preparar los datos.
2. Entrenar el modelo.
3. Construir la página web de consulta.

## Dónde estamos

|                                  |                                                                                    |
| -------------------------------- | ---------------------------------------------------------------------------------- |
| Lista de clases                  | **Cerrada.** 15 órdenes y 38 familias.                                             |
| Etapa de datos                   | **Cerrada.** 34 360 fotografías listas, repartidas y verificadas.                  |
| Código del modelo                | **Terminado.** 9 piezas, 316 pruebas automáticas en verde, prueba de punta a punta superada. |
| Entrenamiento                    | **Siguiente paso.** En Google Colab gratuito, con el cuaderno ya preparado.        |
| Página web de consulta           | Planificada en detalle. Sin empezar.                                               |

## La lista de clases quedó cerrada

El 3 de agosto la Facultad devolvió la ficha de requerimientos y las claves dicotómicas de la Dra. Aldi Guerra Teixeira. Con ese material se armó la lista y se comprobó con datos cuánto material fotográfico existe para cada clase.

- **15 órdenes**, los de la ficha. Las termitas (Isoptera) se tratan como un orden propio, tal como pide la entomóloga, aunque los repositorios internacionales ya las clasifican dentro de Blattodea. El sistema las separa al descargar para que ninguna foto quede con dos órdenes.
- **38 familias.** Salen de las claves, más cinco familias de Hemiptera y Coccinellidae, que entran **de forma provisional**: la ficha las proponía, pero todavía no tienen clave.
- **Cuatro familias descartadas**, con el dato que lo justifica:
  - _Agromyzidae_: 229 fotos de adultos, bajo el mínimo; casi todo el material son hojas minadas, no la mosca.
  - _Mastotermitidae_: 13 fotos; es una familia exclusiva de Australia.
  - _Rhinotermitidae_: 10 fotos; los repositorios la dividieron y su grueso pasó a _Heterotermitidae_, que entra en su lugar.
  - _Locustidae_: no existe como familia en las bases actuales; las langostas están dentro de _Acrididae_.

Al preparar la lista apareció un error serio en la versión de prueba del sistema: el identificador usado para la familia de las polillas _Noctuidae_ correspondía en realidad a los **ciempiés**. Si se hubiera descargado con él, esa clase se habría llenado de ciempiés. Quedó corregido.

## El material fotográfico

| Paso                                                         | Fotografías |
| ------------------------------------------------------------ | ----------: |
| Descargadas de iNaturalist, con licencia y autor registrados | 39 668      |
| Tras quitar duplicados                                       | 39 542      |
| Tras quitar fotos en las que no se ve el insecto             | 38 760      |
| Tras limitar el aporte de cada fotógrafo                     | **34 360**  |

Las 34 360 fotos son de **7 974 fotógrafos distintos** y se reparten así:

- **24 032 para aprendizaje**;
- **5 163 para ajuste**;
- **5 165 para el examen final**.

Ningún fotógrafo aparece en dos grupos: si sus fotos estuvieran en el aprendizaje y en el examen, el sistema parecería mejor de lo que es. **Las 38 familias alcanzaron el mínimo necesario.**

Dos pasos de esa tabla se agregaron en esta etapa, porque los datos reales mostraron problemas que no se veían en el plan:

- **Fotos sin insecto.** En la familia de termitas _Termitidae_, la mitad de las fotos eran montículos de tierra y paisajes, no termitas. Un modelo entrenado con eso aprendería que "montículo" es una familia. Ahora un modelo de visión revisa cada foto y descarta las que solo muestran nidos, montículos, agujeros o paisaje. En esa familia, lo que queda sin insecto bajó de la mitad a menos de una de cada diez.
- **Fotógrafos que dominan una familia.** En algunas familias, una sola persona aportaba casi la mitad de las fotos, y el examen de una familia de polillas dependía de solo 3 fotógrafos. Se limitó a 20 fotos por fotógrafo en cada clase. El mínimo de fotógrafos distintos en el examen subió de 3 a 6.

## Problemas encontrados y corregidos

Cada pieza se verificó contra los datos reales, no solo en pruebas. Estos fueron los hallazgos que importan:

- **El primer filtro de fotos descartaba insectos buenos.** Confundía insectos palo, polillas sobre corteza y colonias de pulgones con "ramas", "madera" y "plantas": llegó a descartar un tercio de una clase. Se detectó revisando a ojo lo descartado, se rediseñó y se volvió a comprobar. Ahora las fotos buenas perdidas fuera de las termitas son del orden de 0.2 %.
- **Una descarga de 15 horas no sobrevivía a un corte de internet.** Ahora reintenta sola, se puede pausar y retomar por partes, y al retomar no duplica fotos.
- **La verificación del modelo exportado dio una falsa alarma.** La prueba de punta a punta con datos reales mostró que la comprobación comparaba mal. Se corrigió para medir lo que importa: con fotos reales, el modelo exportado da la misma respuesta que el original en el 100 % de los casos.

## Cómo se va a entrenar

En **Google Colab gratuito**, desde una sola cuenta. El cuaderno de Colab ya está listo: basta con subir a Google Drive el paquete de datos (un solo archivo) y ejecutar todas las celdas.

- Colab gratuito corta las sesiones sin aviso. El entrenamiento **guarda su avance en Drive al terminar cada vuelta** y, si se corta, continúa donde quedó al volver a ejecutar el cuaderno. Como mucho se pierde una vuelta.
- El tiempo estimado es de una a dos horas.
- Al terminar produce tres cosas: el modelo listo para la página web, sus métricas y un informe de evaluación.

## Lo que está esperando a la Facultad

- **Confirmar las familias provisionales:** las cinco de Hemiptera y Coccinellidae. Hoy están en el sistema, pero no tienen clave dicotómica.
- **La meta de precisión.** La ficha pide 99 % tanto en órdenes como en familias y no acepta recortar familias. Es una meta que ningún sistema de este tipo alcanza con fotos de campo. Conviene acordar por escrito una meta realista antes de presentar resultados, para que no se lean como un incumplimiento. El sistema está diseñado para **decir "no estoy seguro"** y mostrar sus tres mejores opciones cuando duda, en vez de afirmar algo equivocado.
- **Fotografías de campo.** Sin fotos tomadas en parcelas amazónicas, la calificación final mide fotos de catálogo, que es la parte fácil. El informe de evaluación lo declara explícitamente. Con ese material se podría medir la calidad real en campo.

## Límites conocidos, declarados a propósito

- **Casi no hay material de Perú.** Solo alrededor del 0.5 % de las fotos (unas 170) fue tomado en el país. El sistema aprende con fotos de todo el mundo. Es de esperar una diferencia entre su desempeño con fotos de catálogo y con fotos de celular en campo.
- **Tres familias de libélulas y caballitos del diablo tienen poca diversidad de fotógrafos** en su examen o en su grupo de ajuste: 5 o 6 personas. Su calificación será menos confiable que la del resto. Se puede mejorar descargando más fotos de otros fotógrafos.
- **Licencias.** El 73 % de las fotos tiene licencia **no comercial**. Es válido para un proyecto académico y de responsabilidad social. Si el sistema llegara a tener un uso comercial, habría que revisarlo; la licencia de cada foto está registrada.
- **Cinco familias quedaron justas en cantidad de material:** _Chalcididae_, _Termitidae_ y tres de libélulas.

## Próximos pasos

1. Subir el paquete de datos a Google Drive y entrenar en Colab.
2. Revisar el informe de evaluación: dónde acierta y dónde se confunde el modelo.
3. Reunión con la Facultad: familias provisionales, meta de precisión y fotos de campo.
4. Construir la página web de consulta (tercera etapa).
