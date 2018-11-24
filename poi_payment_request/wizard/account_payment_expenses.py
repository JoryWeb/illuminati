import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountPaymentExpensesWiz(models.TransientModel):
    _name = "account.payment.expenses.wiz"
    _description = "Agregar Rendiciones  a las Solicitudes de Pago"

    rendition_id = fields.Many2one('account.expenses.rendition', 'Redicion de Gastos', domain=[('payment_request_id', '=', False)])

    @api.multi
    def action_add_items(self):
        # request_obj = self.env['account.payment.request']
        payment_request_id = self.env.context.get('active_id', False)
        if payment_request_id:
            # payment_request_id = request_obj.browse(payment_request_id)
            # payment_request_id.rendition_ids = [0,0,{}]
            self.rendition_id.payment_request_id = payment_request_id
        else:
            raise ValidationError('Error no se encontro la Solicitud de Pago. Contacte a Soporte.')
