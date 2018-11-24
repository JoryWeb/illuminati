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
    'name' : 'Exportaciones Pretensa',
    'version' : '9.0.0.1',
    'author' : 'Poiesis Consulting',
    'category' : 'account',
    'summary' : 'Reportes de Exportaciones a medida Pretensa',
    'description' : """
reportes a media de exportaciones para pretensa
    """,
    'website': 'http://www.poiesisconsulting.com',
    'depends' : [
        'account',
        'sale',
        'poi_sale_export',
    ],
    'data': [
            'report/logo_template.xml',
            'report/invoice_export.xml',
            'report/packing_list.xml',
            'report/invoice_copy_export.xml',
            ],
    'installable': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
