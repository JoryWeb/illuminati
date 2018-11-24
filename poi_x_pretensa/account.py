from openerp import api, fields, models, _
class AccountVoucher(models.Model):
    _inherit = "account.voucher"
    proveedor = fields.Char("Nombre Proveedor")


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.multi
    def _total_balance(self):
        for account in self:
            self._cr.execute("""
            SELECT (sum(t0.debit)- sum(t0.credit)) as balance, sum(t0.debit) as debito, sum(t0.credit) as credito
            FROM account_move_line t0
            INNER JOIN account_move t1 on t1.id = t0.move_id
            WHERE t1.state in ('posted') AND t0.account_id = """ + str(account.id) + """
            """)
            res = self._cr.dictfetchall()
            for r in res:
                account.balance = r['balance']
                account.debito = r['debito']
                account.credito = r['credito']
        #self.payment_move_line_ids = self.env['account.move.line'].browse(list(set(payment_lines)))

    balance = fields.Float(u"Balance", compute='_total_balance')
    debito = fields.Float(u"Débito", compute='_total_balance')
    credito = fields.Float(u"Crédito", compute='_total_balance')
