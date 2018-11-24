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
    'name': 'Poiesis Authorization Base',
    'version': '11.0',
    'category': 'Authorization',
    'depends': ['base', 'mail'],
    'author': 'Poiesis Consulting',
    'summary': 'Base Authorization Module',
    'description': u"""
Módulo base de autorización
===========================

    El módulo se encarga de la funcionalidad de autorizaciones para cualquier documento dentro de Odoo.
    Las solicitudes y posterior aprobación se las realiza a través de este módulo.
    Debe encontrarse como dependencia de cualquier módulo que contenga autorizaciones.
""",
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'data': ['security/poi_auth_base_security.xml',
             'views/poi_auth_base.xml',
             'base_menu.xml',
             'views/auth_circuit_view.xml',
             'views/auth_rules_view.xml',
             'views/auth_document_view.xml',
             'security/ir.model.access.csv',
             ],
    'qweb': ['static/src/xml/view_auth.xml'],
    'installable': True,
}
