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
    'name': 'Reportes para RRHH',
    'version': '11.0',
    'category': 'Human Resources',
    'summary': 'Reportes Recursos Humanos',
    'description': """
Recursos Humanos Reportes
===================================
  ** Configuracion de Reportes
  ** Planilla de Sueldos
  ** Planilla RcIVA
  ** Aportes Laborales
  ** Boleta de Pago
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
            'hr_payroll',
            'poi_hr_payroll',
            'hr_payroll_account',
            'qweb_usertime',
        ],
    'data': [
        'views/salary_rule.xml',
        'views/afp.xml',
        'wizard/payslip.xml',
        'wizard/rciva.xml',
        'wizard/afp.xml',
        'report/report_payslip_bol.xml',
        'report/rciva_payroll.xml',
        'report/report_afp.xml',
        'report/report_voucher_config.xml',
        'report/report_voucher_bol.xml',
        'report/report_payment.xml',
        'data/data_payroll.xml',
        ],
    'installable': True,
    'sequence': 0,
}
