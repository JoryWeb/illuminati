# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_round
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from openerp.exceptions import UserError


class stock_landed_cost(osv.osv):
    _inherit = 'stock.landed.cost'

    def _create_account_move(self, cr, uid, cost, context=None):
        vals = {
            'journal_id': cost.account_journal_id.id,
            'date': cost.date,
            'ref': cost.name,
            'src': 'stock.landed.cost,' + str(cost.id),
        }
        return self.pool.get('account.move').create(cr, uid, vals, context=context)