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

Versión 1.1
-----------

Se realizaron los siguientes cambios:

* Adopción de la norma 2016 de Impuestos Nacionales
* Rediseño de la generación de Libros de Compra y Venta mediante un wizard que mejora performance
* Ajustes a la facturación con código QR


Versión 1.0
-----------

El módulo se encuentra listo para producción, con las siguientes características:

* Campos en Partners: NIT y Razón social (se copian en la creación de una factura)
* Campo de CI en contactos de Partner
* Cálculo recurrente del IT
* Cálculo de Asientos según ajuste por inflación (UFV y USD)
* Libros de Compra y Venta
* Bancarización
* Notas de crédito según ley
* Comprabantes de Compra simplificados
* Arreglo para usar tasa de impuesto no inversa (13% exacto)
* Campos en Producto: Último precio de compra, Código antiguo
* Uso de Dosificaciones para facturación (sin código de control, sólo numeración y nro de orden)
* Corrección de la generación de asientos con moneda secundaria sobre la factura
* Seguimiento de Facturas para generar Albaran y Pago
* Adicion de campos por tipo de pago en ventas
* Configuraciones generales para instalar los módulos periféricos a esta
* Facturación de Pagos adelantados según ley

Versión 1.1
-----------

El módulo presenta los siguientes cambios:

* El módulo añade la dependencia del Módulo de Tiendas
* El módulo se fusiona con poi_bol_shop (la instalación del mismo no es requerida)

