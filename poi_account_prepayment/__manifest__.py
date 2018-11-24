##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Poiesis Consulting (<http://poiesisconsulting.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'Account Prepayment',
    'version' : '1.0',
    'author' : 'Poiesis Consulting',
    'category' : 'Accounting',
    'summary' : 'Prepayment Voucher',
    'description' : """
Poiesis Account Prepayment
==========================

* Adds prepayment accounts to partner
* Adds two menus to create prepayments (customer, supplier)

    """,
    'website': 'http://www.poiesisconsulting.com',
    'depends' : ['base','account','poi_trace', 'account_cancel'],
    'data': [
        'views/res_partner_view.xml',
        'views/account_payment_view.xml',
    ],
    'qweb' : [
        #"static/src/xml/mi_modulo.xml",
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
