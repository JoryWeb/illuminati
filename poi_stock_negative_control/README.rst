.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Control de Negativos
=======================================

Funcionalidad que deshabilita el botón "forzar disponibilidad" en los pickings
de esta forma se evita generar negativos y aplicar mas la función de comprobar
disponibilidad.

Adicionalmente se asigna por usuario el permiso en caso de querer realizar un
control por usuario

Funciones adicionales
=====================

Parametrizaciones por ubicación lo cual esconde el botón
Usar la configguración del usuario el parametro "Habilitar Forzar disponibilidad"
en el dato maestro de de usuario

Notas
===========
No se pueden crear movimientos de existencia sueltos en odoo 9
lo cual garantiza que el inventario no se mueva si no es a traves de un picking
o albaran de salida

Mejoras
=======
- Autorización de reservas por cada registro
- Autorización por usuario
Credits
=======

Contributors
------------

* Miguel Angel Callisaya Mamani <miguel.callisaya@poeisisconsulting.com>

Maintainer
----------
   :alt: Poiesis consulting
   :target: http://www.poiesisconsulting.com


