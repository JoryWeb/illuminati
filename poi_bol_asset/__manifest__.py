##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Poiesis Consulting (<http://poiesisconsulting.com>).
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
    'name': 'Activos Fijos Bolivia (11)',
    'version': '11.0.0.1',
    'author': 'Poiesis Consulting',
    'category': 'account',
    'summary': 'Legislación de Bolivia para Activos Fijos',
    'description': """
Activos Fijos Bolivia (BETA)
============================
VERSION BETA. AUN NO LISTO PARA USO PRODUCTIVO.

Funcionalidades
---------------
- Parametros y funcionalidades para gestionar los Activos Fijos en Bolivia
- Desvinculación de las transacciones de AF de las Líneas de Asiento. Esto para evitar el volumen de datos en los Asientos contables.

Cargas iniciales
----------------
- Datos maestros
- Depreciación acumulada con cabecera de transacción
    """,
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['account_asset'],
    'data': ['views/asset_view.xml',
             'wizard/wizard_asset_compute_view.xml',
             #'report/asset_asset_reports.xml',
             'report/poi_account_asset_report_view.xml',
             'report/poi_kardex_asset_report_view.xml',
             'report/poi_account_asset_ufv_report_view.xml',
             'wizard/account_move_asset_reversal_view.xml',
             'security/ir.model.access.csv',
             ],
    'installable': True,
    'auto_install': False,
}
# ToDo:  Ver y controlar el cron job relacionado a "_cron_generate_entries". Asegurar que se adapte al nuevo esquema
# ToDo:  Actualización UFVs
# ToDo:  Valores mínimos en base a porcentaje (por categoría)
# ToDo:  Transacciones de Incremento y revalúo técnico (con recálculo de las líneas de depreciación)
# ToDo:  Modificar para que se cree un sólo Asiento de depreciación
# ToDo:  Depreciación de componentes ó padres
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
