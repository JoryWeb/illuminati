##############################################################################
#
#    Odoo Module
#    Copyright (C) 2015 Grover Menacho (<http://www.grovermenacho.com>).
#    Copyright (C) 2015 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Grover Menacho
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

import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from odoo.exceptions import Warning as UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cash_movement_id = fields.Many2one('account.cash.movement', 'Cash Movement')

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        if self.env.context.get("default_cash_movement_id"):
            cash_movement_id_default = self.env['account.cash.movement'].browse(self.env.context.get("default_cash_movement_id"))
            rec['cash_movement_id'] = cash_movement_id_default.id
            rec['communication'] = cash_movement_id_default.name
            rec['currency_id'] = cash_movement_id_default.currency_id.id
            if cash_movement_id_default.payment_type == 'outbound':
                rec['payment_type'] = 'outbound'
                rec['partner_type'] = 'supplier'
            else:
                rec['payment_type'] = 'inbound'
                rec['partner_type'] = 'customer'
            rec['partner_id'] = cash_movement_id_default.partner_id and cash_movement_id_default.partner_id.id or False
            rec['amount'] = cash_movement_id_default.amount_residual
            #We add the account
            rec['destination_account_id'] = cash_movement_id_default.type.account_id.id
            if cash_movement_id_default.account_analytic_id:
                rec['analytic_account_id'] = cash_movement_id_default.account_analytic_id.id

            if 'payment_request_id' in cash_movement_id_default._fields:
                if cash_movement_id_default.payment_request_id:
                    rec['transaction_date'] = cash_movement_id_default.payment_request_id.payment_date
                    rec['transaction_number'] = cash_movement_id_default.payment_request_id.payment_code
                    rec['other_payment_data'] = cash_movement_id_default.payment_request_id.no_voucher
                    if cash_movement_id_default.payment_request_id.journal_id:
                        rec['journal_id'] = cash_movement_id_default.payment_request_id.journal_id.id
                    if cash_movement_id_default.payment_request_id.payment_method_id:
                        rec['payment_method_id'] = cash_movement_id_default.payment_request_id.payment_method_id.id
                    if cash_movement_id_default.payment_request_id.bank_id:
                        rec['bank_id'] = cash_movement_id_default.payment_request_id.bank_id.id

        return rec

    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        super(AccountPayment, self)._compute_destination_account_id()
        if self.cash_movement_id:
            self.destination_account_id = self.cash_movement_id.type.account_id.id

    @api.multi
    def post(self):
        for payment in self:
            if payment.payment_type == 'transfer':
                payment._create_transfer()
            else:
                super(AccountPayment, self).post()
            if payment.cash_movement_id:
                payment.cash_movement_id.test_paid()

    destination_account_id = fields.Many2one('account.account', compute='_compute_destination_account_id',
                                             readonly=True)

    @api.multi
    def _create_transfer(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Use the right sequence to set the name
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'

            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            # move = rec._create_payment_entry_transfer_edition(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                # transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == self.journal_id.default_credit_account_id.id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                # (transfer_credit_aml + transfer_debit_aml)

            rec.state = 'posted'


    @api.multi
    def _create_payment_entry_transfer_edition(self, amount):
            """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
                Return the journal entry.
            """
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            invoice_currency = False
            if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
                #if all the invoices selected share the same currency, record the paiement in that currency too
                invoice_currency = self.invoice_ids[0].currency_id
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)

            move = self.env['account.move'].create(self._get_move_vals())

            move.post()
            return move

    def _create_transfer_entry(self, amount):
        """ Create the journal entry corresponding to the 'incoming money' part of an internal transfer, return the reconciliable move line
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        amount_currency = self.destination_journal_id.currency_id and self.currency_id.with_context(date=self.payment_date).compute(amount, self.destination_journal_id.currency_id) or 0

        dst_move = self.env['account.move'].create(self._get_move_vals(self.journal_id))

        transfer_debit_aml_dict = self._get_shared_move_line_vals(credit, debit, 0, dst_move.id)
        transfer_debit_aml_dict.update({
            'name': _('Transfer from %s') % self.journal_id.name,
            'account_id': self.journal_id.default_credit_account_id.id,
            'currency_id': self.journal_id.currency_id.id,
            'payment_id': self.id,
            'journal_id': self.journal_id.id,
            'bank_account_id': (self.bank_account_id and self.bank_account_id.id) or False,
            'cashier_id': (self.cashier_id and self.cashier_id.id) or False,
            })
        if self.currency_id != self.company_id.currency_id:
            transfer_debit_aml_dict.update({
                'currency_id': self.currency_id.id,
                'amount_currency': -self.amount,
            })

        dst_liquidity_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, dst_move.id)
        dst_liquidity_aml_dict.update({
            'name': self.name,
            'payment_id': self.id,
            'account_id': self.destination_journal_id.default_credit_account_id.id,
            'currency_id': self.destination_journal_id.currency_id.id,
            'journal_id': self.destination_journal_id.id,
            'bank_account_id': (self.destination_bank_account_id and self.destination_bank_account_id.id) or False,
            'cashier_id':( self.cashier_id and self.cashier_id.id) or False,
        })
        aml_obj.create(dst_liquidity_aml_dict)



        transfer_debit_aml = aml_obj.create(transfer_debit_aml_dict)
        dst_move.post()
        return transfer_debit_aml

    @api.model
    def chek_pay_transfer(self):
        payment_ids = self.search([('payment_type', '=', 'transfer'), ('state', '=', 'posted')])
        for p in payment_ids:
            for aml in p.move_line_ids:
                if aml.journal_id.type == 'bank':
                    if aml.debit > 0 and not aml.bank_account_id:
                        aml.bank_account_id = p.destination_bank_account_id and  p.destination_bank_account_id.id or False
                    elif aml.credit > 0 and not aml.bank_account_id:
                        aml.bank_account_id = p.bank_account_id and p.bank_account_id.id or False
                aml.cashier_id = p.cashier_id and p.cashier_id.id or False
