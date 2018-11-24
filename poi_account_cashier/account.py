##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cashier_id = fields.Many2one('res.users', string='Cajero', ondelete='restrict')
    payment_journal_id = fields.Many2one('account.journal', string=u'Método de pago', ondelete='restrict')


class AccountPayment(models.Model):
    _inherit = "account.payment"

    cashier_id = fields.Many2one('res.users', string='Cajero', ondelete='restrict', default=lambda self: self.env.user)

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):

        #Si el "Cajero" fue explicitamente especificado por un account manager, asentar con ese dato. Caso contrario usar el dato del usuario creador
        ml = {}
        ml = super(AccountPayment, self)._get_shared_move_line_vals(debit,credit,amount_currency,move_id,invoice_id)
        if self.cashier_id:
            ml['cashier_id'] = self.cashier_id.id
        else:
            ml['cashier_id'] = self.env.user.id

        if self.payment_type == 'transfer':
            if debit > 0:
                ml['payment_journal_id'] = self.destination_journal_id.id or False
            elif credit > 0:
                ml['payment_journal_id'] = self.journal_id.id or False

        return ml

    @api.multi
    def post(self):
        for payment in self:
            if payment.payment_type != 'transfer':
                payment.cashier_id = self.env.user

        return super(AccountPayment, self).post()