from odoo import models, fields, api, _


class AccountVoucher(models.Model):
    _inherit = "account.voucher"

    @api.multi
    def account_move_get(self):
        res = super(AccountVoucher, self).account_move_get()
        res['src'] = 'account.voucher,' + str(self.id)
        return res
