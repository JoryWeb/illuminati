#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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
    "name": "es_BO Facturación Electrónica",
    "version": "1.0",
    "category": "Localization",
    "depends": ["account", "poi_bol_base", "poi_warehouse"],
    'external_dependencies': {'python': ['qrcode'
                                         ],
                              },
    "author": "Poiesis Consulting",
    "description": """Localización Bolivia:
    - Codigo de control Ver. 7
    - Impresión del Código QR
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'data': [
        'invoice_view.xml',
        'cc_data.xml',
        'cc_view.xml',
        'report/invoice_base.xml',
        'report/basic_invoice.xml',
        'security/ir.model.access.csv',
        # 'views/report_ibol.xml',
    ],
    'installable': True,
    'active': True,
}
