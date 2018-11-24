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

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    rendition_id = fields.Many2one('account.expenses.rendition', 'Rendition')
    rendition_line_id = fields.Many2one('account.expenses.rendition.invoice', 'Rendition Invoice')


class AccountExpensesInvoiceType(models.Model):
    _name = 'account.expenses.invoice.type'
    _description = 'Account Expenses Invoice Type'

    name = fields.Char('Invoice Type')
    account_id = fields.Many2one('account.account', 'Account', required=True, domain=[('deprecated', '=', False)])
    force_analytic_account = fields.Boolean('Force Analytic Account')
    analytic_account_id = fields.Many2one('account.analytic.account')
    taxes_ids = fields.Many2many('account.tax','account_expenses_invoice_type_taxes_rel','type_id','tax_id','Taxes')

class AccountExpensesRendition(models.Model):
    _name = 'account.expenses.rendition'
    _description = 'Expenses Rendition'
    _inherit = ['mail.thread']


    @api.multi
    @api.depends('rendition_invoice_ids.amount','invoice_ids','rendition_invoice_ids','payment_request_id')
    def _compute_rendition(self):
        for rendition in self:
            if not rendition.currency_id:
                rendition.currency_id = rendition.company_currency_id.id
            total = 0.00
            for rendition_inv in rendition.rendition_invoice_ids:
                total += rendition.user_id.company_id.currency_id.compute(rendition_inv.amount_included, rendition.currency_id)
            for acc_inv in rendition.invoice_ids:
                total += acc_inv.currency_id.compute(acc_inv.amount_total, rendition.currency_id)
            rendition.invoice_total = total

            already_rended = 0.0
            to_rend = 0.0
            if rendition.payment_request_id:
                for old_rend in rendition.payment_request_id.rendition_ids:
                    if old_rend.id != rendition.id and old_rend.state == 'done':
                        already_rended+=old_rend.invoice_total

                to_rend = rendition.payment_request_id.amount_total - already_rended

            rendition.amount_debt = total <= to_rend and to_rend - total or 0.0
            rendition.amount_exceeded = total > to_rend and total - to_rend or 0.0

    name = fields.Char('Name')

    user_id = fields.Many2one('res.users', 'Requestor', default=lambda self: self.env.user, required=True)

    payment_request_id = fields.Many2one('account.payment.request', 'Payment Request', ondelete='restrict')
    ref = fields.Char('Reference')
    rendition_date = fields.Date('Date', default=lambda self: fields.Date.today())

    #calculated
    currency_id = fields.Many2one('res.currency', "Currency", required=True, default=lambda self: self.env.user.company_id.currency_id, help="Seleccionar la moneda para la rendicion. En caso de que la rendicion este basada en una Solicitud, se adoptara la moneda de esa Solicitud automaticamente.")
    amount_requested = fields.Float('Amount Requested', related='payment_request_id.amount_total')
    invoice_total = fields.Float('Invoice Total', compute="_compute_rendition")
    amount_debt = fields.Float('Amount Debt', compute="_compute_rendition")
    amount_exceeded = fields.Float('Amount Exceeded', compute="_compute_rendition")

    rendition_invoice_ids = fields.One2many('account.expenses.rendition.invoice','rendition_id','Invoices', copy=True)

    invoice_ids = fields.Many2many('account.invoice','account_expenses_rendition_invoice_rel', 'rendition_id', 'invoice_id', string='Purchase Invoices', domain=[('type','=','in_invoice')])
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)

    notes = fields.Text('Notes')
    state = fields.Selection([('draft','Draft'),
                              ('confirmed','Confirmed'),
                              ('done','Done'),
                              ('cancel', 'Canceled')], 'State', default='draft')

    #For assets
    account_id = fields.Many2one("account.account", "Account", required=True)
    journal_id = fields.Many2one("account.journal", "Journal", required=True)
    move_id = fields.Many2one("account.move", "Move",copy=False)
    tax_line_ids = fields.One2many('account.expenses.rendition.tax', 'rendition_id', string='Tax Lines', copy=False)

    @api.onchange('payment_request_id')
    def onchange_payment_request_id(self):
        if self.payment_request_id:
            self.amount_requested = self.payment_request_id.amount_total
            self.currency_id = self.payment_request_id.amount_currency_id

    @api.multi
    def action_validate(self):
        seq = self.env['ir.sequence']
        code = seq.next_by_code('expenses.rendition') or '/'
        if  self.payment_request_id:
            self.payment_request_id.total_rendition += self.invoice_total
        self.write({'state': 'confirmed', 'name': code})
        return True

    @api.multi
    def _generate_moves(self):
        return True

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_approve(self):
        self.write({'state': 'done'})
        self.compute_taxes()
        if self.rendition_invoice_ids:
            self.action_move_create()
        if self.payment_request_id:
            self.payment_request_id.test_outbound_paid()
        return True

    def _prepare_tax_line_vals(self, line, tax):
        """ Prepare values to create an account.invoice.tax line

        The line parameter is an account.invoice.line, and the
        tax parameter is the output of account.tax.compute_all().
        """
        vals = {
            'rendition_id': self.id,
            'name': tax['name'],
            'tax_id': tax['id'],
            'amount': tax['amount'],
            'base': tax['base'],
            'manual': False,
            'sequence': tax['sequence'],
            'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
            'account_id': tax['account_id'] or (line.account_id and line.account_id.id) or line.invoice_type.account_id.id,
        }

        # If the taxes generate moves on the same financial account as the invoice line,
        # propagate the analytic account from the invoice line to the tax line.
        # This is necessary in situations were (part of) the taxes cannot be reclaimed,
        # to ensure the tax move is allocated to the proper analytic account.
        if not vals.get('account_analytic_id') and line.account_analytic_id and vals['account_id'] == line.invoice_type.account_id.id:
            vals['account_analytic_id'] = line.account_analytic_id.id

        return vals

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.rendition_invoice_ids:
            taxes = line.taxes_ids.compute_all(line.amount)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.multi
    def compute_taxes(self):
        """Function used in other module to compute the taxes on a fresh invoice created (onchanges did not applied)"""
        account_expenses_rendition_tax = self.env['account.expenses.rendition.tax']
        ctx = dict(self._context)
        for rendition in self:
            # Delete non-manual tax lines
            self._cr.execute("DELETE FROM account_expenses_rendition_tax WHERE rendition_id=%s AND manual is False", (rendition.id,))
            self.invalidate_cache()

            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped = rendition.get_taxes_values()

            # Create new tax lines
            for tax in tax_grouped.values():
                account_expenses_rendition_tax.create(tax)

        # dummy write on self to trigger recomputations
        return self.with_context(ctx).write({'rendition_invoice_ids': []})


    @api.model
    def rendition_invoice_line_move_line_get(self):
        res = []
        for line in self.rendition_invoice_ids:
            tax_ids = []
            for tax in line.taxes_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))

            move_line_dict = {
                'rendition_line_id': line.id,
                'type': 'src',
                'name': line.name or '',
                'price': line.amount_subtotal,
                'account_id': line.account_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'tax_ids': tax_ids,
                'rendition_id': self.id,
            }
            if line['account_analytic_id']:
                move_line_dict['analytic_line_ids'] = [(0, 0, line._get_analytic_line())]
            res.append(move_line_dict)
        return res

    @api.model
    def tax_line_move_line_get(self):
        res = []
        for tax_line in self.tax_line_ids:
            if tax_line.amount:
                res.append({
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount,
                    'quantity': 1,
                    'price': tax_line.amount,
                    'account_id': tax_line.account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'rendition_id': self.id,
                })
        return res

    @api.multi
    def compute_invoice_totals(self, company_currency, rendition_move_lines):
        total = 0
        total_currency = 0
        if not self.currency_id:
            raise UserError(_('Debe definir una moneda.'))
        for line in rendition_move_lines:
            if self.currency_id != company_currency:
                currency = self.currency_id.with_context(date=self.rendition_date or fields.Date.context_today(self))
                if not (line.get('currency_id') and line.get('amount_currency')):
                    line['currency_id'] = currency.id
                    line['amount_currency'] = currency.round(line['price'])
                    line['price'] = currency.compute(line['price'], company_currency)
            else:
                line['currency_id'] = False
                line['amount_currency'] = False
                line['price'] = self.currency_id.round(line['price'])

            #TODO: Validate this part
            total -= line['price']
            total_currency -= line['amount_currency'] or line['price']
        return total, total_currency, rendition_move_lines

    @api.model
    def line_get_convert(self, line, part):
        return {
            'date_maturity': line.get('date_maturity', False),
            'partner_id': part,
            'name': line['name'][:64],
            'debit': line['price'] > 0 and line['price'],
            'credit': line['price'] < 0 and -line['price'],
            'account_id': line['account_id'],
            'analytic_line_ids': line.get('analytic_line_ids', []),
            'amount_currency': line['price'] > 0 and abs(line.get('amount_currency', False)) or -abs(
                line.get('amount_currency', False)),
            'currency_id': line.get('currency_id', False),
            'quantity': line.get('quantity', 1.00),
            'product_id': line.get('product_id', False),
            'product_uom_id': line.get('uom_id', False),
            'analytic_account_id': line.get('account_analytic_id', False),
            'rendition_id': line.get('rendition_id', False),
            'tax_ids': line.get('tax_ids', False),
            'tax_line_id': line.get('tax_line_id', False),
        }

    @api.multi
    def action_move_create(self):
        """ Creates the account move and move lines """
        account_move = self.env['account.move']

        for rendition in self:
            if not rendition.journal_id:
                raise UserError(_('Please define a journal.'))
            #We can validate it even if there are only invoices related
            #if not rendition.rendition_invoice_ids:
            #    raise UserError(_('.'))
            if rendition.move_id:
                continue

            ctx = dict(self._context, lang=rendition.user_id.partner_id.lang)

            #rendition.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})

            rendition_date = rendition.rendition_date
            company_currency = rendition.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            rml = rendition.rendition_invoice_line_move_line_get()
            rml += rendition.tax_line_move_line_get()

            diff_currency = rendition.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, rml = rendition.with_context(ctx).compute_invoice_totals(company_currency, rml)

            #Asset line with no payment term
            rml.append({
                'type': 'dest',
                'name': rendition.name,
                'price': total,
                'account_id': rendition.account_id.id,
                'amount_currency': diff_currency and total_currency,
                'currency_id': diff_currency and rendition.currency_id.id,
                'rendition_id': rendition.id
            })

            part = self.env['res.partner']._find_accounting_partner(rendition.user_id.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in rml]

            journal = rendition.journal_id.with_context(ctx)

            date = rendition_date
            move_vals = {
                'ref': rendition.name,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': rendition.notes,
                'src': 'account.expenses.rendition,' + str(rendition.id)
            }
            ctx['company_id'] = rendition.company_id.id
            ctx['dont_create_taxes'] = True
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
            }
            rendition.with_context(ctx).write(vals)
        return True

    @api.multi
    def action_cancel(self):

        for rend in self:
            if rend.move_id:
                rend.move_id.make_fixable()
                rend.move_id.reverse_moves(date=rend.move_id.date)
                rend.move_id.make_unfixable()

            rend.write({'state': 'cancel'})
            if self.payment_request_id:
                self.payment_request_id.total_rendition -= self.invoice_total

        return True


class AccountExpensesRenditionInvoice(models.Model):
    _name = 'account.expenses.rendition.invoice'
    _description = 'Expenses Rendition Invoices'

    @api.multi
    @api.depends('amount', 'taxes_ids')
    def _compute_amount(self):
        for s in self:
            currency = s.rendition_id and s.rendition_id.currency_id or None
            taxes = False
            if s.taxes_ids:
                taxes = s.taxes_ids.compute_all(s.amount, currency, partner=s.rendition_id.user_id.partner_id)
            s.amount_subtotal = amount_subtotal_signed = taxes['total_excluded'] if taxes else s.amount
            s.amount_included = taxes['total_included'] if taxes else s.amount
            if s.rendition_id.currency_id and s.rendition_id.company_id and s.rendition_id.currency_id != s.rendition_id.company_id.currency_id:
                amount_subtotal_signed = s.rendition_id.currency_id.compute(amount_subtotal_signed,
                                                                            s.rendition_id.company_id.currency_id)
            s.amount_subtotal_signed = amount_subtotal_signed

    @api.onchange('invoice_type')
    def onchange_invoice_type(self):
        if self.invoice_type:
            self.account_id = self.invoice_type.account_id
            self.account_analytic_id = self.invoice_type.analytic_account_id
            self.taxes_ids = self.invoice_type.taxes_ids

    rendition_id = fields.Many2one('account.expenses.rendition', 'Rendition')
    state = fields.Selection(related='rendition_id.state', string='Estado doc', readonly=True, default='draft')
    name = fields.Char('Name', required=True)
    invoice_type = fields.Many2one('account.expenses.invoice.type', 'Invoice Type', required=True)
    amount = fields.Float('Amount', required=True)
    amount_included = fields.Monetary(string='Amount Included',
                                      store=True, readonly=True, compute='_compute_amount', currency_field='company_currency_id')
    amount_subtotal = fields.Monetary(string='Amount',
                                      store=True, readonly=True, compute='_compute_amount', currency_field='company_currency_id')
    amount_subtotal_signed = fields.Monetary(string='Amount Signed', currency_field='company_currency_id',
                                             store=True, readonly=True, compute='_compute_amount',
                                             help="Total amount in the currency of the company, negative for credit notes.")
    company_currency_id = fields.Many2one('res.currency', related='rendition_id.company_currency_id', readonly=True,
                                          related_sudo=False)
    taxes_ids = fields.Many2many('account.tax','account_expenses_rendition_invoice_taxes_rel','rendition_invoice_id','tax_id', 'Taxes', domain = [('type_tax_use', '=', 'purchase')])
    account_id = fields.Many2one('account.account', 'Account', required=True, domain=[('deprecated', '=', False)])
    account_analytic_id = fields.Many2one('account.analytic.account','Analytic Account')
    date_invoice = fields.Date('Invoice Date', required=True)
    invoice_number = fields.Char('Invoice Number')
    #NIT; Razon and other will be added on other addon

    move_id = fields.Many2one('account.move', string='Move')
    company_id = fields.Many2one('res.company', 'Company', related='rendition_id.company_id')


    @api.multi
    def _generate_move(self):
        return True

    @api.multi
    def _generate_move_line(self):
        return True

    @api.multi
    def _get_analytic_line(self):
        ref = self.rendition_id.name
        return {
            'name': self.name or '',
            'date': self.date_invoice,
            'account_id': self.account_analytic_id.id,
            'amount': self.amount,
            'general_account_id': self.invoice_type.account_id.id,
            'ref': self.name or '',
        }


class AccountExpensesRenditionTax(models.Model):
    _name = "account.expenses.rendition.tax"
    _description = "Invoice Tax"
    _order = 'sequence'

    def _compute_base_amount(self):
        tax_grouped = {}
        for rendition in self.mapped('rendition_id'):
            tax_grouped[rendition.id] = rendition.get_taxes_values()
        for tax in self:
            tax.base = 0.0
            if tax.tax_id:
                key = tax.tax_id.get_grouping_key({
                    'tax_id': tax.tax_id.id,
                    'account_id': tax.account_id.id,
                    'account_analytic_id': tax.account_analytic_id.id,
                })
                if tax.rendition_id and key in tax_grouped[tax.rendition_id.id]:
                    tax.base = tax_grouped[tax.rendition_id.id][key]['base']
                else:
                    _logger.warning('Tax Base Amount not computable probably due to a change in an underlying tax (%s).', tax.tax_id.name)

    rendition_id = fields.Many2one('account.expenses.rendition', 'Rendition', copy=False)
    name = fields.Char(string='Tax Description', required=True, copy=False)
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict', copy=False)
    account_id = fields.Many2one('account.account', string='Tax Account', required=True, domain=[('deprecated', '=', False)], copy=False)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account', copy=False)
    amount = fields.Monetary(copy=False)
    manual = fields.Boolean(default=True, copy=False)
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tax.", copy=False)
    company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True, copy=False)
    currency_id = fields.Many2one('res.currency', related='rendition_id.currency_id', store=True, readonly=True, copy=False)
    base = fields.Monetary(string='Base', compute='_compute_base_amount')
