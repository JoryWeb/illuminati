##############################################################################
#
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolás Bustillos
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
    'name' : 'Localización Bolivia',
    'version' : '11.1',
    'category': 'Localization',
    'depends' : ['account','sale','purchase','stock','contacts','account_tax_python','poi_warehouse','inputmask_widget'],
    'author' : 'Poiesis Consulting',
    'summary': 'Localización de odoo para normas de Bolivia',
    'description': u"""
Localización para Bolivia
=========================

Datos cargados
--------------
* Impuestos
* Moneda
* Territorios
* Bancos

Funcionalidades incorporadas
----------------------------
* Campos en Partners: NIT y Razón social (se copian en la creación de una factura)
* Campo de CI en contactos de Partner
* Cálculo de Asientos según ajuste por inflación (UFV y USD)
* Libros de Compra y Venta
* Bancarización
* Notas de crédito según ley
* Campos en Producto: Último precio de compra, Código antiguo
* Uso de Dosificaciones para facturación (sin código de control, sólo numeración y nro de orden)
* Corrección de la generación de asientos con moneda secundaria sobre la factura
* Seguimiento de Facturas para generar Albaran y Pago
* Adicion de campos por tipo de pago en ventas
* Configuraciones generales para instalar los módulos periféricos a esta
* Facturación de Pagos adelantados según ley


INSTRUCCIONES
=============

Cálculo IT
----------
Debe existir un Impuesto que tenga especificadas la Cuenta Impuestos, Contra Cuenta de Impuesto y un Diario contable.
Estos datos serán tomados en cuenta al generar el Asiento desde el asistente del menú
Contabilidad->Procesamiento periódico->Impuestos->Registro IT

Roadmap
-------
* Inversor de tipo de cambio para imputar por ejemplo 6.96

""",
    #ToDo: Cambiar datos existentes: Actualizar BOB-No crear nuesva, Moneda Company, Moneda Lista de precio, Cuentas categ 'All Products', Pais defecto Partner 'Bolivia', Borrar estados US, Cambia Zona horaria Admin
    #ToDo: Obtener tipos de cambio UFV desde el BCB: https://www.bcb.gob.bo/librerias/indicadores/ufv/anual.001.php
    'website': 'http://www.poiesisconsulting.com',
    'data': [
        'security/poi_bol_base_security.xml',
        'security/ir.model.access.csv',
        'data/bo_chart_data.xml',
        'data/base_config.xml',
        'data/account_tax.xml',
        'views/poi_bol_base.xml',
        'views/res_currency.xml',
        'bank_view.xml',
        'config_view.xml',
        'partner_view.xml',
        'product_view.xml',
        'account_view.xml',
        'account_move_view.xml',
        'revert_view.xml',
        'invoice_view.xml',
        'company_view.xml',
        'purchase_view.xml',
        'sale_view.xml',
        'stock_view.xml',
        'dosif_view.xml',
        'customer_view.xml',
        'report/account_report.xml',
        # 'wizard/actualiza_aitb_view.xml',
        # 'wizard/imp_it_view.xml',
        # 'wizard/nota_credito_view.xml',
        'wizard/libro_cv_view.xml',
        # 'wizard/account_invoice_tax_inverse_view.xml',
        # 'wizard/account_invoice_refund.xml',
        # 'wizard/account_general_ledger_view.xml',
        # 'report/bancarizacion_view.xml',
        # 'report/lcv1pdf.xml',
    ],
    'installable': True,
    'active': False,
    'sequence': 0,
    'application': True,
}
