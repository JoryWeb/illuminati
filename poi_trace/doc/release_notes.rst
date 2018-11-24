.. Poiesis Odoo documentation, created by
   Grover Menacho on Mon Nov 23 18:19:55 2015.
   Los Release Notes deberán seguir el versionamiento de la siguiente forma del 0.1 al 0.x (ej. 0.25), son versiones alfa y/o beta.
Las versiones alfa, únicamente serán probadas por el desarrollador.
Las versiones beta, serán probadas tanto por el desarrollador como por los funcionales
Las versiones 1.0 - X.0 tendrán nuevas características del módulo.
Las versiones X.1 - X.x tendrán arreglo de funciones, validaciones, etc.

.. _module:

.. queue:: module/series

Release Notes
=============

Versión 1.0
-----------

El módulo se encuentra listo para producción, con las siguientes características:

* Agrega la fuente a cada asiento con el fin de tener una relación con su orígen

Versión 2.0
-----------

El módulo se encuentra en la versión 2.0 con las siguientes novedades:

* Los asientos generados automáticamente, no se podrán borrar

Versión 2.1
-----------

Se modificaron las siguientes partes:

* Los asientos generados automáticamente, tienen un campo de tipo booleano. Este campo permitirá editar el asiento a pesar de ser automático.
* Se creó el asistente de reversiones (revertir y arreglar)

TODO:
* Romper conciliaciones a través del asistente