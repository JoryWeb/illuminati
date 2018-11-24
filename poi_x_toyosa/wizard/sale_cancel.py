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

class SaleType(models.Model):
    _name = 'sale.order.cancel'
    _description = 'Motivos de cancelacion de Ordenes de Venta'

    name = fields.Char('Motivo')


class SaleType(models.TransientModel):
    _name = 'sale.order.cancel.wiz'
    _description = 'Motivos de cancelacion de Ordenes de Venta'

    reason_id = fields.Many2one('sale.order.cancel', 'Motivo de Cancelacion', required=True)

    @api.multi
    def action_cancel(self):
        sale_id = self.env.context.get('active_id', False)
        sale_obj = self.env['sale.order']
        if sale_id:
            sale_id = sale_obj.browse(sale_id)
            if sale_id.lot_id and sale_id.lot_id.id:
                for sale_line in sale_id.order_line:
                    if sale_line.id == sale_id.lot_id.sale_line_id.id:
                        sale_id.lot_id.release()
                        sale_id.lot_id.reset_contract_ref()
            sale_id.message_post(body=self.reason_id.name)
            sale_id.with_context(signal=True).action_cancel()

    @api.multi
    def action_cancel_reasing(self):
        sale_id = self.env.context.get('active_id', False)
        sale_obj = self.env['sale.order']
        if sale_id:
            sale_id = sale_obj.browse(sale_id)
            if sale_id.lot_id and sale_id.lot_id.id:
                for sale_line in sale_id.order_line:
                    if sale_line.id == sale_id.lot_id.sale_line_id.id:
                        sale_id.lot_id.release()
            new_id = sale_id.copy()
            # for pays in sale_id.payment_advanced_ids:
            #     pays.order_id = new_id.id
            new_id.discount_flag = False
            new_id.plate_flag = False
            new_id.confirm_sale = False
            # new_id.order_id = sale_id
            # new_id.contract_ref = sale_id.contract_ref
            # if sale_id.lot_id:
            #     sale_id.lot_id.reset_contract_ref()
            sale_id.message_post(body=self.reason_id.name)
            sale_id.with_context(signal=True).action_cancel()

            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('sale.action_orders')
            list_view_id = imd.xmlid_to_res_id('sale.view_order_tree')
            form_view_id = imd.xmlid_to_res_id('sale.view_order_form')

            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
                'target': action.target,
                'context': action.context,
                'res_model': action.res_model,
            }
            if len(new_id) > 1:
                result['domain'] = "[('id','in',%s)]" % new_id.ids
            elif len(new_id) == 1:
                result['views'] = [(form_view_id, 'form')]
                result['res_id'] = new_id.ids[0]
            else:
                result = {'type': 'ir.actions.act_window_close'}
            return result

    @api.multi
    def action_cancel_adenda(self):
        sale_id = self.env.context.get('active_id', False)
        sale_obj = self.env['sale.order']
        if sale_id:
            sale_id = sale_obj.browse(sale_id)
            if sale_id.lot_id and sale_id.lot_id.id:
                for sale_line in sale_id.order_line:
                    if sale_line.id == sale_id.lot_id.sale_line_id.id:
                        sale_id.lot_id.release()
            new_id = sale_id.copy()
            for pays in sale_id.payment_advanced_ids:
                pays.order_id = new_id.id
            new_id.discount_flag = False
            new_id.plate_flag = False
            new_id.confirm_sale = False
            new_id.order_id = sale_id
            new_id.contract_ref = sale_id.contract_ref
            if sale_id.lot_id:
                sale_id.lot_id.reset_contract_ref()
            sale_id.message_post(body=self.reason_id.name)
            sale_id.with_context(signal=True).action_cancel()

            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('sale.action_orders')
            list_view_id = imd.xmlid_to_res_id('sale.view_order_tree')
            form_view_id = imd.xmlid_to_res_id('sale.view_order_form')

            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
                'target': action.target,
                'context': action.context,
                'res_model': action.res_model,
            }
            if len(new_id) > 1:
                result['domain'] = "[('id','in',%s)]" % new_id.ids
            elif len(new_id) == 1:
                result['views'] = [(form_view_id, 'form')]
                result['res_id'] = new_id.ids[0]
            else:
                result = {'type': 'ir.actions.act_window_close'}
            return result
