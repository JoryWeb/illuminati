##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
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

from openerp import api, fields, models, _
from openerp.tools import float_is_zero, float_compare
import json

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('partner_id')
    def _get_default_shop(self):
        self.shop_id = self.env.user.shop_assigned.id

    shop_id = fields.Many2one("stock.warehouse", string=u'Tienda Almacén')

    #Asignar a todas las lineas del asiento contable la cuenta analitica de la tienda del usuario que
    #confirma la factura
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super(account_invoice,self).finalize_invoice_move_lines(move_lines)
        if self.shop_id and self.shop_id.analytic_account_id:
            analytic_id = self.shop_id.analytic_account_id.id
            for line_arr in move_lines:
                line = line_arr[2]
                line['analytic_account_id'] = analytic_id

        return move_lines

    @api.one
    def _get_outstanding_info_JSON(self):
        self.outstanding_credits_debits_widget = json.dumps(False)
        if self.state == 'open':
            domain = [('account_id', '=', self.account_id.id),
                      ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                      ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
            if self.type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')
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
                    analytic_txt = ''
                    if line.analytic_account_id:
                        analytic_txt = line.analytic_account_id.name
                    info['content'].append({
                        'journal_name': (line.ref or line.move_id.name) + ' ' + analytic_txt + ' ',
                        'amount': amount_to_show,
                        'currency': currency_id.symbol,
                        'id': line.id,
                        'position': currency_id.position,
                        'digits': [69, self.currency_id.decimal_places],
                    })
                info['title'] = type_payment
                self.outstanding_credits_debits_widget = json.dumps(info)
                self.has_outstanding = True
