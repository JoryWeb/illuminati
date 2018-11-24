import logging
from odoo import fields, models, api, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)

class PricelistUpdate(models.Model):
    _name = 'pricelist.update'
    _description = 'Asistente para la modificacion de Precios'

    applicant_id = fields.Many2one('res.users', 'Solicitante')
    pricelist_id = fields.Many2one('product.pricelist', 'Lista de Precios')
    state = fields.Selection(
        string="Estado",
        selection=[
                ('draft', 'Borrador'),
                ('auth', 'Autorizado'),
                ('done', 'Aplicado'),
        ], default="draft"
    )

    line_ids = fields.One2many('pricelist.update.line', 'update_id', 'Lineas de Precios')

class PricelistUpdateLine(models.Model):
    _name = 'pricelist.update.line'
    _description = 'Lineas del Asistente de modificacion de precios'

    update_id = fields.Many2one('pricelist.update', 'Modificacion de Precios')
    product_id = fields.Many2one('product.product', 'Producto')
    year = fields.Integer(u'Año')
    lot_id = fields.Many2one('stock.production.lot', 'Lote')
    qty_min = fields.Float('Cantidad Minima')
    date_from = fields.Date('Fecha Inicial')
    date_to = fields.Date('Fecha Final')
    cost = fields.Float('Costo', readonly=True, related="product_id.standard_price")
    price = fields.Float('Precio')
    discount_max = fields.Float('Descuento Maximo')
