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


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def open_product_historic_prices(self):
        product_tmpl_ids = self.env['product.template']
        for product in self:
            #product_tmpl_ids |= product.product_tmpl_id
            product_ids = self.env['product.product'].search([('product_tmpl_id', '=', product.id)])
        res = self.env['ir.actions.act_window'].for_xml_id(
            'poi_product_price_history', 'action_price_history')
        res['domain'] = (
            (res.get('domain', []) or []) +
            [('product_id', 'in', product_ids.ids)])
        return res
