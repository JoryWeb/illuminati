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
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id','is_prepaid')
    def _compute_destination_account_id(self):
        super(AccountPayment, self)._compute_destination_account_id()
        if self.partner_id and self.is_prepaid:
            if self.partner_type == 'customer':
                if not self.partner_id.property_prepaid_account_receivable_id:
                    raise UserError(_('Prepaid Account Receivable account not defined on the partner.'))
                self.destination_account_id = self.partner_id.property_prepaid_account_receivable_id.id
            else:
                if not self.partner_id.property_prepaid_account_payable_id:
                    raise UserError(_('Prepaid Account Payable account not defined on the partner.'))
                self.destination_account_id = self.partner_id.property_prepaid_account_payable_id.id

    #Module MUST mark is_prepaid as TRUE when they want to use the prepaid accounts
    is_prepaid = fields.Boolean('Is Prepaid', default=False)
    # Money flows from the journal_id's default_debit_account_id or default_credit_account_id to the destination_account_id
    destination_account_id = fields.Many2one('account.account', compute='_compute_destination_account_id',
                                             readonly=True)
