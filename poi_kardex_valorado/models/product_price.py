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

import logging
from odoo import models, fields, api

# All field name of product that will be historize
PRODUCT_FIELD_HISTORIZE = ['standard_price']

_logger = logging.getLogger(__name__)


class ProductPriceHistory(models.Model):
    _inherit = 'product.price.history'
    @api.one
    @api.depends('res_id')
    def _get_sources(self):
        origin = ''
        if not self.res_id or self.res_id == "None,None":
            origin = u'Creación del producto'
        else:
            object = self.res_id.split(',')[0]
            id = int(self.res_id.split(',')[1])
            if object in ('product.template', 'product.product'):
                origin = u'Revalorización'
            elif object != 'None':
                value_object = self.env[object].browse(id)
                origin = value_object.name
            else:
                origin = 'Desconocido'
        self.origin = origin

    cost = fields.Float(string='Costo', digits=(10, 20))
    qty = fields.Float(string='Stock en fecha')
    res_id = fields.Char(string=u'Origen', index=True, readonly=True, default='', copy=False)
    origin = fields.Char(string=u'Origin de revaloriacion', compute=_get_sources, copy=False)

