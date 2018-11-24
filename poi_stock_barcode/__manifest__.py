# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Picking Barcode Scanner',
    'version': '1.0.0',
    'category': 'Stock',
    'sequence': 20,
    'summary': 'Código de barras',
    'description': """
Barcode Picking
===============
Se puede realizar la confirmación de cantidades a transferir sobre los albaranes de transferencia
interna y albaranes de salida
Es importante mantener el cursor sobre los campos
de codigo de barra para la aplicación del lector de codigo de barras

Utilizar un lector de código de barras USB y con digitación QWERTY
    """,
    'depends': ['stock'],
    'data': [
        'views/stock_view.xml',
        #'security/ir.model.access.csv',
    ],
    'demo': [

    ],
    'installable': False,
    'application': True,
    'auto_install': False,
}
