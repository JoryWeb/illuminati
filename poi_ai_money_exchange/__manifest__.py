{
    'name': 'Money Exchange',
    'version': '1.0',
    'category': 'Sales',
    'sequence': 75,
    'summary': 'Campos de totalizadores y por linea segun la moneda base.',
    'description': """
Account Invoice Money Exchange
===================
Agrega Campos al Objeto de account.invoice(facturas), para manejar el tipo de cambio base.
    """,
    'depends': [
        'account',
    ],
    'data': [

    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
