#!/usr/bin/env python
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


from odoo import models, fields, api, _, tools
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"


    @api.multi
    def compute_refund(self, mode='refund'):
        res = super(AccountInvoiceRefund, self).compute_refund(mode)
        inv_id = self.env.context.get('active_id', False)
        ids = res.get('domain', False)
        if inv_id and ids:
            inv = self.env['account.invoice']
            inv_id_obj = inv.browse(inv_id)
            if (inv_id_obj.order_id or inv_id_obj.skip_order) and inv_id_obj.type != 'in_invoice':
                ids = ids[1]
                for i in inv.search([ids]):
                    if inv_id_obj.order_id:
                        i.order_id = inv_id_obj.order_id
                        i.sale_type_id = inv.sale_type_id.id
                    if inv_id_obj.skip_order:
                        i.skip_order = True
        return res
