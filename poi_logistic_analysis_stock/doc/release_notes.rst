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

Versión 0.1
-----------

Se realizaron los siguientes cambios:

* La factura se genera de forma automática a través de la función create_invoice (ejemplo)
* La factura genera el asiento de forma manual a través del botón Crear Asiento (ejemplo)

Versión 0.2
-----------

Se realizaron los siguientes cambios:

* La factura fue reemplazada por el nuevo objeto nueva.factura (ejemplo)

Versión 1.0
-----------
El módulo se encuentra listo para producción, con las siguientes características:
* Revisa el módulo de stock actual
* Se agregó la dependencia de poi_materialized view

Versión 1.1
-----------

Se realizaron los siguientes cambios:

* La función create_invoice tenía un bug en el caso de que el cliente esté vacío, se agregó la validación. (ejemplo)

Versión 1.2
-----------

Se realizaron los siguientes cambios:

* La función create_invoice necesita una validación sobre moneda, se agregó la validación en la función (ejemplo)

Versión 2.0
-----------

El módulo se encuentra en la versión 2.0 con las siguientes novedades:

* Los asientos se generan con una referencia automática por factura (ejemplo)

ToDo:

* Las facturas en pdf, deberían generarse con un número de documento. (ejemplo)
este