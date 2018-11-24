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
#-from odoo.report import report_sxw

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.one
    @api.depends('payment_type', 'journal_id', 'destination_journal_id')
    def _compute_hide_payment_method(self):
        if not self.journal_id:
            self.hide_payment_method = True
            return
        journal_payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or \
                                  self.journal_id.outbound_payment_method_ids
        dest_journal_payment_methods = self.payment_type == 'trasfer' and \
                                       self.destination_journal_id.inbound_payment_method_ids or \
                                       self.destination_journal_id.outbound_payment_method_ids
        inbound_hide = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'
        if dest_journal_payment_methods:
            transfer_hide = len(dest_journal_payment_methods) == 1 and dest_journal_payment_methods[0].code == 'manual'
        else:
            transfer_hide = True
        self.hide_payment_method= inbound_hide and transfer_hide


    #General fields
    bank_id = fields.Many2one('res.bank', 'Bank')
    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account')
    bank_card_issuer = fields.Selection([('visa', 'Visa'),
                                       ('master_card', 'Master Card'),
                                       ('american_express', 'American Express')], 'Card Issuer')
    bank_card_type = fields.Selection([('debit','Debit'),
                                       ('credit','Credit'),
                                       ('prepaid','Prepaid')], 'Card Type')
    other_payment_data = fields.Char('Other Payment Data')

    #Outbound payments
    checkbook_id = fields.Many2one('res.bank.account.checkbook', string='Checkbook')
    check_id = fields.Many2one('res.bank.account.check', 'Check')
    bank_card_id = fields.Many2one('res.bank.card', 'Card')

    #Inbound Payments
    bank_card_code = fields.Char('Bank Card Code',help='Last digits of card')


    #For destination
    destination_bank_id = fields.Many2one('res.bank', 'Destination Bank')
    destination_bank_account_id = fields.Many2one('res.bank.account', string='Destination Bank Account')

    journal_type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'Miscellaneous'),
    ], related='journal_id.type', readonly=True)

    destination_journal_type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'Miscellaneous'),
    ], related='destination_journal_id.type', readonly=True)

    @api.onchange('destination_bank_id')
    def _onchange_destination_bank_id(self):
        # Set partner_id domain
        if self.destination_bank_id:
            return {'domain': {'destination_bank_account_id': [('bank_id', '=', self.destination_bank_id.id)]}}

    @api.onchange('bank_id')
    def _onchange_bank_id(self):
        # Set partner_id domain
        if self.bank_id:
            return {'domain': {'bank_account_id': [('bank_id', '=', self.bank_id.id)]}}

    @api.multi
    def generate_check_wizard(self):
        check_id = False
        for p in self:
            generate_check = False
            if p.checkbook_id and p.check_id and p.check_id.state == 'annulled':
                generate_check = True
            elif p.checkbook_id and not p.check_id:
                generate_check = True
            elif p.check_id and p.check_id.state != 'annulled':
                raise ValidationError(_("Error. You cannot generate another check unless the check is annulled."))

            if generate_check:
                check_id = p.checkbook_id.generate_check(p.amount, date=p.payment_date, payee=p.partner_id.name,
                                                         memo=p.communication) #WE NEED TO CONVERT THE AMOUNT
                p.write({'check_id': check_id.id})

        return True

    @api.multi
    def generate_check(self):
        check_id = False
        for v in self:
            generate_check = False
            if v.checkbook_id and v.check_id and v.check_id.state == 'annulled':
                generate_check = True
            elif v.checkbook_id and not v.check_id:
                generate_check = True
            elif v.check_id and v.check_id.state != 'annulled':
                raise ValidationError(_("Error. You cannot generate another check unless the check is annulled."))

            if generate_check:
                check_id = v.checkbook_id.generate_check(v.amount, date=v.date, payee=v.partner_id.name,
                                                         memo=v.name)  # WE NEED TO CONVERT THE AMOUNT
                v.write({'check_id': check_id.id})

        return True

    def _get_liquidity_move_line_vals(self, amount):
        """ Returns values common to both move lines (except for debit, credit and amount_currency which are reversed)
        """
        res = super(AccountPayment, self)._get_liquidity_move_line_vals(amount)

        if self.bank_account_id:
            res['bank_account_id'] = self.bank_account_id.id
            if self.bank_account_id.account_id:
                res['account_id'] = self.bank_account_id.account_id.id

        return res


    #Override... If we can inherit this on future version. Let's do that
    def _create_transfer_entry(self, amount):
        """ Create the journal entry corresponding to the 'incoming money' part of an internal transfer,
        return the reconciliable move line
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, dummy = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
        amount_currency = self.destination_journal_id.currency_id and self.currency_id.with_context(date=self.payment_date).compute(amount, self.destination_journal_id.currency_id) or 0

        dst_move = self.env['account.move'].create(self._get_move_vals(self.destination_journal_id))

        dst_liquidity_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, dst_move.id)

        #override
        if self.destination_bank_account_id:
            dest_account_id = self.destination_bank_account_id.account_id
            dst_liquidity_aml_dict.update({
                'bank_account_id': self.destination_bank_account_id.id
            })
        else:
            dest_account_id = self.destination_journal_id.default_credit_account_id
        #end override

        dst_liquidity_aml_dict.update({
            'name': _('Transfer from %s') % self.journal_id.name,
            #'account_id': self.destination_journal_id.default_credit_account_id.id,
            'account_id': dest_account_id.id,
            'currency_id': self.destination_journal_id.currency_id.id,
            'payment_id': self.id,
            'journal_id': self.destination_journal_id.id})

        aml_obj.create(dst_liquidity_aml_dict)

        transfer_debit_aml_dict = self._get_shared_move_line_vals(credit, debit, 0, dst_move.id)
        transfer_debit_aml_dict.update({
            'name': self.name,
            'payment_id': self.id,
            'account_id': self.company_id.transfer_account_id.id,
            'journal_id': self.destination_journal_id.id})
        if self.currency_id != self.company_id.currency_id:
            transfer_debit_aml_dict.update({
                'currency_id': self.currency_id.id,
                'amount_currency': -self.amount,
            })
        transfer_debit_aml = aml_obj.create(transfer_debit_aml_dict)
        dst_move.post()
        return transfer_debit_aml