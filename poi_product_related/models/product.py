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

import re
from datetime import datetime, timedelta

from openerp import models, fields, api, _
from openerp import SUPERUSER_ID
from openerp import pooler
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.osv import expression
from openerp.tools import float_is_zero, float_compare
from openerp.tools.misc import formatLang

from openerp.exceptions import UserError, RedirectWarning, ValidationError

import openerp.addons.decimal_precision as dp
import logging

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_related_ids = fields.Many2many('product.template', 'product_template_related_rel', 'product_tmpl_id', 'product_tmpl_related', 'Products Related')

    @api.model
    def create(self, vals):
        new_product = super(ProductTemplate, self).create(vals)
        if vals.get('product_related_ids'):
            products_related = vals.get('product_related_ids')
            for itm in products_related:
                if itm[0] == 6:
                    for rel in itm[2]:
                        rel_product = self.browse(rel)
                        rel_product.write({'product_related_ids': [[4, new_product.id]]})
            new_product
        return new_product

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if vals.get('product_related_ids'):
            products_related = vals.get('product_related_ids')
            for itm in products_related:
                if itm[0] == 6:
                    products_with_relation = self.search([('product_related_ids','=',self.id)])
                    products_with_relation_ids = [x.id for x in products_with_relation]
                    for related in products_with_relation:
                        if related.id not in itm[2]:
                            related.write({'product_related_ids': [[3, self.id]]})
                    for rel in itm[2]:
                        if rel not in products_with_relation_ids:
                            rel_product = self.browse(rel)
                            rel_product.write({'product_related_ids': [[4, self.id]]})
        return res