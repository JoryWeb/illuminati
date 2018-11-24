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

import json
from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError, ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _create_bridge_move(self, line_to_reconcile, prepayment_line):

        moves = {}

        for inv in self:
            journal = inv.journal_id

            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)

            line1 =  {
                #'date_maturity': line.get('date_maturity', False),
                'partner_id': part.id,
                'name': u'Conciliación por Adelanto',
                'debit': prepayment_line.debit > 0 and 0 or prepayment_line.credit,
                'credit': prepayment_line.credit > 0 and 0 or prepayment_line.debit,
                'account_id': prepayment_line.account_id.id,
                #'analytic_line_ids': line.get('analytic_line_ids', []),
                #'amount_currency': line['price'] > 0 and abs(line.get('amount_currency', False)) or -abs(line.get('amount_currency', False)),
                #'currency_id': line.get('currency_id', False),
                #'quantity': line.get('quantity', 1.00),
                #'product_id': line.get('product_id', False),
                #'product_uom_id': line.get('uom_id', False),
                'analytic_account_id': prepayment_line.analytic_account_id.id,
                #'invoice_id': line.get('invoice_id', False),
                #'tax_ids': line.get('tax_ids', False),
                #'tax_line_id': line.get('tax_line_id', False),
            }

            line2 = {
                #'date_maturity': line.get('date_maturity', False),
                'partner_id': part.id,
                'name': 'Conciliación por Adelanto',
                'debit': prepayment_line.debit,
                'credit': prepayment_line.credit,
                'account_id': line_to_reconcile.account_id.id,
                #'analytic_line_ids': line.get('analytic_line_ids', []),
                #'amount_currency': line['price'] > 0 and abs(line.get('amount_currency', False)) or -abs(
                #    line.get('amount_currency', False)),
                #'currency_id': line.get('currency_id', False),
                #'quantity': line.get('quantity', 1.00),
                #'product_id': line.get('product_id', False),
                #'product_uom_id': line.get('uom_id', False),
                'analytic_account_id': prepayment_line.analytic_account_id.id,
                #'invoice_id': line.get('invoice_id', False),
                #'tax_ids': line.get('tax_ids', False),
                #'tax_line_id': line.get('tax_line_id', False),
            }

            line = [(0, 0, line1),(0, 0, line2)]
            move_ref = inv.reference and str(inv.reference) or str(inv.number)
            move_vals = {
                'ref': move_ref + str(_(' (Prepaid)')),
                'line_ids': line,
                'journal_id': journal.id,
                'date': inv.date_invoice,
                'narration': inv.comment,
                'src': 'account.invoice,' + str(inv.id),
            }

            move = self.env['account.move'].create(move_vals)
            move.post()

        return move

    @api.multi
    def register_prepayment(self, prepayment_line, writeoff_acc_id=False, writeoff_journal_id=False):
        """ Reconcile payable/receivable lines from the invoice with prepayment_line """

        #TODO: CREATE THE BRIDGE MOVE

        line_to_reconcile = self.env['account.move.line']
        for inv in self:
            line_to_reconcile += inv.move_id.line_ids.filtered(
                lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable')).sorted(key=lambda r: r.date_maturity)

            #CREATING BRIDGE
            for lr in line_to_reconcile:

                new_move = inv._create_bridge_move(lr, prepayment_line)

                bridge_move_line = False
                payment_line = False

                for line in new_move.line_ids:
                    if line.account_id.id == lr.account_id.id:
                        payment_line = line
                    elif line.account_id.id == prepayment_line.account_id.id:
                        bridge_move_line = line

                (bridge_move_line + prepayment_line).reconcile(writeoff_acc_id, writeoff_journal_id)
                break

        return (line_to_reconcile + payment_line).reconcile(writeoff_acc_id, writeoff_journal_id)

    @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        credit_aml = self.env['account.move.line'].browse(credit_aml_id)
        if not credit_aml.currency_id and self.currency_id != self.company_id.currency_id:
            credit_aml.with_context(allow_amount_currency=True).write({
                'amount_currency': self.company_id.currency_id.with_context(date=credit_aml.date).compute(
                    credit_aml.balance, self.currency_id),
                'currency_id': self.currency_id.id})

        if credit_aml.payment_id:
            credit_aml.payment_id.write({'invoice_ids': [(4, self.id, None)]})

        if credit_aml.payment_id and credit_aml.account_id and credit_aml.account_id.id != self.account_id.id:
            return self.register_prepayment(credit_aml)

        return self.register_payment(credit_aml)

    @api.one
    def _get_outstanding_info_JSON(self):
        self.outstanding_credits_debits_widget = json.dumps(False)
        if self.state == 'open':
            domain = [#('account_id', '=', self.account_id.id),
                      ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                      ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
            if self.type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _(u'Débitos pendientes')
            info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
            lines = self.env['account.move.line'].search(domain)
            currency_id = self.currency_id
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    if line.currency_id and line.currency_id == self.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        amount_to_show = line.company_id.currency_id.with_context(date=line.date).compute(
                            abs(line.amount_residual), self.currency_id)
                    if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                        continue
                    info['content'].append({
                        'journal_name': line.ref or line.move_id.name,
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'id': line.id,
                        'position': currency_id.position,
                        'digits': [69, self.currency_id.decimal_places],
                    })
                info['title'] = type_payment
                self.outstanding_credits_debits_widget = json.dumps(info)
                self.has_outstanding = True
