{
    'name': 'Trafico de Clientes',
    'version': '1.1',
    'category': 'Sales',
    'sequence': 75,
    'summary': 'Motivos de Visita, tipos de Visita, Creacion de Iniciativas',
    'description': """
Client Traffic Management
===================
Registro Hoja de Trafico de Clientes en cual se puede llevar el control de visitas segun el Motivos de visita y productos.
    """,
    'depends': [
        'mail',
        'crm',
        'poi_warehouse',
    ],
    'data': [
        # 'security/hr_security.xml',
        'data/traffic_type_partner.yml',
        'security/ir.model.access.csv',
        'views/crm_traffic_view.xml',
        #'views/product.xml',

    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
