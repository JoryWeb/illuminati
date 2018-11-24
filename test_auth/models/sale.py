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


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _authmode = True

    @api.multi
    def print_quotation(self):
        auth = self.check_authorization(code='sale.order.print.quotation')
        if auth:
            res = super(SaleOrder, self).print_quotation()
            return res
        return True

    @api.multi
    def on_authorized(self):
        code = self.auth_log_id.auth_id.code
        res = super(SaleOrder, self).on_authorized()
        if code == 'sale.order.print.quotation':
            self.print_quotation()
        return res
