# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, api

from .product_price import PRODUCT_FIELD_HISTORIZE


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def open_product_historic_prices(self):
        res = self.env['ir.actions.act_window'].for_xml_id(
            'poi_product_price_history', 'action_price_history')
        res['domain'] = ((res.get('domain', []) or []) +
                         [('product_id', 'in', self.ids)])
        return res




    def _set_standard_price(self, cr, uid, product_id, value, context=None):
        ''' Store the standard price change in order to be able to retrieve the cost of a product template for a given date'''
        #Considerando que cuando context viene con None es de una revalorización de inventario
        if context is None:
            context = {}
            price_history_obj = self.pool['product.price.history']
            user_company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
            company_id = context.get('force_company', user_company)
            res_id = 'product.template' + ',' + str(product_id)
        else:
            price_history_obj = self.pool['product.price.history']
            user_company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
            company_id = context.get('force_company', user_company)
            res_id = str(context.get('active_model')) + ',' + str(context.get('active_id'))
        price_history_obj.create(cr, uid, {
            'product_id': product_id,
            'cost': value,
            'company_id': company_id,
            'res_id': str(res_id),
        }, context=context)