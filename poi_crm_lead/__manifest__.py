{
    'name': 'Localisacion del Modulo CRM',
    'summary': 'Localisacion del modulo Crm, para las Iniciativas y Oportunidades.',
    'description': """
Crm Lead Poiesis

Se Agregron nuevos campos:
    - ci
    - nit
    - razon
    - Ubicacion/Almacen
Nuevas funcionalidades:
    * Busqueda automatica de cliente por ci o nit.
    * Creacion de Oportunidades con los nuevos campos incluidos en la Iniciativa
    """,
    'version': '11.0',
    'author': "Poiesis Consulting",
    'category': 'Extra Tools',
    'website': "http://poiesisconsulting.com",
    'depends': [
        'crm',
        'sale_crm',
        'poi_partner_firstname',
        'poi_warehouse',
        'poi_bol_base',
    ],
    'data': [
        #'security/ir.model.access.csv',
        'views/crm_lead.xml',
        # 'views/res_user.xml',
        # 'data/res_partner.yml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'images': []
}
