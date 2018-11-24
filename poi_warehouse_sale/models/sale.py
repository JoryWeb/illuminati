##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2014 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Grover Menacho
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

from odoo import models, fields, api, _


class sale_order(models.Model):
    _inherit = "sale.order"

    @api.model
    def _default_warehouse_id(self):
        return self.env['res.users'].browse(self.env.context.get('uid', [])).shop_assigned

    @api.model
    def _default_project_id(self):
        shop_assigned = self.env['res.users'].browse(self.env.context.get('uid', [])).shop_assigned
        return self.env['stock.warehouse'].browse(shop_assigned.id).analytic_account_id

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                   default=_default_warehouse_id)

    project_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                 help="The analytic account related to a sales order.", copy=False,
                                 domain=[('account_type', '=', 'normal')],
                                 default=_default_project_id)
