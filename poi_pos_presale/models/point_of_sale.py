##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import logging
import pdb
import time

import odoo
from odoo import netsvc, tools
from odoo.osv import osv
from odoo.tools.translate import _
from odoo.tools import float_is_zero
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class pos_order(osv.osv):
    _inherit = 'pos.order'

    def _fetch_orderline_values(self, cr, uid, orderline, context=None):
        values = {'unique_name': orderline.get('unique_name') or '',
                  'discount': orderline.get('discount'),
                  'price_unit': orderline.get('price_unit'),
                  'product_id': orderline.get('product_id'),
                  'qty': orderline.get('qty'),
                  }
        return values

    def save_orderline_from_ui(self, cr, uid, order_id, orderline_data, context=None):
        if not context:
            context = {}

        context['no_synch'] = True

        if not order_id:
            return True

        pos_line_object = self.pool.get('pos.order.line')
        if orderline_data:
            orderline = orderline_data[0]
            line_properties = self._fetch_orderline_values(cr, uid, orderline, context=context)
            line_properties['order_id'] = order_id
        else:
            return True
        if orderline.get('unique_name'):
            line_ids = pos_line_object.search(cr, uid, [('unique_name', '=', orderline.get('unique_name'))])

        if line_ids:
            line_id = line_ids[0]
            # ToDo: Get remove???
            if orderline.get('remove'):
                pos_line_object.unlink(cr, uid, line_id, context=context)
            pos_line_object.write(cr, uid, line_id, line_properties, context=context)
        else:
            pos_line_object.create(cr, uid, line_properties, context=context)




