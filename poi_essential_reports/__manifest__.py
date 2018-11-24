##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Essential Reports',
    'version': '1.0',
    'category': 'Report',
    'sequence': 19,
    'summary': 'Essential Reports',
    'description': """
Essential Reports
==================================================

This module includes essential reports

Include:
---------------------------------------------------------
* Actual Stock Report

    """,
    'author': 'Poiesis Consulting',
    'website': 'https://www.poiesisconsulting.com',
    'depends': ['stock','poi_materialized_view'],
    #'depends': ['stock', 'product'],
    'data': [
    ],
    'installable': False,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
