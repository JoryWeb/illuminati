##############################################################################
#
#    odoo, Open Source Management Solution
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

from odoo import models, fields, api, _
from odoo import SUPERUSER_ID

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_giftcard = fields.Boolean('Allow GiftCards', help='Allow the cashier to accept giftcards on the whole order.')
    giftcard_product_id = fields.Many2one('product.product', 'GiftCard Product',
                                           domain="[('available_in_pos', '=', True)]",
                                           help='The product used to model the giftcard')


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    giftcard_code = fields.Char("GiftCard Code")
    giftcard_code_used = fields.Char("GiftCard Code Used")

    @api.cr_uid_context
    def _order_line_fields(self, cr, uid, line, context=None):
        if line and 'giftcard_code' in line[2] and line[2]['giftcard_code']:
            product = self.pool['product.product'].browse(cr, uid, line[2]['product_id'], context=context)
            product.product_tmpl_id.add_giftcard(line[2]['giftcard_code'])
        if line and 'giftcard_code_used' in line[2] and line[2]['giftcard_code_used']:
            giftcard_line = self.pool['product.template.gift.card'].search(cr, uid, [('code','=',line[2]['giftcard_code_used'])])
            amount_used = line[2]['price_unit']
            if giftcard_line:
                gc = self.pool['product.template.gift.card'].browse(cr, uid, giftcard_line[0])
                gc.write({'remaining_amount': gc.remaining_amount - abs(amount_used)})
        return line

