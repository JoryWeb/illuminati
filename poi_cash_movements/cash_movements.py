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

from odoo.exceptions import Warning as UserError


class AccountCashMovementType(models.Model):
    _name = 'account.cash.movement.type'
    _description = 'Account Cash Movement Types'

    name = fields.Char('Name', required=True)
    account_id = fields.Many2one('account.account', 'Account', required=True, domain=[('reconcile','=',True)], help="Accounts must be reconciliable")
    payment_type = fields.Selection([('outbound', 'Outbound'),
                                     ('inbound', 'Inbound')], string="Payment Type", required=True)


class AccountCashMovement(models.Model):
    _name = 'account.cash.movement'
    _description = 'Account Cash Movements'
    _inherit = 'mail.thread'

    name = fields.Char('Name', copy='', default='') #To be filled on validate
    type = fields.Many2one('account.cash.movement.type', 'Type', readonly=True, states={'draft': [('readonly', False)]},)
    partner_id = fields.Many2one('res.partner','Contact', required=True,readonly=True, states={'draft': [('readonly', False)]},)
    #journal_id = fields.Many2one('account.journal','Journal', domain=[('type','in',['bank','cash'])])
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.user.company_id.id,readonly=True, states={'draft': [('readonly', False)]},)

    ref = fields.Char('Reference',readonly=True, states={'draft': [('readonly', False)]},)
    date = fields.Date('Date', default=fields.datetime.now(),readonly=True, states={'draft': [('readonly', False)]},)
    amount = fields.Monetary('Amount', required=True, currency_field='currency_id',readonly=True, states={'draft': [('readonly', False)]},)

    payment_type = fields.Selection([('outbound', 'Outbound'),
                                     ('inbound', 'Inbound')], string="Payment Type", related='type.payment_type', readonly=True)
    account_analytic_id = fields.Many2one('account.analytic.account', u"Cuenta analítica", required=False)

    @api.model
    def _get_amount_residual(self):
        real_amount = 0.0
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            real_amount = self.currency_id.compute(self.amount, self.company_id.currency_id)
        else:
            real_amount = self.amount

        p_sum = 0.0
        for p in self.payment_ids:
            real_payment = 0.0
            if p.journal_id.currency_id and p.journal_id.currency_id != self.company_id.currency_id:
                real_payment = p.journal_id.currency_id.compute(p.amount, self.company_id.currency_id)
            else:
                real_payment = p.amount

            p_sum += real_payment

        self.amount_residual = real_amount - p_sum

    amount_residual = fields.Monetary('Amount Residual', currency_field='currency_id', compute=_get_amount_residual)

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  default=_default_currency, track_visibility='always')

    state = fields.Selection([('draft','Draft'),
                              ('open','Partially Paid'),
                              ('paid','Paid')], string='State', default='draft', copy=False)

    move_id = fields.Many2one('account.move','Move Generated') #Not being filled because we have more than 1
    payment_ids = fields.One2many('account.payment','cash_movement_id','Payments')

    #line_ids = fields.One2many('account.cash.movement.line','movement_id',string='Lines')

    @api.multi
    def test_paid(self):
        for m in self:
            if m.name == '':
                seq = self.env['ir.sequence']
                code = seq.next_by_code('account.cash.movement') or '/'
                m.name = code

            real_amount = 0.0
            if m.currency_id and m.currency_id != m.company_id.currency_id:
                real_amount = m.currency_id.compute(self.amount, self.company_id.currency_id)
            else:
                real_amount = self.amount

            p_sum = 0.0
            for p in m.payment_ids:
                real_payment = 0.0
                if p.journal_id.currency_id and p.journal_id.currency_id != m.company_id.currency_id:
                    real_payment = p.journal_id.currency_id.compute(p.amount, self.company_id.currency_id)
                else:
                    real_payment = p.amount

                p_sum += real_payment

            if p_sum >= real_amount:
                m.state = 'paid'
            else:
                m.state = 'open'

        return True


    @api.multi
    def unlink(self):
        for order in self:
            if not order.state == 'draft':
                raise UserError(_('You can\'t delete a cash movement already validated.'))
        return super(AccountCashMovement, self).unlink()