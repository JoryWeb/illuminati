##############################################################################
#
#    Odoo Module
#    Copyright (C) 2015 Grover Menacho (<http://www.grovermenacho.com>).
#    Copyright (C) 2015 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Grover Menacho
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

from odoo import models, fields, modules, api, _


class ProductPricelist(models.Model):
    _name = 'product.pricelist'
    _inherit = ['product.pricelist', 'mail.thread']

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'


    @api.multi
    def _compute_product_id2(self):
        product_obj = self.env['product.product']
        for s in self:
            if s.applied_on in ('1_product'):
                product_ids = product_obj.search([('product_tmpl_id', '=', s.product_tmpl_id.id )], limit=1)
                if product_ids:
                    s.product_id2 = product_ids[0].id
            elif s.applied_on in ('0_product_variant'):
                s.product_id2 = s.product_id.id

    product_id2 = fields.Many2one('product.product', 'Producto', compute="_compute_product_id2")
