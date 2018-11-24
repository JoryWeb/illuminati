##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

class PurchaseDeliveryProduct(models.Model):
    _name = 'purchase.delivery.product'
    _description = 'Product delivery date purchase plan'
    _inherit = ['mail.thread']

    purchase_id = fields.Many2one('purchase.order', 'Orden de Compra', required=True)
    purchase_line_id = fields.Many2one('purchase.order.line', 'Linea de Compra')
    product_id = fields.Many2one('product.product', 'Producto', required=True, readonly=True)
    delivery_date = fields.Date(u'Fecha Recepción', required=True, help=u'Fecha en el que pruducto sera entregado al almacén')
    product_qty = fields.Float('Cantidad planificada', default=0.0, required=True)
