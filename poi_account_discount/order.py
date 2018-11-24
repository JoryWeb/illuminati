# -*- encoding: utf-8 -*-
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


import openerp.addons.decimal_precision as dp
from openerp import models, fields, api, _
from openerp.exceptions import UserError


# class purchase_order(osv.osv):
#     """ Description """
#     _inherit = 'purchase.order'
#
#     def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
#
#         cur_obj=self.pool.get('res.currency')
#         for order in self.browse(cr, uid, ids, context=context):
#             # compute original amounts
#             res = super(purchase_order, self)._amount_all(cr, uid, ids, field_name, arg, context)
#             # Taxes are applied line by line, we cannot apply a discount on taxes that are not proportional
#             if not all(sum([[t.type=='percent' for t in line.taxes_id] for line in order.order_line],[])):
#                 raise osv.except_osv(('Discount error'), ('Unable (for now) to compute a global discount with non percent-type taxes'))
#             # add discount
#             cur = order.pricelist_id.currency_id
#             amount_untaxed = sum([line.price_subtotal for line in order.order_line])
#             discount_amount = amount_untaxed * order.discount_global/100
#             res[order.id]['discount_amount'] = cur_obj.round(cr, uid, cur, discount_amount)
#             res[order.id]['amount_net'] = res[order.id]['amount_untaxed'] - res[order.id]['discount_amount']
#             # we apply a discount on the tax as well. We might have rounding issue
#             res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, res[order.id]['amount_tax'] * (100.0 - (order.discount_global or 0.0))/100.0)
#             res[order.id]['amount_total'] = res[order.id]['amount_net'] + res[order.id]['amount_tax']
#         return res
#
#     _columns = {
#         'discount_global': fields.float('Descuento Global (%)', digits_compute= dp.get_precision('Account')),
#         'discount_amount': fields.function(_amount_all, method=True, store=True, multi='sums',
#                                             digits_compute= dp.get_precision('Purchase Price'),
#                                             string='Monto Descontado',
#                                             help="The additional discount on untaxed amount."),
#         'amount_net': fields.function(_amount_all, method=True, store=True, multi='sums',
#                                           digits_compute= dp.get_precision('Purchase Price'),
#                                           string='Monto Neto',
#                                           help="The amount after additional discount."),
#     }
#
#     def action_invoice_create(self, cr, uid, ids, context=None):
#
#         inv_obj = self.pool.get('account.invoice')
#         for order in self.browse(cr, uid, ids, context):
#             # create the invoice
#             inv_id = super(purchase_order, self).action_invoice_create(cr, uid, ids, context)
#             # modify the invoice
#             inv_obj.write(cr, uid, [inv_id], {'discount_global': order.discount_global or False}, context)
#             inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)
#             res = inv_id
#         return res
#
# purchase_order()
class productpricelistitem(models.Model):
    _inherit = 'product.pricelist.item'
    desc_max = fields.Float('Max. Desc.(%)', size=10, help="Configure el maximo desuento", default=0.0)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    discount_global = fields.Float(string='Descuento Global (%)', digits=dp.get_precision('Discount'), default=0.0)
    discounted_amount = fields.Float(string='Monto Descontado', digits=dp.get_precision('Discount'), default=0.0)

    @api.multi
    @api.onchange('discount_global')
    def discount_global_change(self):
        if self.discount_global < 0:
            self.discount_global = 0

        if self.discount_global >= 0:
            for lines in self.order_line:
                price_products = self.env['product.pricelist.item'].search(
                    [("pricelist_id", "=", self.pricelist_id.id), ("product_id", "=", lines.product_id.id)])
                # Realizar busqueda de producto en esta parte
                if price_products:
                    price_product = price_products[0]
                    if self.discount_global > price_product.desc_max:
                        raise UserError(
                            _(u'Descuento máximo superado en producto: "%s"') % \
                            (lines.product_id.name_template,))
                    else:
                        lines.discount = self.discount_global
                else:
                    lines.discount = self.discount_global

    def launch_discount_wizard(self, cr, uid, ids, context=None):

        if context is None:
            context = {}

        order = self.browse(cr, uid, ids, context=context)[0]

        context = dict(context, order_id=order.id)
        data_obj = self.pool.get('ir.model.data')
        id2 = data_obj._get_id(cr, uid, 'poi_account_discount', 'view_poi_discount_wizard')
        if id2:
            id2 = data_obj.browse(cr, uid, id2, context=context).res_id
        if id2:
            return {
                'name': "Descuento en base a Monto",
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(id2, 'form')],
                'res_model': 'poi.discount.wizard',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': str([]),
                'context': context,
            }

# sale_order()

# class sale_line(osv.osv):
#     """ Description """
#     _inherit = 'sale.order.line'
#
#     def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
#             uom=False, qty_uos=0, uos=False, name='', partner_id=False,
#             lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None, discount_global=False):
#
#         ret_values = super(sale_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag, context)
#
#         context = context or {}
#         discount_global=context.get('discount_global', False)
#         if discount_global:
#             ret_values['value']['discount'] = discount_global
#
#         return ret_values
#
# sale_line()
