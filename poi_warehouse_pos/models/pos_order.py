import logging
from odoo import fields, models, api, _


_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen', compute="_compute_warehouse_id", store=True)

    @api.multi
    @api.depends('cc_dos', 'state')
    def _compute_warehouse_id(self):
        for po in self:
            if po.cc_dos:
                po.warehouse_id = po.cc_dos.warehouse_id.id
