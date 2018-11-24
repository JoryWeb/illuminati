# -*- coding: utf-8 -*-
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

from openerp import models, fields, api, _
from openerp import SUPERUSER_ID

class ResUsers(models.Model):
    _inherit = 'res.users'

    shop_ids = fields.Many2many('stock.warehouse','res_shop_res_users_rel','user_id','shop_id', string='Shops Assigned')
    shop_assigned = fields.Many2one('stock.warehouse', string='Shop Assigned')
    multi_shop = fields.Boolean(string='Multishop', help='In case that this field is false, user is not allowed to change his/her shop assigned', default=True)

    def set_shop_assigned(self, cr, uid, shop_id, context=None):
        user_obj = self.browse(cr, uid, uid)
        if user_obj.multi_shop:
            self.write(cr, SUPERUSER_ID, uid, {'shop_assigned': shop_id})
            #self.write(cr, uid, uid, {'shop_assigned': shop_id})
        else:
            return False
        return True

    @api.cr_uid_context
    def get_allowed_shops(self, cr, uid, context=None):
        shop_pool = self.pool.get('stock.warehouse')
        shop_ids = shop_pool.search(cr, uid, [('user_ids', 'in', uid)])
        return shop_ids

    @api.cr_uid_context
    def get_allowed_warehouses(self, cr, uid, context=None):
        shop_pool = self.pool.get('stock.warehouse')
        shop_ids = shop_pool.search(cr, uid, [('user_ids', 'in', uid)])
        warehouse_ids = [s.warehouse_id.id for s in shop_pool.browse(cr, uid, shop_ids)]
        return warehouse_ids

    @api.cr_uid_context
    def get_allowed_locations(self, cr, uid, context=None):
        shop_pool = self.pool.get('stock.warehouse')
        shop_ids = shop_pool.search(cr, uid, [('user_ids', 'in', uid)])
        location_ids = [s.warehouse_id.lot_stock_id.id for s in shop_pool.browse(cr, uid, shop_ids)]
        return location_ids