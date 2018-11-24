# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Product Related',
    'version': '1.0.0',
    'category': 'Product',
    'sequence': 20,
    'summary': 'Products Related',
    'description': """
Product Related
===============

    """,
    'depends': ['product'],
    'data': [
        'views/product_view.xml',
    ],
    'demo': [

    ],
    'installable': False,
    'application': True,
    'auto_install': False,
}
