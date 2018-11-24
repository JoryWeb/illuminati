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

import re
import time
import psycopg2
import logging
import pytz
from datetime import datetime, timedelta

from odoo import api, fields, models, tools, _
from odoo import SUPERUSER_ID
from odoo.tools import float_is_zero
from odoo.exceptions import UserError

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class PosConfigGroup(models.Model):
    _name = 'pos.config.group'

    name = fields.Char("Group Name")
    pos_config_ids = fields.One2many("pos.config","pos_group_id","POS Interfaces")


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_presale = fields.Boolean('Presale Interface')
    iface_presale_cash_register = fields.Boolean('Cash register for Presale interface')
    pos_group_id = fields.Many2one("pos.config.group", "Group")

class PosOrder(models.Model):
    _inherit = "pos.order"

    pos_group_id = fields.Many2one("pos.config.group", "Group")
    timestamp = fields.Text('Timestamp')
    pending_picking=  fields.Boolean('Pending Picking',
                                      help='This field is going to be true until picking is finally created')
    ui_order = fields.Boolean('UI Order', help='This field is going to be enabled when an order was created automatically')

    #@api.multi
    #def action_pos_order_paid(self):
    #    if not self.test_paid():
    #        pass
    #    else:
    #        return super(PosOrder).action_pos_order_paid()

    @api.model
    def _process_order_presale(self, pos_order):
        prec_acc = self.env['decimal.precision'].precision_get('Account')
        pos_session = self.env['pos.session'].browse(pos_order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            pos_order['pos_session_id'] = self._get_valid_session(pos_order).id
        if pos_order['order_id']:
            order = self.browse(pos_order['order_id'])
            if order.state == 'draft':
                for l in order.lines:
                    l.unlink() # We destroy all lines just in case
                order.write(self._order_fields(pos_order))
            else:
                return order
        else:
            order = self.create(self._order_fields(pos_order))
        journal_ids = set()
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
                order.add_payment(self._payment_fields(payments[2]))
            journal_ids.add(payments[2]['journal_id'])

        if pos_session.sequence_number <= pos_order['sequence_number']:
            pos_session.write({'sequence_number': pos_order['sequence_number'] + 1})
            pos_session.refresh()

        if not float_is_zero(pos_order['amount_return'], prec_acc):
            cash_journal_id = pos_session.cash_journal_id.id
            if not cash_journal_id:
                # Select for change one of the cash journals used in this
                # payment
                cash_journal = self.env['account.journal'].search([
                    ('type', '=', 'cash'),
                    ('id', 'in', list(journal_ids)),
                ], limit=1)
                if not cash_journal:
                    # If none, select for change one of the cash journals of the POS
                    # This is used for example when a customer pays by credit card
                    # an amount higher than total amount of the order and gets cash back
                    cash_journal = [statement.journal_id for statement in pos_session.statement_ids if
                                    statement.journal_id.type == 'cash']
                    if not cash_journal:
                        raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
                cash_journal_id = cash_journal[0].id
            order.add_payment({
                'amount': -pos_order['amount_return'],
                'payment_date': fields.Datetime.now(),
                'payment_name': _('return'),
                'journal': cash_journal_id,
            })
        return order

    @api.model
    def create_from_ui(self, orders):

        order_ids = []

        presale_orders = [o for o in orders if o['data']['order_id']]
        for po in presale_orders:
            orders.remove(po)

        for tmp_order in presale_orders:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
                self._match_payment_to_invoice(order)
            pos_order = self._process_order_presale(order)
            order_ids.append(pos_order.id)

            try:
                pos_order.action_pos_order_paid()
            except psycopg2.OperationalError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            if to_invoice:
                pos_order.action_pos_order_invoice()
                pos_order.invoice_id.sudo().action_invoice_open()
                pos_order.account_move = pos_order.invoice_id.move_id

        res=super(PosOrder, self).create_from_ui(orders)
        res = res + order_ids
        return res

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['pos_group_id'] = ui_order.get('pos_group_id', False)
        return res

    @api.model
    def create(self, values):
        values['timestamp'] = str(time.time())
        return super(PosOrder, self).create(values)

    def avoid_write_fields(self):
        res = ['timestamp', 'picking_id', 'state']
        return res

    @api.multi
    def write(self, values):
        if not self.env.context:
            context = {}
        else:
            context = self.env.context
        flag = False
        if not context.get('no_synch'):
            fields_to_avoid = self.avoid_write_fields()
            for key, value in values.iteritems():
                if key not in fields_to_avoid:
                    flag = True
                    break
        if flag:
            values['timestamp'] = str(time.time())
        return super(PosOrder, self).write(values)

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    timestamp = fields.Text('Timestamp')
    unique_name = fields.Char('Orderline Unique Name', size=64, readonly=True)

    @api.model
    def create(self, values):
        if not self.env.context:
            context = {}
        else:
            context = self.env.context
        if not context.get('no_synch'):
            if values.get('order_id'):
                self.env['pos.order'].browse(int(values.get('order_id'))).write({'timestamp': str(time.time())})
        return super(PosOrderLine, self).create(values)

    @api.multi
    def write(self, values):
        if not self.env.context:
            context = {}
        else:
            context = self.env.context
        if not context.get('no_synch'):
            for orderline in self:
                orderline.order_id.write({'timestamp': str(time.time())})
        return super(PosOrderLine, self).write(values)