# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of Sale - Presale Bolivia',
    'version': '1.0.0',
    'category': 'Point Of Sale',
    'sequence': 1,
    'summary': 'Point of Sale Advanced',
    'description': """
Point of Sale - Advanced
========================

    """,
    'depends': ['poi_pos_bol','poi_pos_presale'],
    'data': [],
    'demo': [],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/poi_pos_presale_bol.xml'],
    'auto_install': True,
}
