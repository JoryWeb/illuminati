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
    'name': 'Payment Request - Bolivia',
    'version': '2.0',
    'category': 'Account',
    'summary': 'Localización SIN para Rendiciones',
    'description': """

- Incorpora los campos requeridos por Impuestos Nacionales en la Rendición de gastos con factura.
- Asistente de cálculo inverso para Retenciones
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['poi_payment_request','poi_bol_base','inputmask_widget'],
    'data': [
            'views/account_expenses_rendition_view.xml',
            'wizard/account_rendition_tax_inverse_view.xml',
        ],
    'qweb': [],
    'installable': True,
    'active': False,
    'application': True,
}
