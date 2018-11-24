# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


# EL NOMBRE DE LA CASE IGUAL AL DEL PADRE
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    division_nprod = fields.Char(string=u'División')
    factory_nprod = fields.Char(string=u'Fabrica')
    world_nprod = fields.Char(string=u'Mundo')
    gif_card_nprod = fields.Boolean(string='Es una tarjeta de ragalo', default=False, help='')
    unid_size_nprod = fields.Char(string=u'Unidades de medida')
    unid_size_buy_nprod = fields.Char(string=u'Unidad de medida de compra')
    warrant_prod_sales = fields.Integer(string=u'Garantía')
    term_prod_cli_sales = fields.Integer(string=u'Plazo de entrega al cliente')
    web_cliente_info = fields.Char(string=u'Pagina web del fabricante', required=True)
    vid_nprod_info = fields.Char(string=u'Enlace a video de desmostración del producto(Youtube,etc)', required=True)
    available_pdv_sales = fields.Boolean(string=u'Disponible en el Pdv')
    category_pdv_sales = fields.Selection([('EUR', 'EUR'),
                                           ('USD', 'USD'),
                                           ('BS', 'BS')],
                                          string=u'Moneda del proveedor')
    for_weight_balance_sales = fields.Boolean(string=u'Para pesar con balamza')
    type_nprod = fields.selection([('1', '1'),
                                   ('2', '2'),
                                   ('3', '3'),
                                   ('4', '4'),
                                   ('5', '5'),
                                   ('6', '6'),
                                   ('7', '7'),
                                   ('8', '8'),
                                   ('9', '9'),
                                   ('10', '10')],
                                  string=u'Communication Skills')
