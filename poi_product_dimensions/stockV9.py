# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _
from openerp.exceptions import Warning
class StockMove(models.Model):
    _inherit = "stock.move"

    lot_creation_pack = fields.Many2one('stock.production.lot', string="Lote")
    causa = fields.Char(string=u"Causa no conformidad")

    @api.onchange('lot_creation_pack')
    def onchange_lot_creation_pack(self):
        if self.lot_creation_pack:
            dimension_ids = self.product_id.dimension_ids.ids
            valido = True
            for item in dimension_ids:
                if item == self.lot_creation_pack.dimension_id.id:
                    valido = False
            if valido:
                self.lot_creation_pack = False
                self.restrict_lot_id = False
                #raise Warning('La medida seleccionada no es valida')
            else:
                self.restrict_lot_id = self.lot_creation_pack.id

    @api.model
    def _prepare_procurement_from_move(self, move):
        vals = super(StockMove, self)._prepare_procurement_from_move(move)
        vals['lot_id'] = move.restrict_lot_id.id
        return vals

class StockPackOperationLot(models.Model):
    _inherit = "stock.pack.operation.lot"
    secuencia = fields.Integer(string='N° Pack', default=0)

