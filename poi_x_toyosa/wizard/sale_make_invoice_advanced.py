import logging
from odoo import fields, models, api, _
from odoo.exceptions import Warning
import time
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection([
        ('delivered', 'Invoiceable lines'),
        ], string='What do you want to invoice?', default='delivered', required=True)

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        invoice_id = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)

        invoice_id.order_id = order.id
        for line in self.invoice_line_ids:
            if line.sale_line_ids[0].lot_id:
                line.lot_id = line.sale_line_ids[0].lot_id.id
