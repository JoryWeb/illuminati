##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GN U Affero General Public License as
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
    'name': u'Módulo Básico de Logística',
    'version': '1.0',
    'category': 'Custom',
    'sequence': 14,
    'summary': 'Logistica',
    'description': """
Modulo de Logistica
===================


    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['product', 'stock', 'poi_web_chart', 'poi_essential_reports', 'poi_warehouse'],
    'data': ['security/logistic_security.xml',
             'product_stock_control_view.xml',
             'report/margin_stock_report_view.xml',
             'report/product_logistic_categories_view.xml',
             'product_view.xml',
             'res_company_view.xml',
             'security/ir.model.access.csv'
             ],
    'installable': False,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwid th=4: