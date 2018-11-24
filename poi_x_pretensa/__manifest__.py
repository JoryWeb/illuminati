##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Author: Carlos Iturri
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
    "name": "Pretensa V9 - Adecuaciones",
    "version": "1.0",
    "category": "Custom",
    "depends": ["poi_webkit", "stock", "account", "sale", "poi_product_dimensions", "poi_warehouse", "poi_warehouse_sale"],
    "author": "Poiesis Consulting",
    "website": 'http://www.poiesisconsulting.com',
    "description": """
Adecuaciones PRETENSA
========================


Funcionalidades Incorporadas:
------------------------------
* Tipo de Producto
* Registro dinámico de características técnicas en Orden de Venta según Tipo de Producto
* Registro Despuntes
* Registro de tipo Entrega en OV
* Impresión de cotizaciones en formato Pretensa
* Reporte de Ventas
* Autorizaciones restringidas por rol acorde a Pretensa

""",
    'data': [
            #'report/headers_data.xml',
            'recibo_report.xml',
            'product_type_view.xml',
            'security/ir.model.access.csv',
            'sale_view.xml',
            #'account_voucher_view.xml',
            'account_payment_view.xml',
            'account_view.xml',
            'stock_recovered_picking_view.xml',
            'stock_view.xml',
            'report/dashboard_view.xml',
            'report/vendedor_mes_view.xml',
            'report/tesoreria_view.xml',
            'oferta_reportviguetas.xml',
            'oferta_reportviguetassolo.xml',
            'oferta_reportrejilla.xml',
            'oferta_reportabiplast.xml',
            'oferta_reportviguetaseps.xml',
            'cubiertas.xml',
            'oferta_reportlosahueca.xml',
            'pricelist_view.xml',
            'stock_backorder_confirmation.xml',
            #'report/sale_report_view.xml',
            'stock_report.xml',
            'vale_entrega_report.xml',
            'print_invoice.xml',
            'account_invoice_view.xml',
            'account_voucher_sales_purchase_view.xml',
            'report/dashboard_cubiertas.xml',
            'security/pretensa_security.xml',
            'warehouse_view.xml',
            'data/picking_type_data.xml',
            'data/procurement_rule_data.xml',
            'data/ir_values_data.xml',
            'wizard/report_kardex_dos_wizard_view.xml',
            'report_kardex.xml',
            'report/kardex_view_dos.xml',
            'kardex_print_report.xml',
            'res_users_view.xml',
            #'report/report_kardex.xml',
            #'reports.xml',
            'product_return.xml',
            'product_return_workflow.xml',
            ],
    'demo_xml': [],
    'installable': False,
    'active': True,
}