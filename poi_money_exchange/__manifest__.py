##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Jesus Gorostiaga
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
    'name': 'Cambio de Moneda Efectivo',
    'version': '1.0',
    'category': 'Account',
    'summary': 'Cambio de Moneda',
    'description': """

    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['poi_bol_base','account'],
    'data': [
        'views/res_config_view.xml',
        'views/account_money_exchange.xml',
        'security/ir.model.access.csv',

        ],
    'installable': True,
    'application': True,

#    'certificate': 'certificate',
}
