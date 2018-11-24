# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


# EL NOMBRE DE LA CASE IGUAL AL DEL PADRE
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    # unit_size = fields.Char(u'Unidades de medida')
    # unit_size_buy = fields.Char(u'Unidad de medida de compra')
    # company = fields.Char(u'Compañia')
    # make_order = fields.Boolean(u'Hacer el pedido')
    btwo = fields.Integer(string=u'% B2O3')
    htwo = fields.Integer(string=u'% H2O')
    dry_base_prod = fields.Integer(string=u'Base Seca')
    # acc_inside = fields.Char(u'Cuenta de Ingreso')
    # costumer_tax = fields.Char(u'Coste de destino')
    # 3type_acc = fields.Char(u'Tipo de Activo')
    # speding_acc = fields.Char(u'Cuenta de Gasto')
    # tax_provee = fields.Char(u'Impuesto de Proveedor')
    # acc_dif_price = fields.Char(u'Cuenta diferencia de precio')
    # exist_acc_entry = fields.Char(u'Cuenta de entrada de existencias')
    # imp_acc_exist = fields.Char(u'Cuenta importación de existencias')
    # acc_exit_existe = fields.Char(u'Cuenta de salida de importacion')
    # valor_ufv = fields.Boolean(u'Aplicar valoración UFV')
