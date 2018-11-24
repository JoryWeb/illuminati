from odoo import api, fields, models, _


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_journal_id = fields.Many2one('account.journal', 'Diario', related="company_id.journal_cash_exchange_id")
    default_account_tc_id = fields.Many2one('account.account', 'Cuenta Tasa de Cambio', related="company_id.account_tc_cash_exchange_id")
    default_tc_id = fields.Many2one('res.currency', 'Tasa de Cambio', related="company_id.tc_cash_exchange_id")


    @api.multi
    def set_account_cash_exhange(self):
        """ Set the product taxes if they have changed """
        ir_values_obj = self.env['ir.values']
        ir_values_obj.sudo().set_default('account.money.exchange', "journal_id", self.default_journal_id.id if self.default_journal_id else False, for_all_users=True, company_id=self.company_id.id)
        ir_values_obj.sudo().set_default('account.money.exchange', "tc", self.default_tc_id.id if self.default_tc_id else False, for_all_users=True, company_id=self.company_id.id)
        ir_values_obj.sudo().set_default('account.money.exchange', "account_tc_id", self.default_account_tc_id.id if self.default_account_tc_id else False, for_all_users=True, company_id=self.company_id.id)
