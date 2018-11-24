{
    'name': 'Pagos Adelantados Sin Factura',
    'summary': 'Funcionalidad de Registrar pagos Adelantados sin la necesidad de crear alguna Factura. y directamente desde la order de venta',
    'description': """
    """,
    'version': '1.0',
    'author': "Poiesis Consulting",
    'category': 'Extra Tools',
    'website': "http://poiesisconsulting.com",
    'depends': ['sale', 'account', 'poi_payment_request'],
    'data': [
        'views/sale.xml',
        'views/account_payment_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'images': []
}
