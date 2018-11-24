##############################################################################
#    
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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
    'name': 'Poiesis Materialized Views',
    'version': '1.0',
    'category': 'Technical Settings',
    'summary': 'Refresh Materialized Views',
    'description': """
Poiesis Materialized Views
==========================

This module is going to refresh Materialized Views on demand and based on a cron activity

    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['base'],
    'data': ['mreport_view.xml'],
    'installable': False,
    'active': False,
    'application': True,
    'images': [],

#    'certificate': 'certificate',
}
