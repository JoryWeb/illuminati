# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Poiesis POS Discounts',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Discounts',
    'description': """
Discounts
=========

""",
    'depends': ['point_of_sale'],
    'data': [
        'views/templates.xml'
    ],
    'qweb': [
        'static/src/xml/discount.xml',
    ],
    'installable': True,
    'website': 'https://www.odoo.com/page/point-of-sale',
    'auto_install': False,
}
