
from odoo import api, fields, models, _

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sale_condition = fields.Many2one("sale.condition.payment", u'Cóndicion de pago')