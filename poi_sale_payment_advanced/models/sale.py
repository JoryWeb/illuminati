import logging
import json
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payments_widget = fields.Text(compute='_get_payment_info_JSON')
    payment_count = fields.Integer('Numero de Pagos registrados', default=0)
    payment_advanced_ids = fields.Many2many('account.payment', compute="_compute_payment_advanced", string='Pagos Adelantados', copy=False)

    @api.multi
    @api.depends('payment_count')
    def _compute_payment_advanced(self):
        payment_obj = self.env['account.payment']
        for s in self:
            payment_ids = payment_obj.search([('order_id', '=', s.id), ('state', '=', 'posted')])
            s.payment_advanced_ids = payment_ids

    @api.multi
    @api.depends('payment_count')
    def _get_payment_info_JSON(self):
        payment_obj = self.env['account.payment']
        for s in self:
            s.payments_widget = json.dumps(False)
            payment_ids = payment_obj.search([('order_id', '=', s.id), ('state', '=', 'posted')])
            if payment_ids:
                info = {'title': _('Pagos Adelantados'), 'outstanding': False, 'content': []}
                for p in payment_ids:
                    move_id = False
                    for moves in p.move_line_ids:
                        move_id = moves.move_id.id
                        break
                    info['content'].append({
                        'name': p.name,
                        'journal_name': p.journal_id.name,
                        'amount': p.amount,
                        'currency': p.currency_id.symbol,
                        'digits': [69, p.currency_id.decimal_places],
                        'position': p.currency_id.position,
                        'date': p.payment_date,
                        'payment_id': p.id,
                        'move_id': move_id,
                        'ref': p.communication,
                    })
                s.payments_widget = json.dumps(info)
