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
    'name': 'Payment Request',
    'version': '11.0',
    'category': 'Account',
    'summary': 'Solicitud de Pago/Cobro y Rendiciones',
    'description': """
        - Solicitud de Pago
        - Solicitud de Cobro
        - Rendiciones
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['account','purchase','poi_account_prepayment','poi_cash_movements','poi_trace','poi_bank'],
    'data': [
            'wizard/account_payment_expenses.xml',
            'views/account_view.xml',
            'views/account_expenses_rendition_view.xml',
            'views/account_sequence.xml',
            'security/payment_request_security.xml',
            'security/ir.model.access.csv'],
    'qweb': [],
    'installable': True,
}
