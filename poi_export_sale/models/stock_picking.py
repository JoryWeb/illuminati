##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import models, api, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    @api.depends('move_line_ids')
    def _compute_weight_picking(self):
        weight = 0.0
        for move_line in self.move_line_ids:
            if move_line.product_id and not move_line.result_package_id:
                weight += move_line.product_uom_id._compute_quantity(move_line.qty_done,
                                                                     move_line.product_id.uom_id) * move_line.product_id.weight
        self.weight_exp = weight

    weight_exp = fields.Float(string=u"Peso Neto/Realizado", compute='_compute_weight_picking')
    weight_tara = fields.Float(string=u"Peso Tara")
    weight_bruto = fields.Float(string=u"Peso Bruto")