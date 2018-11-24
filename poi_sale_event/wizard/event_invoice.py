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


class EventInvoice(models.TransientModel):

    _name = 'sale.event.invoice.wizard'
    _description = "Asistente de facturación"

    event_id = fields.Many2one('sale.event', string='Evento', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', required=True)
    takeaway = fields.Boolean('Se lo lleva', help="Determina si el cliente se llevará consigo los Regalos facturados. Si aplica, se generá una Salida del almacén de reserva.")
    product_lines = fields.One2many('sale.event.invoice.wizard.line', 'wizard_id', string='Regalos a facturar')

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
            if line.state == 'free':
                prod_line = {
                    'event_line_id': line.id,
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'subtotal': line.subtotal,
                    'checked': False,
                }
                defs_lines.append(prod_line)

        defs.update(product_lines=[(0,0, elem) for elem in defs_lines])
        return defs

    @api.multi
    def create_invoice(self):

        invoice = self.env['account.invoice'].create({'partner_id': self.partner_id.id,
                                                      'account_id': self.partner_id.property_account_receivable_id.id,
                                                      'type': 'out_invoice',
                                                      })

        event_lines = []
        invoice_line_ref = self.env['account.invoice.line']
        for line in self.product_lines:
            if line.checked:
                vals_line = {
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'invoice_id': invoice.id,
                }

                inv_line = invoice_line_ref.new(vals_line)
                inv_line._onchange_product_id()
                vals_line = inv_line._convert_to_write(inv_line._cache)

                if not vals_line.get('account_id', None):
                    pass
                inv_line_id = invoice_line_ref.create(vals_line)

                event_lines.append(line.event_line_id.id)

        #invoice.signal_workflow('invoice_open')
        ev_line = self.env['sale.event.line'].browse(event_lines)
        ev_line.write({'state': 'sold', 'invoice_id': invoice.id})
        return ev_line[0].action_view_doc(case='invoice')    #{'type': 'ir.actions.act_window_close'}


class EventInvoiceLine(models.TransientModel):

    _name = 'sale.event.invoice.wizard.line'
    _description = "Productos a facturar"

    wizard_id = fields.Many2one('sale.event.invoice.wizard', string='Evento a facturar')
    event_line_id = fields.Many2one('sale.event.line', string='Línea de Producto')
    product_id = fields.Many2one('product.product', 'Producto', readonly='1')
    quantity = fields.Float('Cantidad', digits=dp.get_precision('Product Unit of Measure'), required=True, readonly=True)
    price_unit = fields.Float('Precio Unitario', digits=dp.get_precision('Product Price'), readonly=True)
    subtotal = fields.Float('Subtotal', digits=dp.get_precision('Product Price'), readonly=True)
    checked = fields.Boolean('Checked')

    @api.multi
    def check_line(self):
        self.write({'checked': True})

    @api.multi
    def uncheck_line(self):
        self.write({'checked': False})