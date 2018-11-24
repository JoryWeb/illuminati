##############################################################################
#    
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2014 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Grover Menacho
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
    'name': 'Company POS Shop Warehouse',
    'version': '1.0',
    'category': 'Point Of Sale',
    'summary': 'Manage Shops to include some specific data',
    'description': u"""
Company Shops
===================================
This module adds shop functionality to some orders or data
 
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
        'base',
        'point_of_sale',
        'poi_warehouse',
        'poi_pos_bol',
    ],
    'data': [
        'views/warehouse_view.xml'
    ],
    'installable': True,
    'active': False,
    'application': True,

#    'certificate': 'certificate',
}
