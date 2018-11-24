# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of Sale - Advanced',
    'version': '1.0.0',
    'category': 'Point Of Sale',
    'sequence': 1,
    'summary': 'Point of Sale Advanced',
    'description': """
Point of Sale - Advanced
========================

    """,
    'depends': ['point_of_sale','poi_pos_base','poi_pos_bol'],
    'data': [
        'views/poi_pos_advanced_templates.xml',
        'views/res_partner_view.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/poi_pos_advanced.xml'],
    'auto_install': False,
}
