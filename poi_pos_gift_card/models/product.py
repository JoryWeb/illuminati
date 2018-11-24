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


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_gift_card = fields.Boolean("Is a gift card")
    gc_amount = fields.Float("Gift Card Amount")
    gc_expiry_type = fields.Selection([('time', 'Time'),
                                       ('date', 'Date'), ('undefined', 'Undefined')], "Expiry Type")
    gc_days_expiry = fields.Integer("Expiry days")
    gc_expiry_date = fields.Date("Expiry date")
    gift_card_ids = fields.One2many("product.template.gift.card", "template_id", "Gift Cards")

    @api.multi
    def add_giftcard(self, code):
        for product in self:
            expiry_date = False
            # TODO: ADD expiry date
            product.write({
                'gift_card_ids': [
                    (0, 0, {'code': code, 'amount': product.gc_amount, 'remaining_amount': product.gc_amount})]
            })


class ProductTemplateGiftCard(models.Model):
    _name = "product.template.gift.card"
    template_id = fields.Many2one("product.template", "Product Template")
    code = fields.Char("Code", required=True)
    partner_id = fields.Many2one("res.partner", "Partner who acquired")  # TODO: Remove it's not needed!
    amount = fields.Float("Amount")
    remaining_amount = fields.Float("Remaining Amount")
    expiry_date = fields.Date("Expiry Date")

    @api.one
    @api.constrains('code')
    def _check_code(self):
        if self.search([('code','=',self.code),('id', '!=', self.id)]):
            raise ValidationError("You can't use the same code. This code is already used")