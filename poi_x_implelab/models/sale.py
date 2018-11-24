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
from openerp import fields, models, api, _
from openerp.exceptions import Warning, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from lxml import etree
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta, date

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    mer2 = fields.Float('Mer', required=True, default=1, digits=dp.get_precision('Product Price'))
    factor2 = fields.Float('Factor', required=True, default=1, digits=dp.get_precision('Product Price'))
    subtotal = fields.Float('Subtotal', readonly=True, compute='_compute_amount', store=True, digits=dp.get_precision('Product Price'))
    unitario_factor = fields.Float('Unitario con Factor', readonly=True, compute='_compute_amount', store=True, digits=dp.get_precision('Product Price'))
    subtotal_2 = fields.Float('SUBTOTAL', readonly=True, compute='_compute_amount', store=True, digits=dp.get_precision('Product Price'))

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'mer2', 'factor2')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            unitario_factor = line.mer2 * line.factor2
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, unitario_factor,
                                            product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'unitario_factor': taxes['total_included'],
                'price_tax': (taxes['total_included'] * line.product_uom_qty) -
                             (taxes['total_excluded'] * line.product_uom_qty),
                'price_total': taxes['total_included'] * line.product_uom_qty,
                'price_subtotal': taxes['total_excluded'] * line.product_uom_qty,
                'subtotal': taxes['total_excluded'],
            })

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res.update({
            'price_unit': self.unitario_factor,
        })

        return res

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """

        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    unitario_factor = line.mer2 * line.factor2
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, unitario_factor,
                                                    product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })
