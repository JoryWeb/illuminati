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
    'name' : 'Poiesis Cash Movements',
    'version' : '0.1',
    'author' : 'Poiesis Consulting',
    'category' : 'Accounting',
    'summary' : 'Cash Movements',
    'description' : """
Poiesis Cash Movements
======================

Este modulo se encarga de:
--------------------------
Movimientos de tesoreria
Pagos de Movimientos
    """,
    'website': 'http://www.poiesisconsulting.com',
    'depends' : ['base','account','poi_bank','poi_trace'],
    'data': [
        'cash_movements_view.xml',
        'cash_movements_sequence.xml',
        'security/ir.model.access.csv'
    ],
    'qweb' : [
        #"static/src/xml/mi_modulo.xml",
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
