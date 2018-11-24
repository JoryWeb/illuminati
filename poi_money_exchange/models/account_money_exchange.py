#########################################################################
#                                                                       #
# Copyright (C) 2015  Agile Business Group                              #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU Affero General Public License as        #
# published by the Free Software Foundation, either version 3 of the    #
# License, or (at your option) any later version.                       #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU Affero General Public Licensefor more details.                    #
#                                                                       #
# You should have received a copy of the                                #
# GNU Affero General Public License                                     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#                                                                       #
#########################################################################
import logging
from odoo import fields, models, api, _
from odoo.exceptions import Warning, ValidationError

_logger = logging.getLogger(__name__)

class AccountMoneyExchange(models.Model):
    _name = 'account.money.exchange'
    _inherit = ['mail.thread']
    _description = 'Cambio de Moneda'
    _rec_name = 'date'

    ref = fields.Char('Referencia', readonly=True, states={'draft':[('readonly',False)]})
    journal_id = fields.Many2one("account.journal", 'Diario', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    date = fields.Date('Fecha', default=fields.Date.today(), readonly=True, states={'draft':[('readonly',False)]}, required=True)
    cashier_id = fields.Many2one('res.users', 'Cajero', default=lambda self: self.env.user, readonly=True, states={'draft':[('readonly',False)]}, required=True)
    analytic_id = fields.Many2one("account.analytic.account" ,"Cuenta Analitica", readonly=True, states={'draft':[('readonly',False)]}, required=True)
    account_destiny_id = fields.Many2one('account.account', 'Cuenta Destino', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    account_origin_id = fields.Many2one('account.account', 'Cuenta Origen', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    account_tc_id = fields.Many2one('account.account', 'Cuenta Dif. Tasa de Cambio', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    amount_destiny = fields.Float('Monto Destino', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    tc_origin = fields.Many2one('res.currency', 'Moneda de Origen', readonly=True)
    tc = fields.Many2one('res.currency', 'Tasa de Cambio', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    amount_origin = fields.Float('Monto Origen', compute="_compute_amount_origin")
    state = fields.Selection([
    	('draft', 'Borrador'),
    	('done', 'Validado'),], string="Estado", default="draft")

    amount_diff = fields.Float('Diferencia', compute="_compute_amount_diff")
    move_id = fields.Many2one('account.move', 'Asiento Contable')


    @api.multi
    @api.depends('amount_origin')
    def _compute_amount_diff(self):
        for s in self:
            s.amount_diff = self.env.user.company_id.currency_id_sec.compute(s.amount_destiny, self.env.user.company_id.currency_id) - s.amount_origin

    @api.multi
    def _compute_amount_origin(self):
        for s in self:
            s.amount_origin = s.tc.compute(s.amount_destiny, self.env.user.company_id.currency_id)

    @api.multi
    def exchange_done(self):
        for rec in self:
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            base_currency_id_sec = self.env.user.company_id.currency_id_sec
            base_currency_id = self.env.user.company_id.currency_id
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=rec.date).compute_amount_fields(rec.amount_destiny, self.env.user.company_id.currency_id_sec, self.env.user.company_id.currency_id)

            debit2, credit2, amount_currency2, currency_id2 = aml_obj.with_context(date=rec.date).compute_amount_fields(rec.amount_origin, base_currency_id, self.env.user.company_id.currency_id)

            debit3, credit3, amount_currency3, currency_id3 = aml_obj.with_context(date=rec.date).compute_amount_fields(rec.amount_diff, base_currency_id, self.env.user.company_id.currency_id)

            name = rec.journal_id.with_context(ir_sequence_date=rec.date).sequence_id.next_by_id()
            move = self.env['account.move'].create({
                'name': name,
                'date': rec.date,
                'ref': rec.ref or '',
                'company_id': self.env.user.company_id.id,
                'journal_id': rec.journal_id.id,
            })


            writeoff_line0 = self._get_shared_move_line_vals(0, 0, 0, move.id, rec.cashier_id)
            writeoff_line0['name'] = _('Monto Destino')
            writeoff_line0['account_id'] = rec.account_destiny_id.id
            writeoff_line0['debit'] = debit
            writeoff_line0['credit'] = credit
            writeoff_line0['amount_currency'] = amount_currency
            writeoff_line0['currency_id'] = currency_id
            writeoff_line0['analytic_account_id'] = rec.analytic_id.id
            writeoff_line0 = aml_obj.create(writeoff_line0)

            writeoff_line1 = self._get_shared_move_line_vals(0, 0, 0, move.id, rec.cashier_id)
            writeoff_line1['name'] = _('Monto Origen')
            writeoff_line1['account_id'] = rec.account_origin_id.id
            writeoff_line1['debit'] = credit2
            writeoff_line1['credit'] = debit2
            writeoff_line1['amount_currency'] = amount_currency2
            writeoff_line1['currency_id'] = currency_id2
            writeoff_line0['analytic_account_id'] = rec.analytic_id.id
            writeoff_line1 = aml_obj.create(writeoff_line1)

            writeoff_line2 = self._get_shared_move_line_vals(0, 0, 0, move.id, rec.cashier_id)
            writeoff_line2['name'] = _('Diff. Tasa de Cambio')
            writeoff_line2['account_id'] = rec.account_tc_id.id
            writeoff_line2['debit'] = credit3
            writeoff_line2['credit'] =  debit3
            writeoff_line2['amount_currency'] = amount_currency3
            writeoff_line2['currency_id'] = currency_id3
            writeoff_line0['analytic_account_id'] = rec.analytic_id.id
            writeoff_line2 = aml_obj.create(writeoff_line2)

            move.post()
            rec.move_id = move.id
            rec.state = 'done'

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, cashier_id=False):
        """ Returns values common to both move lines (except for debit, credit and amount_currency which are reversed)
        """
        return {
            'cashier_id': cashier_id and cashier_id.id or False,
            'move_id': move_id,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency or False,
        }

    @api.multi
    def button_view_move(self):
        if not self.move_id:
            raise Warning('No se Tiene Identificado el asiento Resultante')
        return {
            'name': _('Asiento Contable'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', self.move_id.id)],
        }
