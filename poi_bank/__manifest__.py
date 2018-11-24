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
    'name' : 'Modulo de Banca',
    'version' : '0.3',
    'author' : 'Poiesis Consulting',
    'category' : 'Accounting',
    'summary' : 'Gestión de Cuentas bancarias',
    'description' : """
Poiesis Bank
============

To Do:
------
* Do not import when reference was already imported
    """,
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['base', 'account', 'poi_bol_base'],  # I've removed poi_fix
    'data': ['views/poi_bank.xml',
             'views/bank_view.xml',
             'views/account_payment_data.xml',
             #'account_bank_statement_view.xml',
             'security/ir.model.access.csv',
             'security/poi_bank_security.xml',
             'views/account_payment_view.xml',
             'views/account_view.xml',
             #'wizard/reconciliate_bank_statements.xml'
        #'.xml'
    ],
    'qweb' : [
        'static/src/xml/account_bank_statement_reconciliation.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
