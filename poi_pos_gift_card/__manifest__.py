# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of Sale - Gift Cards',
    'version': '1.0.0',
    'category': 'Point Of Sale',
    'sequence': 20,
    'summary': 'Point of Sale Gift Cards',
    'description': """
Point of Sale - Gift Cards
==========================

TODO:
* Discount card from remaining amount
* Remove all the card used

    """,
    'depends': ['point_of_sale', 'poi_pos_base'],
    'data': [
        'views/poi_pos_gift_card_templates.xml',
        'views/point_of_sale_view.xml',
        'views/product_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [

    ],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/poi_pos_gift_card.xml'],
    'auto_install': False,
}
