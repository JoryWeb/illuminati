# © 2014-2015 Avanzosc
# © 2014-2015 Pedro M. Baeza
# © 2016 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models, SUPERUSER_ID

class StockMove(models.Model):
    _inherit = 'stock.move'

    def product_price_update_before_done(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.product')
        tmpl_dict = {}
        for move in self.browse(cr, uid, ids, context=context):
            # adapt standard price on incomming moves if the product cost_method is 'average'
            # Aplicar que el costo del producto sera actualizado por el ingreso de las producciones
            if (move.location_id.usage in ('supplier', 'production')) and (move.product_id.cost_method == 'average'):
                product = move.product_id
                product_id = move.product_id.id
                qty_available = move.product_id.qty_available
                if tmpl_dict.get(product_id):
                    product_avail = qty_available + tmpl_dict[product_id]
                else:
                    tmpl_dict[product_id] = 0
                    product_avail = qty_available
                # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
                price_unit = self.pool.get('stock.move').get_price_unit(cr, uid, move, context=context)
                if product_avail <= 0:
                    new_std_price = price_unit
                else:
                    # Get the standard price
                    amount_unit = product.standard_price
                    new_std_price = ((amount_unit * product_avail) + (price_unit * move.product_qty)) / (product_avail + move.product_qty)
                tmpl_dict[product_id] += move.product_qty
                # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
                ctx = dict(context or {}, force_company=move.company_id.id)
                product_obj.write(cr, SUPERUSER_ID, [product.id], {'standard_price': new_std_price}, context=ctx)
