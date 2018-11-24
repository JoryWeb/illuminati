# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo Module
#    Copyright (C) 2015 Grover Menacho (<http://www.grovermenacho.com>).
#    Autor: Grover Menacho
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
    'name': 'Processmaker BPM',
    'version': '1.0',
    'category': 'Tools',
    'summary': '(BETA) Integración con el Suite BPM Processmaker',
    'description': """
WORK IN PROGRESS!!!
THIS IS AN EARLY VERSION AND IS FOR TESTING PURPOSES ONLY

FEATURES
--------
- Create and edit Processmaker's BPM inside odoo

INSTRUCTIONS
------------
- Install Processmaker as per its documentation
- Make sure Apache's web server is accepting crossdomain iframes by not setting 'X-Frame-Options' in httpd.conf
- For a better look, make sure you install odoo skin on Processmaker
- https://www.youtube.com/watch?v=Cl587TfTUBw

ROADMAP
-------
- Invoke popup window with dynaform associated a to a web Entry from a initial node with public URL  
- LDAP Integration. Or sync users upon creation
- Install plugin & skin via API automatically from odoo to PM
- Add support for multiple odoo DBs in PM plugin (for inter-db integragration)
- Get process KPIs using odoo's reporting tools. Focus on process improvement. Use ODBC to connect to MySQL directly
- Implement Business Rule engine inside odoo. Read them from PM.
- Unify odoo's Inbox with PM's Inbox

TODO
----
- Peritir descargar los archivos zip desde la pagina de configuracion de PM
- Opción de intervenir diferentes botones de Odoo y derivarlos a un BPM. Investigar REST API para instanciar un proceso de PM
- Limpiar processmaker.js de todo rastro de apps.js
- Mejorar plugin de PM para permitir llamar cualquier función de objeto de odoo (no sólo read, write, etc.)
- Investigar la manera de que los Steps de PM se ejecuten sin ser asignados a algún usuario
- Manejar el timeout de la sesión de login, para refrescar el token

    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['base'],
    'data': ['views/processmaker_view.xml',
             'views/pm_config_view.xml'],
    'qweb' : [
        "static/src/xml/*.xml",
    ],
    'installable': False,
    'active': False,
    'application': True,
}