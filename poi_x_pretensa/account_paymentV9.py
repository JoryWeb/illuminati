# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class ModelName(models.Model):
    _inherit = "account.payment"

    @api.one
    def _compute_invoice_vendor_amount(self):
        amount = 0
        for invoice in self.invoice_ids:
            amount += invoice.amount_total
        if amount == 0:
            self.amount_consiled = amount
        elif amount >= self.amount:
            self.amount_consiled = self.amount
        else:
            self.amount_consiled = amount

    amount_consiled = fields.Float(
        string='Monto Conciliado',
        compute=_compute_invoice_vendor_amount)
