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
    'name': 'Recursos Humanos Funciones Avanzadas',
    'version': '11.0',
    'category': 'Human Resources',
    'summary': 'Funciones Avanzadas para recursos Humanos',
    'description': """
Recursos Humanos Funciones Avanzadas
===================================
  ** Lista Negra \n
  ** Motivos de Desactivacion \n
  ** Campos Nuevos\n
  ** Familia del Empleado\n
  ** Adjuntos \n
  ** Educacion y Experiencias\n
  ** Memorandums\n
  ** Registro de Accidentes\n
  ** Afps\n


    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
            'hr',
            'hr_contract',
            'poi_bol_base',
        ],
    'data': [
            'views/hr_menu.xml',
            'views/hr.xml',
            'views/hr_family.xml',
            'views/hr_accident.xml',
            'views/hr_health_box.xml',
            'views/hr_afps.xml',
            'views/hr_attachment.xml',
            'views/hr_learning.xml',
            'views/hr_memo.xml',
            'views/hr_contract.xml',
            'report/memo.xml',
            'wizard/employee_reason_left.xml',
            'security/ir.model.access.csv',
        ],
    'installable': True,
    'sequence': 0,
}
