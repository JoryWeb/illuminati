# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of Sale - Bolivia',
    'version': '1.0.0',
    'category': 'Point Of Sale',
    'sequence': 20,
    'summary': 'Point of Sale adapted to Bolivia',
    'description': """
Point of Sale - Bolivia
=======================

* TODO: Popup restrict double session.

    """,
    'depends': ['point_of_sale', 'poi_bol_base', 'poi_pos_base', 'poi_bol_cc','poi_warehouse'],
    'data': [
        'views/poi_pos_bol_templates.xml',
        'views/point_of_sale_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [

    ],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/poi_pos_bol.xml'],
    'auto_install': False,
}
