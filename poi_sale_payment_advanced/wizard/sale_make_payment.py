import logging
from odoo import api, fields, models, _


_logger = logging.getLogger(__name__)

class SaleMakePayment(models.TransientModel):
    _name = 'sale.make.payment'
    _description = 'Pagos Adelantados sin Factura'

    @api.model
    def _get_advanced_account(self):
        active_id = self.env.context.get('active_id', False)
        order_id = self.env['sale.order'].search([('id', '=', active_id)], limit=1).partner_id.property_prepaid_account_payable_id
        return order_id

    amount = fields.Float('Monto a Pagar', required=True)
    journal_id = fields.Many2one('account.journal', 'Metodo de Pago', required=True, domain=[('at_least_one_inbound', '=', True), ('type', 'in', ('cash', 'bank'))])
    payment_date = fields.Date('Fecha de Pago', default=fields.Date.today(), required=True)
    account_advanced_id = fields.Many2one('account.account', 'Cuenta de Adelanto', default=_get_advanced_account, domain=[('internal_type', '=', 'receivable'), ('deprecated', '=', False)])

    @api.multi
    def action_make_payment(self):
        order_obj = self.env['sale.order']
        payment_obj = self.env['account.payment']
        active_id = self.env.context.get('active_id', False)
        if active_id:
            order_id = order_obj.browse(active_id)
            payment_data = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': order_id.partner_id.id,
                'amount': self.amount,
                'journal_id': self.journal_id.id,
                'payment_date': self.payment_date,
                'communication': order_id.name,
                'payment_method_id': 1,
                'order_id': order_id.id,
            }
            order_id.payment_count = order_id.payment_count + 1
            payment_id = payment_obj.create(payment_data)
            payment_id.destination_account_id = self.account_advanced_id.id
            payment_id.post()
