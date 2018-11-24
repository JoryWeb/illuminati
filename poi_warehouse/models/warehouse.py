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
import odoo.addons.decimal_precision as dp
from odoo.osv import expression
from odoo import SUPERUSER_ID
from odoo.exceptions import except_orm, Warning, RedirectWarning

class stock_warehouse(models.Model):

    _inherit = "stock.warehouse"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica')
    enabled_for_sale= fields.Boolean('Enabled for Sales')
    street = fields.Char(string='Street', related='partner_id.street', readonly=True, store=True)
    street2 = fields.Char(string='Street2', related='partner_id.street2', readonly=True, store=True)
    zip = fields.Char(string='Zip', related='partner_id.zip', readonly=True, store=True)
    city = fields.Char(string='City', related='partner_id.city', readonly=True, store=True)
    state_id = fields.Many2one('res.country.state',string='State', related='partner_id.state_id', readonly=True, store=True)
    country_id = fields.Many2one('res.country',string='Country', related='partner_id.country_id', readonly=True, store=True)
    email = fields.Char(string='Email', related='partner_id.email', readonly=True, store=True)
    phone = fields.Char(string='Phone', related='partner_id.phone', readonly=True, store=True)
    #fax = fields.Char(string='Fax', related='partner_id.fax', readonly=True, store=True)
    mobile = fields.Char(string='Mobile', related='partner_id.mobile', readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True)
    active = fields.Boolean(string='Active', default=True)
    other_info = fields.Char(string='Other Info')
    user_ids = fields.Many2many('res.users', 'res_shop_res_users_rel', 'shop_id', 'user_id', string='Users Assigned')
    agency_id = fields.Many2one('res.agency',string='Agency')
    branch = fields.Char('Sucursal')




    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     if not self.env.context.get('display_all'):
    #         newargs = expression.AND([args]+[[('user_ids','in',self.env.uid)]])
    #         res = super(stock_warehouse, self).name_search(name=name, args=newargs, operator=operator, limit=limit)
    #         if not res:
    #             res = super(stock_warehouse, self).name_search(name=name, args=args, operator=operator, limit=limit)
    #     else:
    #         res = super(stock_warehouse, self).name_search(name=name, args=args, operator=operator, limit=limit)
    #     return res

    @api.onchange("country_id")
    def on_change_country(self):
        res = {'domain': {'state_id': []}}
        if self.country_id:
            currency_id = self.env['res.country'].browse(self.country_id.id).currency_id.id
            res['domain'] = {'state_id': [('country_id','=',country_id)]}

    @api.onchange("state_id")
    def onchange_state(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id
