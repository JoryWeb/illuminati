import logging
from openerp import fields, models, api, _
from openerp.exceptions import Warning, ValidationError
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_total_exchange = fields.Float('Monto Total', compute="_compute_amount_total_exchange", digits=dp.get_precision('Product Price'))

    # amount_total_usd = fields.Float('Monto Total', compute="_compute_amount_total_usd", digits=dp.get_precision('Product Price'))

    @api.multi
    # @api.depends("amount_total")
    def _compute_amount_total_exchange(self):
        for s in self:
            s.amount_total_exchange = s.amount_total / s.company_id.currency_id.rate

    # @api.multi
    # @api.depends("amount_total")
    # def _compute_amount_total_usd(self):
    #     for s in self:
    #         if s.currency_id.name != 'USD':
    #             s.amount_total_usd = s.amount_total / s.company_id.currency_id.rate


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    price_subtotal_exchange = fields.Float('Monto Total', compute="_compute_price_subtotal_exchange", digits=dp.get_precision('Product Price'))

    price_unit_with_discount = fields.Float('Precio de Unidad con Descuento', compute="_compute_price_unit_with_discount", digits=dp.get_precision('Product Price'))

    @api.multi
    # @api.depends("price_subtotal_with_tax")
    def _compute_price_subtotal_exchange(self):
        for s in self:
            s.price_subtotal_exchange = s.price_subtotal_with_tax / s.company_id.currency_id.rate

    @api.multi
    # @api.depends("price_unit")
    def _compute_price_unit_with_discount(self):
        for s in self:
            s.price_unit_with_discount =  s.price_unit / s.company_id.currency_id.rate
