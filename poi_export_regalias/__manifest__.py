# -*- coding: utf-8 -*-
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
    'name': 'Exportaciones Pago Regalias',
    'version': '11.0.0.1',
    'author': 'Poiesis Consulting',
    'category': 'account',
    'summary': 'Exportaciones pago de regalias',
    'description': """
Pago de regalias
=====================

Funcionalidades
---------------
* Pago de regalias DS Nº 29577

    """,
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
        'account',
        'poi_export_sale',
        'poi_bol_cc',
    ],
    'data': [
        'views/payment_royalties_views.xml',
        'views/invoice_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
