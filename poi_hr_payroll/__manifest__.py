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
    'name': 'Funciones Avanzadas Para Nominas Salariales',
    'version': '11.0',
    'category': 'Human Resources',
    'summary': 'Funciones Avanzadas para recursos Humanos',
    'description': """
Recursos Humanos Funciones Avanzadas Nominas Salariales
=======================================================
  **


    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
            'hr_payroll',
            'poi_hr_advanced',
            'poi_hr_public_holidays',
        ],
    'data': [
            'views/hr_advance.xml',
            'views/hr_loan.xml',
            'views/hr_form110.xml',
            'views/hr_others.xml',
            'views/hr_planing.xml',
            'views/hr_bio.xml',
            'views/hr_payroll.xml',
            'views/hr.xml',
            'views/hr_finiquito.xml',
            'views/hr_menu.xml',
            'report/finiquito_img.xml',
            'report/finiquito.xml',
            'data/data_payroll.xml',
            'data/data_currency.xml',
            'security/ir.model.access.csv',
        ],
    'installable': True,
    'sequence': 0,
}
