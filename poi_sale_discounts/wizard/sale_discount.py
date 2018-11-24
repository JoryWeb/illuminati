##############################################################################
#    
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from odoo.osv import osv, fields
import odoo.addons.decimal_precision as dp

import time

from odoo.tools.translate import _

class sale_discount_wizard(osv.TransientModel):
    
    _name='sale.discount.wizard'
    
    _columns = {
        'discount_amount': fields.float('Discount Amount', digits_compute=dp.get_precision('Point Of Sale')),
        'discount': fields.float('Discount (%)', digits=(16, 5), digits_compute=dp.get_precision('Percent')),
    }
    _defaults = {
        'discount_amount': lambda *a: 0.0,
        'discount': lambda *a: 0.0,
    }
    
    def apply_discounts(self, cr, uid, ids, context=None):
        pos_order_pool=self.pool.get('pos.order')
        pos_orderline_pool=self.pool.get('pos.order.line')
        
        sale_order_pool=self.pool.get('sale.order')
        sale_orderline_pool=self.pool.get('sale.order.line')
        
        order_id=context.get('order_id')
        
        for discount in self.browse(cr, uid, ids, context):
            discount_percentage = discount.discount
            discount_amount=discount.discount_amount
                
        total_order = 0
        total_discount = 0
        
        if context.get('type')=='pos.order':

            for order in pos_order_pool.browse(cr, uid, [order_id]):
                for orderline in order.lines:
                    total_order+=(orderline.price_unit * orderline.qty)
                    total_discount+=((orderline.price_unit * orderline.qty)*(orderline.discount/100))

            #Para el monto nuevo_descuento=((100*(discount-totaldiscount))/totalorder)+orderline.discount;
            if discount_amount>0:
                for order in pos_order_pool.browse(cr, uid, [order_id]):
                    for orderline in order.lines:
                        new_discount=((100*(discount_amount))/total_order)+orderline.discount
                        pos_orderline_pool.write(cr, uid, orderline.id, {'discount': new_discount})
            elif discount_percentage>0:
                for order in pos_order_pool.browse(cr, uid, [order_id]):
                    for orderline in order.lines:
                        pos_orderline_pool.write(cr, uid, orderline.id, {'discount': discount_percentage})
                        
        elif context.get('type')=='sale.order':

            for order in sale_order_pool.browse(cr, uid, [order_id]):
                for orderline in order.order_line:
                    total_order+=(orderline.price_unit * orderline.product_uom_qty)
                    total_discount+=((orderline.price_unit * orderline.product_uom_qty)*(orderline.discount/100))

            #Para el monto nuevo_descuento=((100*(discount-totaldiscount))/totalorder)+orderline.discount;
            if discount_amount>0:
                for order in sale_order_pool.browse(cr, uid, [order_id]):
                    for orderline in order.order_line:
                        new_discount=((100*(discount_amount))/total_order)
                        #Orderline subtotal
                        sub_total = orderline.price_unit * orderline.product_uom_qty
                        discount_amount_set = sub_total * new_discount * 0.01
                        sale_orderline_pool.write(cr, uid, orderline.id, {'discount': new_discount,
                                                                          'discount_amount': discount_amount_set})
            elif discount_percentage>0:
                for order in sale_order_pool.browse(cr, uid, [order_id]):
                    for orderline in order.order_line:
                        #Orderline subtotal
                        sub_total = orderline.price_unit * orderline.product_uom_qty
                        discount_amount_set = sub_total * discount_percentage * 0.01
                        sale_orderline_pool.write(cr, uid, orderline.id, {'discount': discount_percentage,
                                                                          'discount_amount': discount_amount_set})
                
        return {}
        