
{
    'name': 'Administración de Adjuntos',
    'version': '11.0.0.1',
    'author': 'Poiesis Consulting',
    'category': 'account',
    'summary': 'Adjuntos',
    'description': """
Administración de adjuntos
=====================
* Registro amigable de adjuntos y filtros adicionales
    """,
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
        'document',
        'base',
        'stock',
        'purchase',
        'account',
        'sale',
    ],
    'data': [
        'views/ir_attachment_views.xml',
        'views/stock_picking_views.xml',
        #'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/invoice_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
}
