{
    'name': 'Costo en Factura de venta',
    'version': '9.0.1.0',
    'category': 'Account',
    'summary': 'Contabiliza costo de venta en Factura y no en Albaran',
    'description': """
Incorpora las siguientes funcionalidades para una contabilidad anglo-sajona parcial:

* Cuenta contable puente parametrizable en Categoría de producto y Producto
* Al contabilizar una factura de venta, agrega dos líneas para contabilizar el costo de venta contra una cuenta puente
* Al contabilizar la salida de Productos a cliente, baja Inventarios contra la misma cuenta puente

CONSIDERACIONES
---------------
* Este modulo imita parcialmente la funcionalidad nativa de la configuración 'anglo_saxon_accounting' que se encuentra en Company. Por ende no debería usarse en combinación.

ToDo
----
* Impedir por desarrollo que este módulo y la configuración anglo_saxon_accounting coexistan al mismo tiempo
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['stock_account', 'stock_landed_costs'],
    'data': ['views/product_view.xml'],
    'installable': True,
    'active': True,
    'application': True,
}