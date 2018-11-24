#########################################################################
#                                                                       #
# Copyright (C) 2015  Agile Business Group                              #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU Affero General Public License as        #
# published by the Free Software Foundation, either version 3 of the    #
# License, or (at your option) any later version.                       #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU Affero General Public Licensefor more details.                    #
#                                                                       #
# You should have received a copy of the                                #
# GNU Affero General Public License                                     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#                                                                       #
#########################################################################
import logging
from odoo import fields, models, api, _
import math

_logger = logging.getLogger(__name__)

def closeness(a, b):
    """Returns measure of equality (for two floats), in unit
       of decimal significant figures."""
    if a == b:
        return float("infinity")
    difference = abs(a - b)
    avg = (a + b)/2
    return math.log10( avg / difference )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_discounted = fields.Float('Descuento Total', compute="_compute_discount")
    discount_percentage = fields.Float('Porcentaje del Descuento (%)', compute="_compute_discount")

    @api.multi
    @api.depends("order_line")
    def _compute_discount(self):
        for s in self:
            total_discount = 0
            total_order = 0
            for order_line in s.order_line:
                total_discount += order_line.amount_discounted
                total_order += order_line.price_unit * order_line.product_uom_qty
            s.amount_discounted = total_discount
            if total_order > 0:
                discount_percentage = total_discount * 100 / total_order
            else:
                discount_percentage = 0.0

            s.discount_percentage = discount_percentage



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    amount_discounted = fields.Float('Descuento Total')

    @api.onchange("discount")
    def _onchange_discount(self):
        if not self.product_id:
            return

        if not self.amount_discounted:
            amount_discounted = 0.0


        if not self.discount or self.discount == 0:
            self.amount_discounted = 0.0
            return

        if self.discount > 0:
            final_discount = self.discount
            sub_total = self.price_unit * self.product_uom_qty
            discount_amount_set = sub_total * final_discount * 0.01
            if closeness(float(discount_amount_set),float(self.amount_discounted)) < 3:
                self.amount_discounted =  discount_amount_set

    @api.onchange("amount_discounted")
    def _onchange_amount_discount(self):
        if not self.amount_discounted or self.amount_discounted == 0:
            self.discount = 0.0
        if self.amount_discounted:
            sub_total = self.price_unit * self.product_uom_qty
            if sub_total == 0:
                return
            discount_set = float(self.amount_discounted) / float(sub_total) * 100.0
            if closeness(float(discount_set), float(self.discount)) < 3:
                self.discount = discount_set
