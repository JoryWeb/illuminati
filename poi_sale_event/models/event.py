##############################################################################
#
#    Odoo Module
#    Copyright (C) 2015 Grover Menacho (<http://www.grovermenacho.com>).
#    Copyright (C) 2015 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Grover Menacho
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

import time
from openerp import models, fields, modules, api, _
from openerp import tools
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError

from openerp import SUPERUSER_ID
import os


class SaleEventType(models.Model):
    _name = 'sale.event.type'
    _description = "Tipo de Evento"

    name = fields.Char('Tipo', required=True)


class SaleEvent(models.Model):
    _name = 'sale.event'
    _description = 'Evento'

    _inherit = ['mail.thread']

    @api.model
    def _default_warehouse_id(self):
        warehouse_ids = self.env['res.users'].browse(self.env.context.get('uid', [])).shop_assigned
        if not warehouse_ids:
            company = self.env.user.company_id.id
            warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
            return warehouse_ids
        return warehouse_ids

    def _get_default_image(self):
        image_path = modules.get_module_resource('poi_sale_event', 'static/src/img', 'event_placeholder.jpg')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

    @api.one
    @api.depends('product_lines')
    def _compute_amounts(self):
        """
        Compute the amounts of the SO line.
        """

        total_lines = 0.0
        total_qty = 0.0
        total_price = 0.0
        total_picks = 0.0
        total_invs = 0.0
        for line in self.product_lines:
            total_lines += 1
            total_qty += line.quantity
            total_price += (line.quantity * line.price_unit)
            if line.picking_id:
                total_picks += 1
            if line.invoice_id:
                total_invs += 1

        self.total_lines = total_lines
        self.total_qty = total_qty
        self.total_price = total_price
        self.total_picks = total_picks
        self.total_invs = total_invs


    name = fields.Char('Evento', required=True)
    type_id = fields.Many2one('sale.event.type', string='Tipo de evento')
    image = fields.Binary("Foto", default=_get_default_image, attachment=True, help="This field holds the image used as photo for the event or presents, limited to 1024x1024px.")
    date_event = fields.Date(u'Día del evento', help=u"Fecha en la se llevará a cabo el evento")
    date_init = fields.Date(u'Fecha de apertura', copy=False, help="Fecha en la que se creo esta ficha de evento.")
    date_close = fields.Date(u'Fecha de cierre', readonly=True, help=u"Fecha en la que se cierra la gestión de entrega y facturación de la lista de regalos.")
    date_due = fields.Date(u'Fecha vencimiento de reserva', help=u"Fecha en la que debería vencer la reserva.")
    warehouse_id = fields.Many2one('stock.warehouse', u'Tienda/almacén', required=True, default=_default_warehouse_id)
    pricelist_id = fields.Many2one('product.pricelist', 'Lista de precio', required=True)
    organizer_id = fields.Many2one('res.partner', 'Organizado Por')
    partner_id = fields.Many2one('res.partner', 'Titular', required=True)
    phone = fields.Integer(u'Teléfono')
    mobile = fields.Integer(u'Celular')
    email = fields.Char('Email')
    contact_ids = fields.Many2many('res.partner', 'rel_event_partner', 'event_id', 'partner_id', string='Contactos')
    state = fields.Selection([('draft', 'Inicial'), ('canceled', 'Cancelado'), ('open', 'Abierto'), ('closed', 'Cerrado')], string='Estado', default='draft', required=True, readonly=True, copy=False)
    product_lines = fields.One2many('sale.event.line', 'event_id', string='Regalos')
    picking_rsv_id = fields.Many2one('stock.picking', u'Albarán de reserva', copy=False)
    picking_rsv_state = fields.Selection(string="Estado Reserva", related='picking_rsv_id.state')
    note = fields.Text('Notas')
    total_lines = fields.Float(compute='_compute_amounts', string='Total líneas', readonly=True, store=True)
    total_qty = fields.Float(compute='_compute_amounts', string='Total cantidad', readonly=True, store=True)
    total_price = fields.Float(compute='_compute_amounts', string='Total monto', readonly=True, store=True)
    total_picks = fields.Float(compute='_compute_amounts', string='Total Entregas', readonly=True, store=True)
    total_invs = fields.Float(compute='_compute_amounts', string='Total Facturas', readonly=True, store=True)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.phone = self.partner_id.phone or False
            self.mobile = self.partner_id.mobile or False
            self.email = self.partner_id.email or False
            self.pricelist_id = self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False

    @api.multi
    def launch_tree_view(self):

        # Lanzar asistente ade Añadir líneas

        view_id = self.env['ir.model.data'].xmlid_to_res_id('poi_sale_event.view_event_form_editabletree')

        wizard_form = {
            'name': u"Añadir Producto",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sale.event',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
        }
        return wizard_form

    @api.multi
    def action_view_products(self):

        #Lanzar asistente ade Añadir líneas

        view_id = self.env['ir.model.data'].xmlid_to_res_id('poi_sale_event.view_event_line_tree')

        wizard_form = {
            'name': u"Lista de Regalos",
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'sale.event.line',
            'type': 'ir.actions.act_window',
            'domain': [('event_id', '=', self.id)],
            'context': {'default_event_id': self.id, 'event_id': self.id},
            'views': [(view_id, 'tree')],
            'view_id': view_id,
        }
        return wizard_form

    @api.multi
    def dummy(self):
        #Boton dummy sólo para Guardar y cerrar el asistente de Añadir líneas
        self.write({})
        return {'view_mode': 'tree,form', 'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_init(self):

        if not self.warehouse_id.reserv_loc_id:
            raise UserError(_('El Almacén/Tienda del cual se esta vendiendo no tiene configurada ua Ubicación de reserva.'))
        reserv_loc_id = self.warehouse_id.reserv_loc_id.id

        #group_ab = self.env["procurement.group"].create({'name': 'RSRV_' + self.name})

        picking_rsv = self.env['stock.picking'].create({
            'partner_id': False,
            'picking_type_id': self.warehouse_id.int_type_id.id,
            'location_id': self.warehouse_id.lot_stock_id.id,
            'location_dest_id': reserv_loc_id,
        })

        for line in self.product_lines:
            self.env['stock.move'].create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking_rsv.id,
                'location_id': self.warehouse_id.lot_stock_id.id,
                'location_dest_id': reserv_loc_id,
            })

        picking_rsv.action_assign()
        self.write({'state': 'open', 'picking_rsv_id': picking_rsv.id, 'date_init': fields.Date.context_today(self)})
        return True


    @api.multi
    def action_view_reserv(self):

        # Lanzar asistente para procesar reserva

        view_id = self.env['ir.model.data'].xmlid_to_res_id('stock.view_picking_form')

        wizard_form = {
            'name': u"Albaran de Reserva",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'res_id': self.picking_rsv_id and self.picking_rsv_id.id or False,
        }
        return wizard_form

    @api.multi
    def open_invoice_wizard(self):

        # Lanzar asistente de Añadir líneas

        view_id = self.env['ir.model.data'].xmlid_to_res_id('poi_sale_event.view_sale_event_invoice_wizard')

        wizard_form = {
            'name': u"Productos a facturar",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sale.event.invoice.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
        }
        return wizard_form

    @api.multi
    def action_view_invoices(self):

        # Lanzar facturas
        invoices = []
        for line in self.product_lines:
            if line.invoice_id:
                invoices.append(line.invoice_id.id)

        view = {
            'name': u"Facturas",
            'view_mode': 'tree,kanban,form,calendar,pivot,graph',
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': [('id','in',invoices)],
        }
        return view

    @api.multi
    def open_picking_wizard(self):

        # Lanzar asistente de Añadir líneas

        view_id = self.env['ir.model.data'].xmlid_to_res_id('poi_sale_event.view_sale_event_pick_wizard')

        wizard_form = {
            'name': u"Productos a entregar",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sale.event.pick.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
        }
        return wizard_form

    @api.multi
    def action_view_pickings(self):

        # Lanzar facturas
        pickings = []
        for line in self.product_lines:
            if line.picking_id:
                pickings.append(line.picking_id.id)

        view = {
            'name': u"Albaranes",
            'view_mode': 'tree,kanban,form,calendar',
            'view_type': 'form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': [('id', 'in', pickings)],
        }
        return view

    @api.multi
    def action_close(self):
        #Valida que todos los productos esten o Devueltos o Vendidos
        for line in self.product_lines:
            pass

        self.write({'state': 'closed'})


class SaleEventLine(models.Model):
    _name = 'sale.event.line'
    _description = 'Lista Productos'

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {}

        vals = {}
        product = self.product_id.with_context(
            lang=self.event_id.partner_id.lang,
            partner=self.event_id.partner_id.id,
            quantity=vals.get('quantity') or self.quantity,
            date=self.event_id.date_init,
            pricelist=self.event_id.pricelist_id.id,
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        if self.event_id.pricelist_id and self.event_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id,product.taxes_id)
        self.update(vals)
        return {}

    event_id = fields.Many2one('sale.event', string='Evento')
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    product_image = fields.Binary(string='Foto', related='product_id.image')
    product_description = fields.Text(string=u'Descripción', related='product_id.description_sale')
    name = fields.Char(u'Descripción')
    partner_id = fields.Many2one('res.partner', 'Invitado', help="Nombre del invitado que compro el regalo.")
    quantity = fields.Float('Cantidad', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    price_unit = fields.Float('Precio Unitario', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    subtotal = fields.Float('Subtotal', digits=dp.get_precision('Product Price'), readonly=True)
    comment = fields.Char('Comentario')
    state = fields.Selection([('free', 'Libre'), ('sold', 'Vendido'), ('delivered', 'Entregado'),('taken', 'Llevado'),('devuelto', 'Devuelto'), ('anulado', 'Anulado')], "Estado", required=True, default='free')
    invoice_id = fields.Many2one('account.invoice', 'Factura')
    picking_id = fields.Many2one('stock.picking', u'Albarán entrega')

    @api.multi
    def action_view_doc(self, case):

        # Lanzar factura
        if case == 'invoice':
            res_obj = 'account.invoice'
            res_name = 'Factura de regalo'
            res_id = self.invoice_id and self.invoice_id.id or False
            view_id = self.env['ir.model.data'].xmlid_to_res_id('account.invoice_form')
        elif case == 'picking':
            res_obj = 'stock.picking'
            res_name = u'Albarán de entrega'
            res_id = self.picking_id and self.picking_id.id or False
            view_id = False
        else:
            raise UserError(
                _('Tipo de documento a desplegar no identificado.'))


        view = {
            'name': res_name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': res_obj,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'res_id': res_id,
        }
        return view