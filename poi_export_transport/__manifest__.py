
{
    'name': 'Transporte en Exportaciones',
    'version': '11.0.0.1',
    'author': 'Poiesis Consulting',
    'category': 'account',
    'summary': 'Manejo de transporte en exportaciones',
    'description': """
Transporte en exportaciones Bolivia
=====================
* Usar la funcionalidad de flotas y simplicar el registro de transrpotes
* Registro de incidencias por transporte
* Costes de transporte por rutas
    """,
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
        'fleet',
        'stock',
    ],
    'data': [
        #'data/data2.xml',
        #'data/data_base.xml',
        #'views/res_company.xml',
        #'views/invoice_view.xml',
        #'views/sale_export.xml',
        #'views/res_partner.xml',
        'views/incidence_transport_view.xml',
        'views/stock_picking_view.xml',
        'views/fleet_vehicle_views.xml',
        #'data/data.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
