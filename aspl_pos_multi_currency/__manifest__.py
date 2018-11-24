#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    'name': "POS Multi Currency",
    'version': '1.0',
    'category': 'Point of Sale',
    'description': """
This module is allow to pay with multiple currencies from POS Interface.
""",
    'summary': 'Payment with multiple currencies from Point of sale Interface.',
    'author': 'Acespritech Solutions Pvt. Ltd.',
    'website': "http://www.acespritech.com",
    'currency': 'EUR',
    'price': 22.00,
    'depends': ['web', 'point_of_sale', 'base', 'account_invoicing'],
    'data': [
        'views/aspl_pos_multi_currency.xml',
        'views/point_of_sale_view.xml'
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: