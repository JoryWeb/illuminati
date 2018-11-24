{
    'name': 'Sale Report Advanced',
    'version': '11.0',
    'category': 'Sales',
    'sequence': 75,
    'summary': 'Campos para Impresion Segun la Moneda.',
    'description': """
Sale Report Advanced
===================
Agrega Campos al Objeto de sale.order(OV), para manejar el tipo de cambio base.
    """,
    'depends': [
        'sale',
    ],
    'data': [
        'views/sale.xml',
    ],

    'installable': True,
    'qweb': [],
}
