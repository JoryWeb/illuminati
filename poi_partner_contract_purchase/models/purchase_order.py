##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2011 Poiesis Consulting (<http://www.poiesisconsulting.com>). All Rights Reserved.
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from odoo import models, fields, api
from datetime import datetime, timedelta


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = 'Orden de compra'

    @api.one
    def _contract_count(self):
        valor = 0
        for contrac in self.contract_id:
            valor = valor + 1
        self.contract_count = valor

    contract_id = fields.Many2one('partner.contract.invoice', 'Contracto de Compra', required=False)
    contract_count = fields.Integer(string='N° Contratos', readonly=True, compute='_contract_count')

    @api.multi
    def view_contract(self):
        mod_obj = self.env['ir.model.data']
        model, action_id = tuple(
            mod_obj.get_object_reference(
                'poi_partner_contract_purchase',
                'action_partner_contract_invoice'))
        action = self.env[model].browse(action_id).read()[0]

        co_ids = []
        for co in self.contract_id:
            co_ids += [contract.id for contract in co]

        action['context'] = {}
        if len(co_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, co_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference('poi_partner_contract_purchase', 'view_partner_contract_invoice_form')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = co_ids and co_ids[0] or False
        return action

    @api.multi
    def verificar_facturas(self):
        return False

    @api.multi
    def _create_contract_line(self, contract_id=False):
        for order_line in self.order_line:
            if order_line.state == 'cancel':
                continue
            if not order_line.product_id:
                continue

            if order_line.product_id.type in ('service') and order_line.product_id.purchase_method == 'contract':
                vals = {
                    'date': order_line.date_planned,
                    'product_id': order_line.product_id.id,
                    'amount_inv': order_line.price_unit * order_line.product_qty,
                    'amount_paid': 0.0,
                    'amount_rest': 0.0,
                    'invoice_id': False,
                    'contract_id': contract_id.id,
                    'order_line_id': order_line.id,
                }
                self.env['partner.contract.invoice.line'].create(vals)

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for purchase_line in self.order_line:
            if purchase_line.product_id.purchase_method == 'contract':
                self.action_contract_create()
        return res

    @api.multi
    def action_contract_create(self):

        contract_vals = {
            'name': "Contrato asignado a " + self.name,
            'user_id': self._uid,
            'partner_id': self.partner_id.id,
            'date_start': self.date_order,
            'date_end': self.date_order,
            'order_id': self.id
        }
        contract_id = self.env['partner.contract.invoice'].create(contract_vals)
        self.contract_id = contract_id.id
        self._create_contract_line(contract_id)
        return contract_id


