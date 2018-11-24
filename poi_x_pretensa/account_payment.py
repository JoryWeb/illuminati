##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Coded by: Grover Menacho
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

from openerp.osv import osv, fields
from openerp import models, api, _


class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        'code': fields.char('Code', size=10, required=True, help="The code will be displayed on reports."),
        'efectivo_cheque': fields.boolean('Efectivo/Cheque'),
    }


class account_payment(osv.osv):
    _inherit = 'account.payment'

    _columns = {
        'efectivo': fields.boolean('Efectivo'),
        'cheque': fields.boolean('Cheque'),
        'txt_validate': fields.char('Validate', size=10),
        'reference': fields.char('Ref. Pago'),
        'project_id': fields.many2one('account.analytic.account', u'Cuenta Analítica'),
        'user_id': fields.many2one('res.users', 'Vendedor'),
        'note': fields.text('Notas'),
    }

    _defaults = {
        'txt_validate': '0',
    }

    # Rescatar la cuenta analitica del pedido de ventas para asignar al pago desde factura
    @api.model
    def default_get(self, fields):
        rec = super(account_payment, self).default_get(fields)
        if rec.get('invoice_ids'):
            invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
            query = """ SELECT t1.order_id, t2.invoice_id
                               from sale_order_line_invoice_rel t0
                               inner join sale_order_line t1 on t1.id = t0.order_line_id
                               inner join account_invoice_line t2 on t2.id = t0.invoice_line_id
                               where t2.invoice_id = %s
                               group by t1.order_id, t2.invoice_id
                                """
            invoice = invoice_defaults[0]
            inv_id = invoice['id']
            self._cr.execute(query, (inv_id,))
            ord_id = 0
            for order_id, invoice_id in self._cr.fetchall():
                ord_id = order_id

            orders = self.env['sale.order'].browse(ord_id)
            if invoice_defaults and len(invoice_defaults) == 1:
                rec['analityc_account_id'] = orders.project_id.id
        return rec

    @api.onchange('journal_id')
    def _onchange_journal_pret(self):
        if self.journal_id.efectivo_cheque == True:
            self.txt_validate = '1'
        else:
            self.txt_validate = '0'


    def onchange_check(self, cr, uid, ids, journal_id, cheque, efectivo, txt_validate, context=None):
        res = {}
        if cheque == True and efectivo == True:
            res.update({'efectivo': False})
        if not journal_id:
            return False
        journal_pool = self.pool.get('account.journal')
        if cheque == True and txt_validate == "1":
            res.update({'payment_model': 'bank_transfer'})
        else:
            res.update({'payment_model': None, 'bank_payment_type': None})

        return {'value': res}

    def onchange_check_efectivo(self, cr, uid, ids, cheque, efectivo, context=None):
        res = {}
        if cheque == True and efectivo == True:
            res.update({'cheque': False})
        return {'value': res}

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):
        """ Returns values common to both move lines (except for debit, credit and amount_currency which are reversed)
        """
        return {
            'partner_id': self.payment_type in ('inbound', 'outbound') and self.env[
                'res.partner']._find_accounting_partner(self.partner_id).id or False,
            'invoice_id': invoice_id and invoice_id.id or False,
            'move_id': move_id,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency or False,
            'analytic_account_id': self.analytic_account_id.id,
        }
