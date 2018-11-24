##############################################################################
#    
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
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
    'name': 'Control Cajero',
    'version': '9.0.1.0',
    'category': 'Account',
    'summary': 'Lleva control de los pagos del cajero',
    'description': """
Incorpora las siguientes funcionalidades para una contabilidad mas completa:

* Todos los movimiento originados desde un Pago del modulo de Contabilidad lleva el registro del cajero usuario
* Gerente de contabilidad puede asociar un Pago interno a un cajero especifico
* Reporte consolidado de movimientos del cajero

CONSIDERACIONES
---------------
* Actualmente el reporte funciona para monedas Bolivianos y Dolares. Si se desea crear Diarios en otras monedas (EUR), se debe revisar el reporte generado

ROADMAP
-------
* Rol de cajero?
* Manejo dinamico de mas de dos monedas
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['account', 'poi_account_analytic'],
    'data': ['account_payment_view.xml',
             'wizard/account_report_payment_sum_view.xml',
             'report/payment_sum_view.xml',
             'security/ir.model.access.csv',
            ],
    'installable': True,
    'active': True,
    'application': True,
}