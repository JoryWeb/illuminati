# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
#import sets

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    # We will only support cards and checks

    #check_number = fields.Char('Check Number', size=16)
    #bank = fields.Many2one('res.bank', string='Bank')
    #transaction_date = fields.Date('Transaction Date') #Not needed
    card_code = fields.Char('Card Code') # TODO: All data must be char
    card_bank_owner = fields.Char('Card Owner', size=64)
    #bank_account_number = fields.Char('Bank Account Number', size=16)
    #transaction_number = fields.Char('Transaction Number', size=16)
    #client_code = fields.Integer('Card Code')
    #other_description = fields.Char('Other Description', size=64)