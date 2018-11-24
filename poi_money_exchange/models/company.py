
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from datetime import timedelta


class ResCompany(models.Model):
    _inherit = "res.company"

    journal_cash_exchange_id = fields.Many2one('account.journal', 'Diario cambio moneda')
    account_tc_cash_exchange_id = fields.Many2one('account.account', 'Cuenta Tasa de Cambio')
    tc_cash_exchange_id = fields.Many2one('res.currency', 'tasa de cambio moneda')
