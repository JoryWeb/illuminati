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
    'name': 'Logistic Analysis Reports - Sale Invoices',
    'version': '1.0',
    'category': 'Report',
    'sequence': 19,
    'summary': 'Analysis Reports',
    'description': """
Logistic Analysis Reports - Sale Invoices
=========================================

This module includes logistic reports

    """,
    'author': 'Poiesis Consulting',
    'website': 'https://www.poiesisconsulting.com',
    'depends': ['poi_web_chart','poi_materialized_view','sale','account','poi_logistic', 'poi_warehouse_sale', 'poi_warehouse_invoice'],
    'data': [
        'wizard/invoices_analysis_wizard_view.xml',
        'report/product_sale_invoice_list_view.xml',
        'report/product_date_sold_returned_invoices_view.xml',
        'product_view.xml',
        'security/ir.model.access.csv'
    ],
    'installable': False,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
