##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2014 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Grover Menacho
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
#from odoo.report import report_sxw

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.one
    @api.constrains('journal_id', 'bank_account_id')
    def _check_journal_bank_id(self):
        if self.bank_account_id:
            if self.journal_id.type != 'bank':
                raise ValidationError(_('A bank account can only be applied to a bank journal.'))

    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account')
    bank_reconcile_id = fields.Many2one('account.bank.statement.reconcile', string='Bank Reconcile')
    bank_reconcile_comment = fields.Char('Bank Reconcile Comment')

    @api.one
    @api.constrains('lines')
    def prepare_move_lines_for_bank_reconciliation_widget(self, target_currency=False):
        """ Returns move lines formatted for the manual/bank reconciliation widget

            :param target_currency: curreny you want the move line debit/credit converted into
            :param target_date: date to use for the monetary conversion
        """
        if not self.lines:
            return []
        if self.env.context is None:
            context = {}
        ctx = context.copy()
        currency_obj = self.pool.get('res.currency')
        company_currency = self.pool.get('res.users').browse(self.env.uid).company_id.currency_id
        #rml_parser = report_sxw.rml_parse(self.env.cr, self.env.uid, 'reconciliation_widget_aml', context=self.env.context)
        ret = []

        for line in self.lines:
            partial_reconciliation_siblings_ids = []
            #if line.reconcile_partial_id:
            #    partial_reconciliation_siblings_ids = self.search(cr, uid, [
            #        ('reconcile_partial_id', '=', line.reconcile_partial_id.id)], context=context)
            #    partial_reconciliation_siblings_ids.remove(line.id)

            ret_line = {
                'id': line.id,
                'name': line.name != '/' and line.move_id.name + ': ' + line.name or line.move_id.name,
                'ref': line.move_id.ref or '',
                'account_code': line.account_id.code,
                'account_name': line.account_id.name,
                'account_type': line.account_id.type,
                'date_maturity': line.date_maturity,
                'date': line.date,
                'period_name': line.period_id.name,
                'journal_name': line.journal_id.name,
                'partner_id': line.partner_id.id,
                'partner_name': line.partner_id.name,
                'is_partially_reconciled': bool(line.reconcile_partial_id),
                'partial_reconciliation_siblings_ids': partial_reconciliation_siblings_ids,
            }

            # Amount residual can be negative
            debit = line.debit
            credit = line.credit
            amount = line.debit - line.credit
            amount_currency = line.amount_currency
            if amount < 0:
                debit, credit = credit, debit
                amount = -amount
                amount_currency = -amount_currency

            # Get right debit / credit:
            target_currency = target_currency or company_currency
            line_currency = line.currency_id or company_currency
            amount_currency_str = ""
            total_amount_currency_str = ""
            if line_currency != company_currency:
                total_amount = line.amount_currency
                actual_debit = debit > 0 and amount_currency or 0.0
                actual_credit = credit > 0 and amount_currency or 0.0
            else:
                total_amount = abs(debit - credit)
                actual_debit = debit > 0 and amount or 0.0
                actual_credit = credit > 0 and amount or 0.0
            if line_currency != target_currency:
                amount_currency_str = rml_parser.formatLang(actual_debit or actual_credit, currency_obj=line_currency)
                total_amount_currency_str = rml_parser.formatLang(total_amount, currency_obj=line_currency)
                ret_line['credit_currency'] = actual_credit
                ret_line['debit_currency'] = actual_debit
                if target_currency == company_currency:
                    actual_debit = debit > 0 and amount or 0.0
                    actual_credit = credit > 0 and amount or 0.0
                    total_amount = abs(debit - credit)
                else:
                    ctx = context.copy()
                    ctx.update({'date': line.date})
                    total_amount = currency_obj.compute(self.env.cr, self.env.uid, line_currency.id, target_currency.id, total_amount,
                                                        context=ctx)
                    actual_debit = currency_obj.compute(self.env.cr, self.env.uid, line_currency.id, target_currency.id, actual_debit,
                                                        context=ctx)
                    actual_credit = currency_obj.compute(self.env.cr, self.env.uid, line_currency.id, target_currency.id, actual_credit,
                                                         context=ctx)
            amount_str = rml_parser.formatLang(actual_debit or actual_credit, currency_obj=target_currency)
            total_amount_str = rml_parser.formatLang(total_amount, currency_obj=target_currency)

            ret_line['debit'] = actual_debit
            ret_line['credit'] = actual_credit
            ret_line['amount_str'] = amount_str
            ret_line['total_amount_str'] = total_amount_str
            ret_line['amount_currency_str'] = amount_currency_str
            ret_line['total_amount_currency_str'] = total_amount_currency_str
            ret.append(ret_line)
        return ret
