##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2011 Poiesis Consulting (<http://www.poiesisconsulting.com>). All Rights Reserved.
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import odoo
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _authmode = True

    @api.multi
    def button_confirm(self):
        auth = self.check_authorization(code='purchase.order.check.prices') #SI ESTA AUTORIZADO O SI NO NECESITA AUTORIZACION
        if auth:
            res = super(PurchaseOrder, self).button_confirm()
            return res
        return True

    @api.multi
    def on_authorized(self):
        code = self.auth_log_id.auth_id.code
        res = super(PurchaseOrder, self).on_authorized()
        if code == 'purchase.order.check.prices':
            self.button_confirm()
        return res

    @api.multi
    def on_rejected(self):
        code = self.auth_log_id.auth_id.code
        res = super(PurchaseOrder, self).on_authorized()
        if code == 'purchase.order.check.prices':
            for order in self:
                for line in order.order_line:
                    if line.price_unit > line.product_id.standard_price:
                        line.price_unit = line.product_id.standard_price
            self.button_confirm()
        return res
