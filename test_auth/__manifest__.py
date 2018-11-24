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
    'name' : 'Poiesis Authorization - Test Module',
    'version' : '11.0',
    'category': 'Authorization',
    'depends' : ['poi_auth_base','sale','purchase'],
    'author' : 'Poiesis Consulting',
    'summary': 'Sale Authorization Module',
    'description': u"""

""",
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'data': [
        "data/poi_auth_auth_python_code.xml",
        "data/poi_auth_circuit.xml",
        "data/poi_auth_auth.xml",
    ],
    'installable': True,
}
