# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, registry
from odoo.tools.translate import _
from psycopg2 import OperationalError
import logging
import threading
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class stock_immediate_confirmation(models.TransientModel):
    _inherit = 'stock.immediate.transfer'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
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
            # If still in draft => confirm and assign
            if self.pick_id.state == 'draft':
                self.pick_id.action_confirm()
                if self.pick_id.state != 'assigned':
                    self.pick_id.action_assign()
                    if self.pick_id.state != 'assigned':
                        raise UserError(_(
                            "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for pack in self.pick_id.pack_operation_ids:
                if pack.product_qty > 0:
                    pack.write({'qty_done': pack.product_qty})
                else:
                    pack.unlink()
            self.pick_id.do_transfer()

            if use_new_cursor:
                cr.commit()
                user_id = self._uid
                usuario = self.env['res.users'].browse(user_id)
                body_html_send = "Picking " + str(self.pick_id.name) + " Confirmado"
                new_msg = self.env['mail.thread'].message_post(body=body_html_send)
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
        if len(self.pick_id.pack_operation_ids) >= 100:
            self.picking_threading()
        else:
            self.ensure_one()
            # If still in draft => confirm and assign
            if self.pick_id.state == 'draft':
                self.pick_id.action_confirm()
                if self.pick_id.state != 'assigned':
                    self.pick_id.action_assign()
                    if self.pick_id.state != 'assigned':
                        raise UserError(_(
                            "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for pack in self.pick_id.pack_operation_ids:
                if pack.product_qty > 0:
                    pack.write({'qty_done': pack.product_qty})
                else:
                    pack.unlink()
            self.pick_id.do_transfer()