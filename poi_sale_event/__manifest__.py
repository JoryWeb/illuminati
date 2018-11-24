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
    'name': 'Listas de regalo para Eventos',
    'version': '2.0',
    'category': 'Sales',
    'summary': 'Gestión para venta de listas de regalos',
    'description': """
    
- Permite la creación de Eventos como listados de regalos a ser reservados y posteriormente comprados
- Asistente de facturación y entrega

ToDo:
Vinculo Pos
Desreserva
Lector de código de barras
    """,
    'author': 'Poiesis Consulting',
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['sale','stock','poi_warehouse'],
    'data': ['security/ir.model.access.csv',
             'views/event_view.xml',
             'views/stock_view.xml',
             'wizard/event_invoice_view.xml',
             'wizard/event_pick_view.xml',
             ],
    'qweb': [],
    'installable': False,
    'active': False,
    'application': True,
}