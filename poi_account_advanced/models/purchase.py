##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2011 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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


from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class purchase(osv.osv):

    _inherit = 'purchase.order'


    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):

        ret = super(purchase, self)._prepare_inv_line(cr, uid, account_id, order_line, context=context)

        if order_line.segment_id:
            ret['segment_id'] = order_line.segment_id.id

        return ret

class purchase_line(osv.osv):

    _inherit = 'purchase.order.line'

    _columns = {
        'segment_id': fields.many2one('account.segment', 'Segmento')
    }



