##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2014 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Jesus Gorostiga Herrera
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
    'name': 'Alina Servicios Web',
    'version': '1.0',
    'category': 'Other',
    'summary': 'Intregacion con Servicios Web',
    'description': """

    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['base','sale', 'account', 'stock'],
    'data': [
             'views/res_partner.xml',
             'views/sale.xml',
             'views/account_payment.xml',
             'views/product_view.xml',
             'views/res_partner.xml',
             'views/stock_warehouse.xml',
             'security/ir.model.access.csv',
            ],
    'installable': False,
    'active': False,
    'application': True,
    'sequence': 0,
}
