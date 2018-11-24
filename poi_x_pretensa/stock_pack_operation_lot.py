# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _
import logging
_logger = logging.getLogger(__name__)

class StockPackOperationLotRecu(models.Model):
    _name = "stock.pack.operation.lot.recu"
    #operation_lot_id = fields.Many2one("stock.pack.operation.lot", string="Operacion")
    name = fields.Char("Lote Recuperación")
    lot_id = fields.Many2one("stock.production.lot", string="Lote")
    qty = fields.Float(string="Cantidad")
    operation_recu_line = fields.One2many("stock.pack.operation.lot.recu.line", "operation_lot_id")

    @api.model
    def default_get(self, fields):
        res = super(StockPackOperationLotRecu, self).default_get(fields)
        lot_id = self._context.get('lot_id')
        qty = self._context.get('qty')
        lines = []
        res['lot_id'] = lot_id
        res['qty'] = qty
        res['name'] = self.env["stock.production.lot"].browse(lot_id).name
        return res


class StockPackOperationLotRecuLine(models.Model):
    _name = "stock.pack.operation.lot.recu.line"
    operation_lot_id = fields.Many2one("stock.pack.operation.lot.recu", string="Recuperados Lista")
    qty = fields.Float(string=u"Cantidad", default=1.0)
    return_pack_lot = fields.Many2one("stock.pack.operation.lot", string=u"Lote Devolución")
    causa = fields.Char(string=u"Causa no conformidad")

class StockPackOperationLot(models.Model):
    _inherit = "stock.pack.operation.lot"

    @api.model
    def _get_origen(self):
        for pack_lot in self:
            pack_lot.origen = pack_lot.operation_id.picking_id.origin
    #operation_id = fields.Many2one("stock.pack.operation", string="operacion")
    origen = fields.Char(compute="_get_origen", string='Origen', copy=False, default='')
    name = fields.Char(string='Nombre', required=True, copy=False, default='', store=True)
    return_pack_lot = fields.Many2one("stock.pack.operation.lot", string=u"Lote Devolución")
    #return_pack = fields.Many2one("stock.pack.operation.lot.recu", string=u"Lote Devolución", domain=[('qty', '<', 0)])
    causa = fields.Char(string=u"Causa no conformidad")

    @api.model
    def create(self, vals):
        operation_pick = self.env['stock.pack.operation'].browse(vals['operation_id'])
        if vals['lot_id']:
            lot_obj = self.env['stock.production.lot'].browse(vals['lot_id'])
            if vals.get('secuencia'):
                vals['name'] = str(vals['secuencia']) + "-" + operation_pick.picking_id.name + '-' + lot_obj.name
        #else:
        #    vals['name'] = operation_pick.picking_id.name + operation_pick.product_id.name_template + 'Cant.: ' + str(vals['qty'])
        res_id = super(StockPackOperationLot, self).create(vals)
        return res_id

    @api.onchange('return_pack_lot')
    def onchange_internal_type(self):
        for line_op in self:
            if line_op.return_pack_lot:
                if line_op.lot_id.dimension_id.var_x > line_op.return_pack_lot.lot_id.dimension_id.var_x:
                    _logger.warning('No puede seleccionar a medida (%s).',
                                    line_op.return_pack_lot.name)


    _sql_constraints = [
        ('qty', 'CHECK(qty >= 0.0)', 'Quantity must be greater than or equal to 0.0!'),
        ('uniq_lot_id', 'CHECK(1=1)', 'You have already mentioned this lot in another line'),
        ('uniq_lot_name', 'CHECK(1=1)', 'You have already mentioned this lot name in another line')]

