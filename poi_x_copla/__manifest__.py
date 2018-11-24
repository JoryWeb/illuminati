{
    'name': 'Funcionalidades Exclusivas de Copla',
    'summary': 'Funcionalidades Exclusivas',
    'description': """
* Adicionales campos en Proveedor
    """,
    'version': '11.0',
    'author': "Poiesis Consulting",
    'category': 'Generic',
    'website': "http://poiesisconsulting.com",
    'depends': ['account', 'stock', 'poi_export_sale', 'poi_export_transport'],
    'data': [
        'views/partner_view.xml',
        'views/stock_picking_view.xml',
        'views/product_template_form_view.xml',
        'views/purchase_view.xml',
        'views/sale_order_view.xml',
        'views/invoice_view.xml',
        'wizard/reservas_tren_wizard_view.xml',
        'report/reservas_tren_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
