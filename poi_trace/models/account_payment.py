
from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    state = fields.Selection(selection_add=[('cancel', 'Canceled')])

    def _get_move_vals(self, journal=None):
        res = super(AccountPayment, self)._get_move_vals(journal=journal)
        res['src'] = 'account.payment,' + str(self.id)
        return res

    @api.multi
    def cancel(self):
        for rec in self:
            for move in rec.move_line_ids.mapped('move_id'):
                if rec.invoice_ids:
                    move.line_ids.remove_move_reconcile()
                move.make_fixable()
                move.reverse_moves(date=move.date)
                move.make_unfixable()

            rec.state = 'cancel'
