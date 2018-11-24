#!/usr/bin/env python
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from openerp import models, fields, api

import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools.translate import _


class EventPicking(models.TransientModel):

    _name = 'sale.event.pick.wizard'
    _description = "Asistente de entrega"

    event_id = fields.Many2one('sale.event', string='Evento', readonly=True)
    product_lines = fields.One2many('sale.event.pick.wizard.line', 'wizard_id', string='Regalos a entregar')

    @api.model
    def default_get(self, fields):
        defs = {}
        active_id = self._context.get('active_id')
        if not active_id:
            raise UserError(_('No se encontró un Evento de contexto'))
        defs['event_id'] = active_id
        defs_lines = []
        event = self.env['sale.event'].browse(active_id)
        for line in event.product_lines:
            if line.state == 'sold':
                prod_line = {
                    'event_line_id': line.id,
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'checked': True,
                }
                defs_lines.append(prod_line)

        defs.update(product_lines=[(0,0, elem) for elem in defs_lines])
        return defs

    @api.multi
    def create_picking(self):

        if not self.event_id.warehouse_id.reserv_loc_id:
            raise UserError(_('El Almacén/Tienda del cual se esta vendiendo no tiene configurada ua Ubicación de reserva.'))
        reserv_loc_id = self.event_id.warehouse_id.reserv_loc_id.id
        out_loc_id = self.env.ref('stock.stock_location_customers').id

        picking_dlv = self.env['stock.picking'].create({
            'partner_id': self.event_id.partner_id.id,
            'picking_type_id': self.event_id.warehouse_id.out_type_id.id,
            'location_id': reserv_loc_id,
            'location_dest_id': out_loc_id,
        })

        event_lines = []
        for line in self.product_lines:
            if line.checked:
                self.env['stock.move'].create({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking_dlv.id,
                    'location_id': reserv_loc_id,
                    'location_dest_id': out_loc_id,
                })
                event_lines.append(line.event_line_id.id)

        picking_dlv.action_assign()

        new_state = 'delivered'
        ev_line = self.env['sale.event.line'].browse(event_lines)
        ev_line.write({'state': new_state, 'picking_id': picking_dlv.id})
        return ev_line[0].action_view_doc(case='picking')    #{'type': 'ir.actions.act_window_close'}

class EventPickingLine(models.TransientModel):

    _name = 'sale.event.pick.wizard.line'
    _description = "Productos a entregar"

    wizard_id = fields.Many2one('sale.event.pick.wizard', string='Evento a facturar')
    event_line_id = fields.Many2one('sale.event.line', string='Línea de Producto')
    product_id = fields.Many2one('product.product', 'Producto', readonly='1')
    quantity = fields.Float('Cantidad', digits=dp.get_precision('Product Unit of Measure'), required=True, readonly=True)
    checked = fields.Boolean('Checked')

    @api.multi
    def check_line(self):
        self.write({'checked': True})

    @api.multi
    def uncheck_line(self):
        self.write({'checked': False})