##############################################################################
#    
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2011 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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
    "name": "Descuento Global V9",
    "version": "1.2",
    "category": "Invoicing & Payments",
    "depends": ["purchase", "sale"],
    "author": "Poiesis Consulting",
    "website": 'http://www.poiesisconsulting.com',
    "description": """
    Provee la opción de especificar a nivel global un descuento que se copie a cada linea
    """,
    "init_xml": [],
    'update_xml': [
        #'account_view.xml',
        'order_view.xml',
        'wizard/discount_amount_view.xml',
    ],
    'demo_xml': [],
    'installable': False,
    'active': True,
}