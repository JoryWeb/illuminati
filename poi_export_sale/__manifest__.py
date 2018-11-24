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
    'name': 'Exportaciones Bolivia',
    'version': '11.0.0.1',
    'author': 'Poiesis Consulting',
    'category': 'account',
    'summary': 'Localización para norma de Exportaciones en Bolivia',
    'description': """
Exportaciones Bolivia
=====================
Aplicable a ventas al exterior

Funcionalidades
---------------
- Incorpora la "Orden de exportación" que esta basada en la Orden de venta nativa. Tiene su propia numeración OE/XXXXX
- Las facturas generadas desde estas OE estarán accesibles desde el menú Facturas de exportación. Estas tienen su propio Diario contable.
- Impresión de la factura de exportación en formato según norma.
- Impresión de la Lista de empaque según norma
- Incorporación de las facturas de exportación en el Libro de ventas según norma.

    """,
    'website': 'http://www.poiesisconsulting.com',
    'depends': [
        'account',
        'sale',
        'sale_stock',
        #'poi_bol_base',
        'poi_bol_cc',
        'delivery',
    ],
    'data': [
        'data/data2.xml',
        'data/data_base.xml',
        'views/res_company.xml',
        'views/invoice_view.xml',
        'views/sale_export.xml',
        'views/res_partner.xml',
        'views/res_country.xml',
        'views/product.xml',
        'views/stock_picking_views.xml',
        #'report/invoice_export.xml',
        #'report/packing_list.xml',
        'data/data.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
