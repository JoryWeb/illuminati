# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of Sale - Presale',
    'version': '1.0.0',
    'category': 'Point Of Sale',
    'sequence': 1,
    'summary': 'Point of Sale',
    'description': """
Point of Sale - Poiesis Consulting
==================================

    """,
    'depends': ['point_of_sale'],
    'data': [
        'views/poi_pos_base_templates.xml',
        'views/point_of_sale_view.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/poi_pos_presale.xml'],
    'auto_install': False,
}
