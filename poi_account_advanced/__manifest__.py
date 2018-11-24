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
    'name': 'Contabilidad extendida',
    'version': '11.0',
    'category': 'Account',
    'summary': 'Contabilidad potenciada por Poiesis Consulting',
    'description': """
Incorpora las siguientes funcionalidades para una contabilidad mas completa:

* Manejo de Segmentos en Apuntes contables
* Especificación de Segmentos a nivel de líneas de Orden de Compra y Factura de Compra
* Libro Mayor dinámico en pantalla
DEPRECADO V9:
* Bloqueo de Periodos contables a nivel de Diario específico
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['account', 'account_budget','purchase', 'poi_bank'],
    'data': [
            'views/account_view.xml',
            'views/master_data_view.xml',
            'report/libro_mayor_view.xml',
            'security/ir.model.access.csv',
            ],
    'installable': True,
}
