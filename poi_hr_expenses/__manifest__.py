##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2014 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Jesus Gorostiga Herrera
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
    'name': 'Recursos Humanos Rendicion de Gastos',
    'version': '11.0',
    'category': 'Human Resources',
    'summary': 'Funciones Avanzadas para recursos Humanos',
    'description': """
Recursos Humanos Rendicion de Gastos
===================================
  ** Rendicion de Gastos \n
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
            'hr',
            'poi_payment_request',
            'account',
        ],
    'data': [
            'security/security.xml',
            'views/hr_menu.xml',
            'security/ir.model.access.csv',
        ],
    'installable': True,
}
