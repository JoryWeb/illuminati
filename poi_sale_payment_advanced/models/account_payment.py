import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    order_id = fields.Many2one('sale.order', compute="_compute_order_id", store=True, string='Orden Venta', inverse="_set_order_id")

    @api.multi
    @api.depends("payment_request_id")
    def _compute_order_id(self):
        for s in self:
            if s.payment_request_id:
                s.order_id = s.payment_request_id.sale_order_id.id

    @api.multi
    def _set_order_id(self):
        return True
