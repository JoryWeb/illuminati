
from odoo import models, fields, api, _


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _prepare_reconciliation_move(self, move_name):
        res = super(AccountBankStatementLine, self)._prepare_reconciliation_move(move_name)
        res['src'] = "account.bank.statement.line," + str(self.id)
        return res
