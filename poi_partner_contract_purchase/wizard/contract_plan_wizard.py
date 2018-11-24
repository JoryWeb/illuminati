##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.odoo.com>
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

from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import datetime, timedelta

class ContractPlanWizard(models.TransientModel):
    _name = 'contract.plan.wizard'
    _description = 'Wizard Plan de Pagos'

    contract_id = fields.Many2one('partner.contract.invoice', 'Contrato de Compra')
    base_date = fields.Date('Fecha primer pago', required=True)
    plan_pagos = fields.Boolean('Plan de Pagos')
    item_planned_ids = fields.One2many('contract.plan.wizard.planned', 'plan_id', 'Pagos Base')
    item_ids = fields.One2many('contract.plan.wizard.items', 'plan_id', 'Pagos Planificados')

    @api.model
    def default_get(self, fields):
        res = super(ContractPlanWizard, self).default_get(fields)
        contract_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')

        if not contract_ids or len(contract_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('partner.contract.invoice'), 'Bad context propagation'
        contract_id, = contract_ids
        contract = self.env['partner.contract.invoice'].browse(contract_id)
        items = []
        items2 = []
        for co in contract.contract_invoice_id:
            item = {
                'contract_id': co.contract_id.id,
                'contract_line_id': co.id,
                'product_id': co.product_id.id,
                'product_qty': 1.0,
                'amount': co.amount_inv,
                'delivery_date': co.date,
                'order_line_id': co.order_line_id.id,
            }
            if co.product_id:
                items.append(item)

            item2 = {
                'contract_id': co.contract_id.id,
                'contract_line_id': co.id,
                'product_id': co.product_id.id,
                'product_qty': 1.0,
                'amount': co.amount_inv,
                'delivery_date': co.date,
                'order_line_id': co.order_line_id.id,
            }
            if co.product_id:
                items2.append(item2)

        res['item_planned_ids'] = [(0, 0, x) for x in items2]
        res['base_date'] = contract.date_start
        if contract.plan_pagos == 'plan_pagos':
            res['plan_pagos'] = False
        else:
            res['plan_pagos'] = True
        return res

    @api.multi
    def wizard_view(self):
        view = self.env.ref('poi_partner_contract_purchase.view_contract_plan_wizard')

        return {
            'name': _('Detalles del plan'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'contract.plan.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context,
        }

    @api.multi
    def do_split_plan(self):
        #Limpiar los registros de planificación
        for item in self.item_ids:
            item.unlink()

        for planned in self.item_planned_ids:
            amount = planned.amount
            #Dias division 7
            day_division = planned.day_division
            #cantidad division
            amount_division = planned.amount_division

            suma_base = 0
            base_date = datetime.strptime(self.base_date, "%Y-%m-%d")
            for x_monto in range(amount_division, int(amount) + 1, int(amount_division)):
                plan_vals = {
                    'plan_id': planned.plan_id.id,
                    'product_id': planned.product_id.id,
                    'amount': amount_division,
                    'product_qty': 1.0,
                    'delivery_date': base_date,
                    'contract_line_id': planned.contract_line_id.id,
                    'order_line_id': planned.order_line_id.id,
                }
                suma_base = suma_base + amount_division
                base_date = base_date + timedelta(days=day_division)
                self.env['contract.plan.wizard.items'].create(plan_vals)

            if amount > suma_base:
                base_date = base_date + timedelta(days=day_division)
                plan_vals = {
                    'plan_id': planned.plan_id.id,
                    'product_id': planned.product_id.id,
                    'amount': amount - suma_base,
                    'product_qty': 1.0,
                    'delivery_date': base_date,
                    'contract_line_id': planned.contract_line_id.id,
                    'order_line_id': planned.order_line_id.id,
                }
                self.env['contract.plan.wizard.items'].create(plan_vals)

        if self and self[0]:
            return self[0].wizard_view()

    @api.multi
    def do_detailed_delivery(self):
        contract_ids = self._context['active_ids']
        active_model = self._context['active_model']
        if not contract_ids or len(contract_ids) != 1:
            return True
        assert active_model in ('partner.contract.invoice'), 'Bad context propagation'
        contract_id, = contract_ids
        contract = self.env['partner.contract.invoice'].browse(contract_id)
        contract.contract_invoice_id.unlink()
        for service in self.item_ids:
            plan_data = {
                'product_id': service.product_id.id,
                'product_qty': service.product_qty,
                'amount_inv': service.amount,
                'date': service.delivery_date,
                'contract_id': contract.id,
                'order_line_id': service.order_line_id.id,
            }
            self.env['partner.contract.invoice.line'].create(plan_data)
        return True

class PurchaseDeliveryProductWizardPlanned(models.TransientModel):
    _name = 'contract.plan.wizard.planned'
    _description = 'Items para plan pagos'

    plan_id = fields.Many2one('contract.plan.wizard', 'Plan de Pagos')
    contract_line_id = fields.Many2one('partner.contract.invoice.line', 'Linea de Compra')
    order_line_id = fields.Many2one('purchase.order.line', 'Linea de Compra')
    product_id = fields.Many2one('product.product', 'Producto')
    delivery_date = fields.Date('Fecha')
    product_qty = fields.Float('Cantidad')
    amount = fields.Float('Monto')
    day_division = fields.Integer('Dias Intervalo', default=7)
    amount_division = fields.Integer('Monto Intervalo', default=1)

class PurchaseDeliveryProductWizardItems(models.TransientModel):
    _name = 'contract.plan.wizard.items'
    _description = 'Items para plan de entrega'

    plan_id = fields.Many2one('contract.plan.wizard', 'Plan de pagos')
    product_id = fields.Many2one('product.product', 'Servicio')
    contract_line_id = fields.Many2one('partner.contract.invoice.line', 'Linea de Compra')
    delivery_date = fields.Date('Fecha Ingreso Planificado')
    product_qty = fields.Float('Cantidad')
    amount = fields.Float('Monto')
    order_line_id = fields.Many2one('purchase.order.line', 'Linea de Compra')


