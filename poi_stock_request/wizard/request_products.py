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

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class PoiRequestProducts(models.TransientModel):
    _name = 'poi.request.products'
    _description = 'Request Products Wizard'

    picking_id = fields.Many2one('stock.picking', 'Albaran')
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacén de requerimiento')
    request_lines = fields.One2many('poi.request.products.line', 'request_wizard_id', 'Lineas')

    @api.model
    def default_get(self, fields):
        res = super(PoiRequestProducts, self).default_get(fields)
        picking_ids = self.env.context.get('active_ids', False)

        if not picking_ids or len(picking_ids) != 1:
            return res

        picking_id, = picking_ids
        picking = self.env['stock.picking'].browse(picking_id)

        lines = []
        for move in picking.move_lines:
            if move.state in ('done'):
                qty_reserve = move.reserved_availability
                item = {
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    #'lot_id': move.restrict_lot_id.id,
                    'quantity': move.product_uom_qty - qty_reserve,
                }
                lines.append(item)

        res['request_lines'] = [(0, 0, x) for x in lines]
        return res

    @api.multi
    def do_request(self):

        req_obj = self.env['stock.request']
        warehouse_obj = self.env['stock.warehouse']
        lines = []
        for line in self.request_lines:
            line_data = {
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'product_uom_id': line.product_uom_id.id,
                'lot_id': line.lot_id.id,
            }
            lines.append(line_data)



        picking_ids = self.env.context.get('active_ids', False)

        picking_id, = picking_ids
        picking = self.env['stock.picking'].browse(picking_id)
        request_data = {'warehouse_dest_id': self.warehouse_id.id,
                        'picking_id': picking.id}

        req_name = _('Request for ') + picking.name + '-' + (picking.origin or '')

        return req_obj.create_request(req_name, lines, request_data=request_data)

    @api.multi
    def wizard_view(self):
        view = self.env.ref('poi_stock_request.view_stock_request_products')

        return {
            'name': _('Request Products'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'poi.request.products',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context,
        }


class PoiRequestProductsLine(models.TransientModel):
    _name = 'poi.request.products.line'
    _description = 'Productos de solicitudes de stock'

    request_wizard_id = fields.Many2one('poi.request.products', 'Wizard')
    product_id = fields.Many2one('product.product', 'Producto')
    product_uom_id = fields.Many2one('product.uom', 'Unidad de Medida')
    quantity = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0)
    lot_id = fields.Many2one('stock.production.lot', 'Serie/Lote')

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        self.product_uom_id = self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)],
                            'lot_id': [('product_id', '=', self.product_id.id)]}

        return result
