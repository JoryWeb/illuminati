# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
from openerp.tools import float_compare, float_round
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api, models
from openerp.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# Quants
#----------------------------------------------------------


class account_move(osv.osv):
    _inherit = 'account.move'

    _columns = {
        'src_quant': fields.char(string='Source Quants', size=128)
    }


class stock_quant(osv.osv):
    _inherit = "stock.quant"

    def _create_account_move_line(self, cr, uid, quants, move, credit_account_id, debit_account_id, journal_id, context=None):
        #group quants by cost
        quant_cost_qty = {}
        quant_src = ""
        for quant in quants:
            if quant_src != "":
                quant_src += ","
            quant_src += str(quant.id)
            if quant_cost_qty.get(quant.cost):
                quant_cost_qty[quant.cost] += quant.qty
            else:
                quant_cost_qty[quant.cost] = quant.qty
        move_obj = self.pool.get('account.move')
        for cost, qty in quant_cost_qty.items():
            move_lines = self._prepare_account_move_line(cr, uid, move, qty, cost, credit_account_id, debit_account_id, context=context)
            if move_lines:
                date = context.get('force_period_date', fields.date.context_today(self, cr, uid, context=context))
                new_move = move_obj.create(cr, uid, {'journal_id': journal_id,
                                          'line_ids': move_lines,
                                          'date': date,
                                          'ref': move.picking_id.name,
                                          'src': 'stock.move,' + str(move.id),
                                          'src_quant': quant_src}, context=context) #Override and linking to move, because wuants are not fix
                move_obj.post(cr, uid, [new_move], context=context)