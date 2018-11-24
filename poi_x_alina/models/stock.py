##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _
from openerp.exceptions import UserError, ValidationError, Warning

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _batch_equivalente(self):
        for move in self:
            if move.raw_material_production_id:
                for bom_lines in move.raw_material_production_id.bom_id.bom_line_ids:
                    if move.product_id.id == bom_lines.product_id.id:
                        move.batch = bom_lines.product_qty
            else:
                move.batch = 0.0

    @api.one
    @api.depends('state', 'product_id', 'product_qty', 'location_id')
    def _compute_product_availability_origin(self):
        if self.state == 'done':
            self.availability_origin = self.product_qty
        else:
            quants = self.env['stock.quant'].search(
                [('location_id', 'child_of', self.location_id.id), ('product_id', '=', self.product_id.id),
                 ('reservation_id', '=', False)])
            self.availability_origin = min(self.product_qty, sum(quants.mapped('qty')))

    batch = fields.Float(string=u"Batch equivalente", compute='_batch_equivalente')
    availability_origin = fields.Float(
        'Cantidad Disponible', compute='_compute_product_availability_origin',
        readonly=True, help='Cantidad Disponible en la ubicación de origen')

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def do_new_transfer(self):
        if self.location_dest_id.usage == 'inventory' and not self.env.user.has_group('poi_x_landicorp.group_scrap_inventory'):
            raise Warning('Solo el contador puede validar esta transferencia, envíe un email al responsable\nUsando la mensajería del sistema')

        res = super(StockPicking, self).do_new_transfer()
        return res