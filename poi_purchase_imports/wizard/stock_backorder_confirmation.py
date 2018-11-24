# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, registry
from odoo.tools.translate import _
from psycopg2 import OperationalError
import logging
import threading

_logger = logging.getLogger(__name__)

class stock_backorder_confirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.multi
    def _button_picking_threading(self):
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            self._picking_confirm(
                use_new_cursor=new_cr.dbname,
                company_id=self.env.user.company_id.id)
            new_cr.close()
            return {}

    @api.model
    def _picking_confirm(self, use_new_cursor=False, company_id=False):
        if use_new_cursor:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        try:
            self.ensure_one()
            self._process()
            if use_new_cursor:
                cr.commit()
                user_id = self._uid
                usuario = self.env['res.users'].browse(user_id)
                body_html_send = "Picking " + str(self.name) + " Confirmado"
                new_msg = self.message_post(body=body_html_send)
                new_msg.sudo().write({'needaction_partner_ids': [(4, usuario.partner_id.id)]})
        except OperationalError:
            if use_new_cursor:
                cr.rollback()
            else:
                raise

        if use_new_cursor:
            cr.commit()
            cr.close()

        return {}

    @api.multi
    def picking_threading(self):
        threaded_calculation = threading.Thread(target=self._button_picking_threading, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def process(self):
        if len(self.pick_id.pack_operation_ids) > 100:
            self.picking_threading()
        else:
            self.ensure_one()
            self._process()