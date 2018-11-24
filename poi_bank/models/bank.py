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

from operator import itemgetter
from lxml import etree

from openerp import models, fields, api, _
from openerp.osv import expression
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.exceptions import Warning as UserError
from openerp.exceptions import ValidationError



class ResBank(models.Model):
    _inherit = 'res.bank'

    code = fields.Char(u'Código banco', required=False)
    bic = fields.Char(u'Código Swift', index=True, help="Sometimes called BIC or Swift.")   #Nativo
    iban = fields.Char(u'Código IBAN', required=False)
    bank_account_ids = fields.One2many('res.bank.account','bank_id','Bank Accounts')


class ResBankCard(models.Model):
    _name = 'res.bank.card'
    _description = 'Bank Cards'

    name = fields.Char("Card Code (XXXX-XXXX-XXXX-NNNN)")
    bank_card_type = fields.Selection([('debit', 'Debit'),
                                       ('credit', 'Credit'),
                                       ('prepaid', 'Prepaid')], 'Card Type')
    bank_card_issuer = fields.Selection([('visa', 'Visa'),
                                         ('master_card', 'Master Card'),
                                         ('american_express', 'American Express')], 'Card Issuer')
    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account')



class BankAccount(models.Model):
    _name = 'res.bank.account'
    _description = 'Bank Accounts'

    @api.multi
    def _compute_debit_credit_balance(self):
        account_move_line_obj = self.env['account.move.line']
        domain = []
        if self._context.get('from_date', False):
            domain.append(('date', '>=', self._context['from_date']))
        if self._context.get('to_date', False):
            domain.append(('date', '<=', self._context['to_date']))

        bank_account_ids = self.mapped('id')
        data_debit = {bank_account_id: 0.0 for bank_account_id in bank_account_ids}
        data_credit = {bank_account_id: 0.0 for bank_account_id in bank_account_ids}

        for bank_account in self:
            bank_domain = []
            bank_domain = bank_domain + domain
            bank_domain.append(('bank_account_id','=',bank_account.id))

            bank_account_amounts = account_move_line_obj.search_read(bank_domain, ['bank_account_id', 'debit', 'credit', 'amount_currency', 'currency_id'])


            #Testing currency:
            base_currency = True
            if bank_account.company_id.currency_id.id != bank_account.currency_id.id:
                base_currency = False


            for bank_account_amount in bank_account_amounts:
                if bank_account_amount['debit'] > 0.0:
                    data_debit[bank_account_amount['bank_account_id'][0]] += base_currency and bank_account_amount['debit'] or bank_account_amount['amount_currency']
                else:
                    data_credit[bank_account_amount['bank_account_id'][0]] += base_currency and bank_account_amount['credit'] or bank_account_amount['amount_currency']

        for bank_account in self:
            bank_account.debit = abs(data_debit.get(bank_account.id, 0.0))
            bank_account.credit = data_credit.get(bank_account.id, 0.0)
            bank_account.balance = abs(data_debit.get(bank_account.id, 0.0)) - data_credit.get(bank_account.id, 0.0)
            bank_account.balance_reconciled = 0.0

    # name = fields.Char(string='')
    active = fields.Boolean(string='Active', default=True)
    bank_id = fields.Many2one('res.bank', string='Bank', required=True)
    account_type = fields.Selection([('savings', 'Savings Account'), ('checking', 'Checking Account')],
                                    string='Account Type', required=True)
    account_number = fields.Char('Account Number', required=True)
    account_id = fields.Many2one('account.account', string='Accounting Account', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    journal_id = fields.Many2one('account.journal', 'Journal')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    partner_id = fields.Many2one('res.partner', 'Account Owner')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Project') # PROJECT
    description = fields.Char('Description')
    account_checkbook_ids = fields.One2many('res.bank.account.checkbook', 'bank_account_id', 'Checkbooks')

    balance = fields.Float(string='Balance', compute=_compute_debit_credit_balance, search="_search_balance")
    debit = fields.Float(string='Debit', compute=_compute_debit_credit_balance)
    credit = fields.Float(string='Credit', compute=_compute_debit_credit_balance)

    balance_reconciled = fields.Float(string='Saldo Conciliado', compute=_compute_debit_credit_balance)

    @api.multi
    @api.depends('bank_id', 'account_number','currency_id')
    def name_get(self):
        result = []
        for account in self:
            name = '%s - %s (%s)' % (account.bank_id.name, (account.account_number and account.account_number or ''), account.currency_id.name)
            result.append((account.id, name))
        return result

    def _search_balance(self, operator, value):
        domain = []
        bank_ids = []
        if operator == '<=':
            for b in self.env['res.bank.account'].search([]):
                if b.balance <= 0:
                    bank_ids.append(b.id)
            domain.append(['id', 'in', bank_ids])
        if operator == '>':
            for b in self.env['res.bank.account'].search([]):
                if b.balance > 0:
                    bank_ids.append(b.id)
            domain.append(['id', 'in', bank_ids])
        return domain

class BankAccountCheckbook(models.Model):
    _name = 'res.bank.account.checkbook'

    name = fields.Char(string='Checkbook Description', required=True)
    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account')
    bank_id = fields.Many2one('res.bank', string='Bank', related='bank_account_id.bank_id', store=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', related='bank_account_id.company_id', store=True)

    ref = fields.Char(string='Reference')
    start_num = fields.Integer(string='Start Number', required=True)
    end_num = fields.Integer(string='End Number', required=True)
    next_num = fields.Integer(string='Next Number', readonly=True)
    active = fields.Boolean(string='Active', default=True)

    check_ids = fields.One2many('res.bank.account.check', 'checkbook_id', 'Checks generated')

    @api.one
    @api.returns('res.bank.account.check')
    def generate_check(self, amount, date=False, payee='', memo=''):
        check_obj = self.env['res.bank.account.check']
        check_id = False
        for cb in self:
            if cb.check_missing_values():
                check_id = check_obj.create({'checkbook_id': cb.id,
                                             'amount': amount,
                                             'date': date and date or date, #SET NOW DATE
                                             'payee': payee,
                                             'memo': memo})
        if check_id:
            return check_id
        else:
            raise ValidationError(_('The check was not generated properly'))

    #TODO: Evaluate if this works without api.multi
    def check_missing_values(self):
        checks = [x.check_number for x in self.check_ids]

        checks.sort()
        if checks:
            return True
        return True

    # TODO: Evaluate if this works without api.multi
    def get_last_value(self):
        checks = [x.check_number for x in self.check_ids]
        max_val = self.end_num
        if checks:
            checks.sort(reverse=True)
            if checks[0] >= max_val:
                raise ValidationError(
                    _("You've reached the maximum value for this checkbook. Please user another checkbook"))
            return checks[0]
        else:
            return self.start_num


class BankAccountCheck(models.Model):
    _name = 'res.bank.account.check'

    check_number = fields.Integer(string='Check Number')
    checkbook_id = fields.Many2one('res.bank.account.checkbook', string='Checkbook')
    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account', related='checkbook_id.bank_account_id',
                                      store=True, readonly=True)
    bank_id = fields.Many2one('res.bank', string='Bank', related='checkbook_id.bank_id', store=True, readonly=True)
    date = fields.Date('Date', default=lambda self: fields.Date.today())
    amount = fields.Float('Amount', group_operator="sum")
    payee = fields.Char('Pay to the order of')# girado a
    memo = fields.Char('Memo')# concepto
    state = fields.Selection([('draft', 'Draft'),
                              ('validated', 'Validated'),
                              ('printed', 'Printed'),
                              ('signed', 'Signed'),
                              ('delivered', 'Delivered'),
                              ('cashed', 'Cashed'),
                              ('annulled', 'Annulled')], string='State', default='draft')

    @api.multi
    @api.depends('bank_id', 'bank_account_id', 'check_number')
    def name_get(self):
        result = []
        for check in self:
            name = _('(%s - %s) Check: %s') % (
                check.bank_id.name, (check.checkbook_id.name or ''), check.check_number)
            result.append((check.id, name))
        return result

    @api.multi
    def validate_check(self):
        cb = self.checkbook_id

        if self.amount <= 0.0:
            raise ValidationError(_('You cannot validate a check with a zero or negative amount'))

        if cb.check_missing_values():
            last_value = cb.get_last_value()
            cb.write({'next_num': cb.end_num > last_value + 1 and last_value + 2 or cb.end_num})
            return self.write({'state': 'validated', 'check_number': last_value + 1})
        else:
            return {}

    @api.multi
    def print_check(self):
        return self.write({'state': 'printed'})

    @api.multi
    def annul_check(self):
        cb = self.checkbook_id
        last_value = cb.get_last_value()
        if self.check_number == last_value:
            cb.write({'next_num': self.check_number})
            return self.write({'state': 'annulled', 'check_number': 0})
        else:
            raise ValidateError(_(u'El cheque a ser anulado no es el último. No puede ser anulado'))


    @api.multi
    def annul_check_printed(self):
        return self.write({'state': 'annulled'})

    @api.multi
    def mark_as_signed(self):
        return self.write({'state': 'signed'})

    @api.multi
    def mark_as_delivered(self):
        if self.state == 'signed':
            return self.write({'state': 'delivered'})
        else:
            return {}

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        """
        Override: Set the default view on check selection
        """
        res = super(BankAccountCheck, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                          submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            #if self._context.get('default_type', False) not in ('in_invoice', 'in_refund'):
            #    for node in doc.xpath("//field[@name='approval_user_id']"):
            #        doc.remove(node)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def unlink(self):
        for check in self:
            if check.state != 'draft':
                raise UserError(
                    _("The check '%s' is not in draft state. "
                      "Please annul it.")
                    % check.check_number)
        return super(BankAccountCheck, self).unlink()