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

from odoo import models, fields, api, exceptions, _
from odoo.tools.translate import _
from datetime import datetime, timedelta

class PurchaseDeliveryProductWizard(models.TransientModel):
    _name = 'purchase.delivery.product.wizard'
    _description = 'Delivery Wizard'

    purchase_id = fields.Many2one('purchase.order', 'Orden de compra')
    base_date = fields.Date('Fecha Primera Entrega', required=True)
    item_ids = fields.One2many('purchase.delivery.product.wizard.items', 'delivery_id', 'Productos Planificados')
    item_planned_ids = fields.One2many('purchase.delivery.product.wizard.planned', 'delivery_id', 'Productos Base')

    @api.model
    def default_get(self, fields):
        res = super(PurchaseDeliveryProductWizard, self).default_get(fields)
        purchase_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')

        if not purchase_ids or len(purchase_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('purchase.order'), 'Bad context propagation'
        purchase_id, = purchase_ids
        purchase = self.env['purchase.order'].browse(purchase_id)
        items = []
        items2 = []
        if not purchase.order_line:
            raise exceptions.Warning(
            _('Error! \n Debe Ingresar productos a la compra y Guardar'))
        for po in purchase.order_line:
            po.product_id.type
            if po.product_id.type in ('product', 'consu'):
                item2 = {
                    'purchase_id': po.order_id.id,
                    'purchase_line_id': po.id,
                    'product_id': po.product_id.id,
                    'product_qty': po.product_qty,
                    'delivery_date': po.date_planned,
                }
                if po.product_id:
                    items2.append(item2)

        res['item_planned_ids'] = [(0, 0, x) for x in items2]
        res['base_date']=purchase.date_order
        return res

    @api.multi
    def wizard_view(self):
        view = self.env.ref('poi_purchase_delivery_product.view_purchase_delivery_product_wizard')

        return {
            'name': _('Enter transfer details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.delivery.product.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context,
        }

    @api.multi
    def do_split_delivery(self):
        #Limpiar los registros de planificación
        for item in self.item_ids:
            item.unlink()

        for planned in self.item_planned_ids:
            #cantidad 100
            product_qty = planned.product_qty
            product_res = product_qty
            #Dias division 7
            day_division = planned.day_division
            #cantidad division
            qty_division = planned.qty_division

            suma_base = 0
            base_date = datetime.strptime(self.base_date, "%Y-%m-%d")
            for x_cantidad in range(qty_division, int(product_qty) + 1, int(qty_division)):
                plan_vals = {
                    'delivery_id': planned.delivery_id.id,
                    'product_id': planned.product_id.id,
                    'product_qty': qty_division,
                    'delivery_date': base_date,
                    'purchase_line_id': planned.purchase_line_id.id
                }
                suma_base = suma_base + qty_division
                base_date = base_date + timedelta(days=day_division)
                self.env['purchase.delivery.product.wizard.items'].create(plan_vals)

            if product_qty > suma_base:
                base_date = base_date + timedelta(days=day_division)
                plan_vals = {
                    'delivery_id': planned.delivery_id.id,
                    'product_id': planned.product_id.id,
                    'product_qty': product_qty - suma_base,
                    'delivery_date': base_date,
                    'purchase_line_id': planned.purchase_line_id.id
                }
                self.env['purchase.delivery.product.wizard.items'].create(plan_vals)
        if self and self[0]:
            return self[0].wizard_view()

    @api.one
    def do_detailed_delivery(self):
        purchase_ids = self._context['active_ids']
        purchase_id, = purchase_ids

        for product in self.item_ids:
            delivery_data = {
                'product_id': product.product_id.id,
                'product_qty': product.product_qty,
                'delivery_date': product.delivery_date,
                'purchase_id': purchase_id,
                'purchase_line_id': product.purchase_line_id.id,
            }
            self.env['purchase.delivery.product'].create(delivery_data)
        return True

class PurchaseDeliveryProductWizardPlanned(models.TransientModel):
    _name = 'purchase.delivery.product.wizard.planned'
    _description = 'Items para plan de entrega Base'

    delivery_id = fields.Many2one('purchase.delivery.product.wizard', 'Plan de Entregas')
    purchase_line_id = fields.Many2one('purchase.order.line', 'Linea de Compra')
    product_id = fields.Many2one('product.product', 'Producto')
    delivery_date = fields.Date('Fecha')
    product_qty = fields.Float('Cantidad')
    day_division = fields.Integer('Dias Intervalo', default=7)
    qty_division = fields.Integer('Cantidad Invervalo', default=1)

class PurchaseDeliveryProductWizardItems(models.TransientModel):
    _name = 'purchase.delivery.product.wizard.items'
    _description = 'Items para plan de entrega'

    delivery_id = fields.Many2one('purchase.delivery.product.wizard', 'Plan de Entregas')
    product_id = fields.Many2one('product.product', 'Producto')
    purchase_line_id = fields.Many2one('purchase.order.line', 'Linea de Compra')
    delivery_date = fields.Date('Fecha Ingreso Planificado')
    product_qty = fields.Float('Cantidad')


