##############################################################################
#    
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Grover Menacho
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

from openerp.osv import fields, osv
from openerp.tools.translate import _

class discount_amount(osv.TransientModel):

    _name = "poi.discount.wizard"
    _description = "Descuento en base a Monto"

    _columns = {
        'order_id': fields.many2one('sale.order', string="Orden de venta"),
        'monto_real': fields.float('Monto lista'),
        'monto_descontado': fields.float('Monto descontado'),
    }

    def default_get(self, cr, uid, fields, context=None):

        if context is None:
            return {}


        if 'order_id' in context:
            order_id = context['order_id']
        elif 'active_ids' in context:
            order_id = context['active_ids'][0]

        init_vals = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        order = self.pool.get('sale.order').browse(cr, uid, [order_id], context=context)[0]

        if order.discount_global > 0:
            val_disc = order.amount_total*(order.discount_global/100)
            init_vals['monto_real'] = val_disc + order.amount_total
        else:
            init_vals['monto_real'] = order.amount_total

        init_vals['monto_descontado'] = order.amount_total
        init_vals['order_id'] = order_id
        return init_vals

    def action_discount(self, cr, uid, ids, context=None):
        order_obj = self.pool.get('sale.order')
        for wizard in self.browse(cr, uid, ids, context=context):
            if wizard.monto_real < wizard.monto_descontado:
                raise osv.except_osv(_('Accion Invalida'), _("Debe ingresar un descuento válido."))
            if wizard.monto_real > 0:
                new_discount = (100*(wizard.monto_real - wizard.monto_descontado)/wizard.monto_real)
            else:
                new_discount = 0.0

            order_obj.write(cr, uid, [wizard.order_id.id], {'discount_global': new_discount, 'discounted_amount': wizard.monto_descontado}, context=context)
            wizard.order_id.discount_global_change()

            #Aplicar descuento maximo en esta parte

            #order_obj._copy_global_discount(cr, uid, [wizard.order_id.id], context=context)
            #Verificar diferecia de centavos por redondeo y aplicar a última linea un descuento diferente para hacer cuadrar totales
            # amounts = order_obj.read(cr, uid, [wizard.order_id.id], ['amount_total','discounted_amount'], context=context)[0]
            # new_total = amounts['amount_total']
            # if new_discount > 0 and new_total != wizard.monto_descontado:
            #     diff = wizard.monto_descontado - new_total
            #     if abs(diff) < 0.02:
            #         order_line_obj = self.pool.get('sale.order.line')
            #         last_id = order_line_obj.search(cr, uid, [('order_id', '=', wizard.order_id.id)], limit=1, order='id desc')
            #         vals = order_line_obj.read(cr, uid, last_id, ['price_subtotal_with_tax','product_uom_qty','price_unit'])[0]
            #         disc_adj = (((vals['price_subtotal_with_tax'] + diff) / (vals['product_uom_qty']*vals['price_unit'])) - 1) * -100
            #         order_line_obj.write(cr, uid, last_id, {'discount': disc_adj}, context=context)

        return {'view_mode' : 'tree,form','type': 'ir.actions.act_window_close'}

discount_amount()