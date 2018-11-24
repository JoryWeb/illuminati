import logging
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    currency_report_id = fields.Many2one('res.currency', 'Moneda de Impresion', default=lambda self: self.env.user.company_id.currency_id )
    amount_total_exchange = fields.Float('Monto Total', compute="_compute_amount_total_exchange", digits=dp.get_precision('Product Price'))

    @api.multi
    @api.depends("amount_total")
    def _compute_amount_total_exchange(self):
        for s in self:
            s.amount_total_exchange = s.currency_id.compute(s.amount_total, s.currency_report_id)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    currency_report_id = fields.Many2one('res.currency', 'Moneda de Impresion', related="order_id.currency_report_id")
    price_total_exchange = fields.Float('Monto Total', compute="_compute_price_total_exchange", digits=dp.get_precision('Product Price'))

    price_unit_exchange = fields.Float('Precio de Unidad', compute="_compute_price_unit_exchange", digits=dp.get_precision('Product Price'))

    @api.multi
    @api.depends("price_total")
    def _compute_price_total_exchange(self):
        for s in self:
            s.price_total_exchange = s.currency_id.compute(s.price_total, s.currency_report_id)

    @api.multi
    @api.depends("price_unit")
    def _compute_price_unit_exchange(self):
        for s in self:
            s.price_unit_exchange = s.currency_id.compute(s.price_unit, s.currency_report_id)
