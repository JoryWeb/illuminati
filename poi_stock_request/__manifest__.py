
{
    "name": "Solicitud de Stocks",
    "version": "3.0",
    "category": "Warehouse",
    "depends": ["stock", "poi_stock_account_consolidate"],
    "author": "Poiesis Consulting",
    "website": 'http://www.poiesisconsulting.com',
    "description": """
Solicitud de Stocks
==============

* Simple registro de solicitud de productos entre almacenes
* Manejo de reglas de abastecimiento
* Planificación de entregas desde los picking confirmados

    """,
    'data': [
             #'security/request_security.xml',
             #'data/stock_request_data.xml',
             'wizard/request_products_view.xml',
             'views/stock_request_view.xml',
             'data/stock_request_sequence.xml',
             'security/ir.model.access.csv'
            ],
    'demo_xml': [],
    'installable': True,
    'active': True,
    'application': True,
#    'certificate': 'certificate',
}