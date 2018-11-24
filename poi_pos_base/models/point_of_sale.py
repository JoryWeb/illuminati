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
from odoo import api, models
from odoo.osv import osv
from odoo.tools.translate import _
from odoo.tools import float_is_zero
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class pos_order(models.Model):

    _inherit = 'pos.order'

    def _on_refund_order(self, cr, uid, order_id, clone_id):
        return True

    def _on_refund_clone(self):
        return {}

    def _create_refund_order(self, cr, uid, order_id, context=None):
        line_obj = self.pool.get('pos.order.line')
        order = self.browse(cr, uid, order_id)

        current_session_ids = self.pool.get('pos.session').search(cr, uid, [
            ('state', '!=', 'closed'),
            ('user_id', '=', uid)], context=context)
        if not current_session_ids:
            raise UserError(
                _('To return product(s), you need to open a session that will be used to register the refund.'))


        copy_dict = {
            'name': order.name + ' REFUND',  # not used, name forced by create
            'session_id': current_session_ids[0],
            'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
        }

        copy_dict.update(self._on_refund_clone())

        # Creating Reverted Order
        clone_id = self.copy(cr, uid, order.id, copy_dict, context=context)

        # Reverting lines
        clone = self.browse(cr, uid, clone_id, context=context)
        for order_line in clone.lines:
            line_obj.write(cr, uid, [order_line.id], {
                'qty': -order_line.qty
            }, context=context)

        self._on_refund_order(cr, uid, order_id, clone_id)
        return clone_id

    def _on_duplicate_order(self, cr, uid, order_id, clone_id):
        return True

    def _create_duplicated_order(self, cr, uid, order_id, context=None):
        line_obj = self.pool.get('pos.order.line')
        order = self.browse(cr, uid, order_id)

        current_session_ids = self.pool.get('pos.session').search(cr, uid, [
            ('state', '!=', 'closed'),
            ('user_id', '=', uid)], context=context)
        if not current_session_ids:
            raise UserError(
                _('To return product(s), you need to open a session that will be used to register the refund.'))

        # Creating Reverted Order
        clone_id = self.copy(cr, uid, order.id, {
            'name': order.name + ' REFUND',  # not used, name forced by create
            'session_id': current_session_ids[0],
            'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
            'ui_order': False,
        }, context=context)

        self._on_duplicate_order(cr, uid, order_id, clone_id)

        return clone_id

    # We're going to fix the native REFUND, it's encapsulated so we're going to separate it
    def revert_order(self, cr, uid, ids, close=False, reopen=False, context=None):

        statement_line_obj = self.pool.get('account.bank.statement.line')

        if not context:
            context = {}

        revert_list = []
        duplicated_list = []
        for order_id in ids:
            clone_id = self._create_refund_order(cr, uid, order_id, context=context)
            order_obj = self.browse(cr, uid, order_id)

            if order_obj.amount_total < 0 and (reopen or close):
                raise osv.except_osv(_('Error!'), _('You cannot use reopen or close option on refund orders.'))

            revert_list.append(clone_id)

            if reopen:
                # We've to create a new order based on original
                duplicated_id = self._create_duplicated_order(cr, uid, order_id, context=context)
                duplicated_list.append(duplicated_id)

            if close:

                payment_ids = []

                clone_obj = self.browse(cr, uid, clone_id)

                for payment in order_obj.statement_ids:

                    clone_statement_id = False

                    for statement in clone_obj.session_id.statement_ids:
                        if statement.journal_id.id == payment.statement_id.journal_id.id:
                            clone_statement_id = statement.id
                            break

                    if not clone_statement_id:
                        raise osv.except_osv(_('Error!'), _(
                            'To return product(s), you need to open a session that will be used to register the refund.'))

                    copy_payment_id = payment.copy()
                    statement_line_obj.write(cr, uid, copy_payment_id.id,
                                             {'amount': -copy_payment_id.amount, 'statement_id': clone_statement_id})
                    payment_ids.append(copy_payment_id.id)

                statement_line_obj.write(cr, uid, payment_ids, {'pos_statement_id': clone_id})

                try:
                    self.signal_workflow(cr, uid, [clone_id], 'paid')
                except Exception as e:
                    _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

        if reopen:
            return duplicated_list
        return revert_list

    def refund_close(self, cr, uid, ids, context=None):
        """Create a copy of order  for refund order"""
        clone_list = []

        clone_list = self.revert_order(cr, uid, ids, close=True, reopen=False, context=context)

        abs = {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': clone_list[0],
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
        return abs

    def refund_close_open(self, cr, uid, ids, context=None):
        """Create a copy of order  for refund order"""
        clone_list = []

        clone_list = self.revert_order(cr, uid, ids, close=True, reopen=True, context=context)

        abs = {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': clone_list[0],
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
        return abs

    def refund(self, cr, uid, ids, context=None):
        """Create a copy of order  for refund order"""
        clone_list = []

        for order_id in ids:
            clone_id = self._create_refund_order(cr, uid, order_id, context=context)
            clone_list.append(clone_id)

        abs = {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': clone_list[0],
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
        return abs
