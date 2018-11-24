##############################################################################
#
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolás Bustillos
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
    'name' : 'Poiesis Account Analytic Base',
    'version' : '1.0',
    'category': 'Accounting',
    'depends' : ['base','analytic'],
    'author' : 'Poiesis Consulting',
    'summary': 'Base Analytic Account',
    'description': u"""

""",
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'data': ['views/account_view.xml',
             'views/account_payment_view.xml',
             'security/ir.model.access.csv'],
    'installable': True,

}
