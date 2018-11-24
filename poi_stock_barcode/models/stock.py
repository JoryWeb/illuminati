##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
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

from openerp import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    barcode_move = fields.Char(u"Codigo Barras", help=u"Colocar el puntero sobre este campo y proceder a escanear los productos")
    barcode_operation = fields.Char(u"Codigo Barras", help=u"Colocar el puntero sobre este campo y proceder a escanear los productos")

    # Load all unsold PO lines
    @api.onchange('barcode_move')
    def barcode_move_change(self):
        if self.barcode_move:
            product = self.env['product.product'].search([('barcode', '=', self.barcode_move)])
            if product:
                new_lines = self.env['stock.move']
                ban = True
                for lines in self.move_lines:
                    if lines.product_id.id == product.id:
                        lines.product_uom_qty = lines.product_uom_qty + 1
                        ban = False
                        break
                if ban:
                    data = {
                        'name': product.default_code and product.name or "/",
                        'company_id': self.company_id.id,
                        'date_expected': self.min_date or fields.Datetime.now(),
                        'date': self.min_date or fields.Datetime.now(),
                        'procure_method': 'make_to_stock',
                        'product_id': product.id,
                        #'picking_id': self.id,
                        'product_uom_qty': 1,
                        'product_uom': product.uom_id.id,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'picking_type_id': self.picking_type_id.id,
                        'state': 'draft',
                    }
                    #new_lines.create(data)
                    new_line = new_lines.new(data)
                    new_lines += new_line

                    self.move_lines += new_lines
            self.barcode_move = ''
        return {}

    # Load all unsold PO lines
    @api.onchange('barcode_operation')
    def barcode_operation_change(self):
        if self.barcode_operation:
            product = self.env['product.product'].search([('barcode', '=', self.barcode_operation)])
            if product:
                for lines in self.pack_operation_product_ids:
                    if lines.product_id.id == product.id:
                        lines.qty_done = lines.qty_done + 1
            self.barcode_operation = ''
        return {}