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

from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError

import operator as py_operator

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}

class ProductProduct(models.Model):
    _inherit = "product.product"
    @api.one
    def _get_moves(self):
        for product in self:
            moves = self.env['stock.move'].search([('product_id', '=', product.id)])
            product.qty_moves = len(moves)

    qty_moves = fields.Integer(string=u'Cantidad Movimientos', compute='_get_moves', search='_search_get_moves', copy=False)

    def _search_get_moves(self, operator, value):
        if value == 0.0 and operator in ('=', '>=', '<=', '>', '<'):
            ids = []
            cr = self.env.cr
            cr.execute("""select product_id from stock_move
                          where state in ('done')
                        group by product_id""")
            result = cr.fetchall()
            for res in result:
                ids.append(res[0])
            return [('id', 'in', ids)]

    def _search_product_moves(self, operator, value, field):
        # TDE FIXME: should probably clean the search methods
        # to prevent sql injections
        if field not in ('qty_moves'):
            raise UserError(_('Invalid domain left operand %s') % field)
        if operator not in ('<', '>', '=', '!=', '<=', '>='):
            raise UserError(_('Invalid domain operator %s') % operator)
        if not isinstance(value, (float, int)):
            raise UserError(_('Invalid domain right operand %s') % value)
        ids = []
        for product in self.search([]):
            if OPERATORS[operator](product[field], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    @api.multi
    def open_product_historic_prices(self):
        res = self.env['ir.actions.act_window'].for_xml_id(
            'poi_product_price_history', 'action_price_history')
        res['domain'] = ((res.get('domain', []) or []) +
                         [('product_id', 'in', self.ids)])
        return res

    # def _set_standard_price(self, cr, uid, product_id, value, context=None):
    #     ''' Store the standard price change in order to be able to retrieve the cost of a product template for a given date'''
    #     #Considerando que cuando context viene con None es de una revalorización de inventario
    #     if context is None:
    #         context = {}
    #         price_history_obj = self.pool['product.price.history']
    #         user_company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
    #         company_id = context.get('force_company', user_company)
    #         res_id = 'product.template' + ',' + str(product_id)
    #     else:
    #         price_history_obj = self.pool['product.price.history']
    #         user_company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
    #         company_id = context.get('force_company', user_company)
    #         res_id = str(context.get('active_model')) + ',' + str(context.get('active_id'))
    #
    #     domain_quant = [('product_id', 'in', [product_id]),
    #                     ('location_id.usage', '=', 'internal')]
    #     quants = self.pool.get('stock.quant').search(cr, uid, domain_quant, {})
    #     qty_total = 0
    #     for quant in quants:
    #         quant_data = self.pool.get('stock.quant').browse(cr, uid, quant, {})
    #         qty_total = qty_total + quant_data.qty
    #     price_history_obj.create(cr, uid, {
    #         'product_id': product_id,
    #         'cost': value,
    #         'company_id': company_id,
    #         'res_id': str(res_id),
    #         'qty': qty_total,
    #     }, context=context)