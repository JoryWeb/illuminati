##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Coded by: Grover Menacho
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
    'name': 'Product Dimensions',
    'version': '1.0',
    'category': 'Warehouse',
    'summary': 'Product Dimensions',
    'description': """
Product Dimensions
===================================
This module adds dimensions to products.
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['base','product','sale','purchase','sale_stock','account'],
    'data': [
            'product_dimension_data.xml',
            'security/ir.model.access.csv',
            'product_dimension_view.xml',
            'product_view.xml',
            'sale_view.xml',
            'stock_view.xml',
            'purchase_view.xml',
            'account_invoice_view.xml',
            ],
    'installable': False,
    'active': False,
    'application': True,
}