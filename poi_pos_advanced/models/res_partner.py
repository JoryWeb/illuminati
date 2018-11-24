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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _get_last_pos_order(self):
        for partner in self:
            orders = self.env['pos.order'].sudo().search([('partner_id','=',partner.id)])
            if not orders:
                partner.last_purchase = ''
                partner.last_payment_method = ''
            else:
                last_order = False
                for o in orders:
                    if not last_order:
                        last_order = o
                    elif last_order.id < o.id:
                        last_order = o
                last_purchase = ''
                last_payment_method = ''
                for l in last_order.lines:
                    last_purchase += l.product_id.display_name + '  -  '
                for p in last_order.statement_ids:
                    last_payment_method += p.statement_id.journal_id.display_name + '  -  '
                partner.last_purchase = last_purchase
                partner.last_payment_method = last_payment_method

    @api.multi
    def _get_total_pos_order(self):
        for partner in self:
            orders = self.env['pos.order'].sudo().search([('partner_id','=',partner.id)])
            if not orders:
                partner.number_of_purchases = 0
                partner.total_purchases_amount = 0.0
            else:
                number_of_purchases = 0
                total_purchases_amount = 0.0
                for o in orders:
                    number_of_purchases += 1
                    total_purchases_amount += o.amount_total
                partner.number_of_purchases = number_of_purchases
                partner.total_purchases_amount = total_purchases_amount


    number_of_purchases = fields.Float("Number of Purchases", compute=_get_total_pos_order, store=False)
    last_purchase = fields.Text("Last Purchase", compute=_get_last_pos_order, store=False)
    client_category = fields.Selection([('a','A'),
                                        ('b','B')],"Client Category")
    last_payment_method = fields.Char("Last Payment Method", compute=_get_last_pos_order, store=False)
    total_purchases_amount = fields.Float("Total Purchases Amount", compute=_get_total_pos_order, store=False)