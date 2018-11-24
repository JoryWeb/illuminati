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
    'name': 'Logistic Analysis Reports - Stock',
    'version': '1.0',
    'category': 'Report',
    'sequence': 19,
    'summary': 'Analysis Reports',
    'description': """
Logistic Analysis Reports - Stock
=================================

This module includes logistic reports

    """,
    'author': 'Poiesis Consulting',
    'website': 'https://www.poiesisconsulting.com',
    'depends': ['poi_materialized_view','stock','poi_logistic','poi_kardex_valorado','poi_web_chart'],
    'data': ['report/stock_analysis_view.xml',
             'wizard/kardex_wizard_view.xml',
             'product_view.xml',
            'security/ir.model.access.csv'
    ],
    'installable': False,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
