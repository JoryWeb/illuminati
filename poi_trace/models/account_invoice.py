
from odoo import models, fields, api, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        if res and self:
            if self.move_id:
                self.move_id.add_source(self._name, self.id)
        return True
