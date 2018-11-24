
{
    'name': 'Dato Maestro del Cliente Nuevos Campos',
    'version': '11.0',
    'category': 'Sales',
    'sequence': 76,
    'summary': 'Se añadieron nuevos campos al dato maestro del cliente.',
    'description': """
Partner Advanced Poiesis
==========================
    Campos Avanzados al modelo del cliente/proveedor
    Se añadieron nuevos campos al dato maestro del cliente entre los cuales estan:
        - Estado Civil
        - Familia
        - Recomendado Por
    """,
    'depends': [
        'base',
    ],
    'data': [
        'views/res_partner_view.xml',

    ],

    'installable': True,
    'application': True,
    'qweb': [],
}
