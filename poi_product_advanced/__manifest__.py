# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Product Advanced',
    'version': '2.0.0',
    'category': 'Product',
    'sequence': 20,
    'summary': 'Funciones avanzadas para producto',
    'description': """
Product Advanced
===============

- Atributos de producto
- Múltiples imágenes para Producto
- Links a fabricante y video
    """,
    'depends': ['product'],
    'data': [
        'views/product_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
