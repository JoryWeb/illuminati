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
    _inherit = "purchase.order.line"

    delivery_id = fields.One2many('purchase.delivery.product', 'purchase_id', 'Plan de Entregas')

    @api.multi
    def _create_stock_moves(self, picking):
        stock_move = self.env['stock.move']
        stock_picking = self.env['stock.picking']
        todo_moves = []
        new_group = self.pool.get("procurement.group").create({'name': self.order_id.name, 'partner_id': self.order_id.partner_id.id}, context=context)
        if self.order_id.delivery_id:
            cr.execute("""select delivery_date from purchase_delivery_product
                            where purchase_id = """ + str(self.order_id.id) + """
                            group by delivery_date""")
            for delivery_date in self._cr.fetchall():
                # get localized dates
                date_from = datetime.strptime(delivery_date[0], "%Y-%m-%d") + timedelta(hours=4)

                del_date = delivery_date[0]
                # Crear los picking y duplicar para un nuevo movimiento asignado a los productos
                picking_id = stock_picking.copy(picking_id, default={'move_lines': [], 'date': date_from})
                for delivery in self.order_id.delivery_id:
                    if del_date == delivery.delivery_date:
                        if delivery.product_id.type in ('product', 'consu'):
                            for vals in self._prepare_order_line_move(delivery.purchase_line_id, picking_id, new_group):
                                vals['product_uom_qty'] = delivery.product_qty
                                vals['product_uos_qty'] = delivery.product_qty
                                move = stock_move.create(vals)
                                todo_moves.append(move)

            todo_moves = stock_move.action_confirm(todo_moves)
            stock_move.force_assign(todo_moves)

        else:
            moves = self.env['stock.move']
            done = self.env['stock.move'].browse()
            for line in self:
                for val in line._prepare_stock_moves(picking):
                    done += moves.create(val)
            return done