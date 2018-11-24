# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
from openerp.tools import float_compare, float_round
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from openerp.exceptions import UserError

class stock_landed_cost(osv.osv):
    _inherit = 'stock.landed.cost'
    _description = 'Stock Landed Cost'

    def get_valuation_lines(self, cr, uid, ids, picking_ids=None, context=None):
        picking_obj = self.pool.get('stock.picking')
        lines = []
        if not picking_ids:
            return lines

        for picking in picking_obj.browse(cr, uid, picking_ids):
            for move in picking.move_lines:
                #it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                #if move.product_id.valuation != 'real_time' or move.product_id.cost_method != 'real':
                if move.product_id.valuation != 'manual_periodic' and move.product_id.cost_method != 'real':
                    continue
                total_cost = 0.0
                weight = move.product_id and move.product_id.weight * move.product_qty
                volume = move.product_id and move.product_id.volume * move.product_qty
                for quant in move.quant_ids:
                    total_cost += quant.cost * quant.qty
                vals = dict(product_id=move.product_id.id, move_id=move.id, quantity=move.product_qty, former_cost=total_cost, weight=weight, volume=volume)
                lines.append(vals)
        if not lines:
            raise UserError(_('The selected picking does not contain any move that would be impacted by landed costs. Landed costs are only possible for products configured in real time valuation with real price costing method. Please make sure it is the case, or you selected the correct picking'))
        return lines



    def button_validate(self, cr, uid, ids, context=None):
        quant_obj = self.pool.get('stock.quant')

        for cost in self.browse(cr, uid, ids, context=context):
            if cost.state != 'draft':
                raise UserError(_('Only draft landed costs can be validated'))
            if not cost.valuation_adjustment_lines or not self._check_sum(cr, uid, cost, context=context):
                raise UserError(_('You cannot validate a landed cost which has no valid valuation adjustments lines. Did you click on Compute?'))

            # No es necesario generar asiento contable porque en el primer nivel
            # se controla que los productos tienen que estar confirgurados de forma Periodica
            #if self.pool['res.users'].has_group(cr, uid, 'stock_account.group_inventory_valuation'):
            #    move_id = self._create_account_move(cr, uid, cost, context=context)

            for line in cost.valuation_adjustment_lines:
                if not line.move_id:
                    continue
                per_unit = line.final_cost / line.quantity
                diff = per_unit - line.former_cost_per_unit

                # If the precision required for the variable diff is larger than the accounting
                # precision, inconsistencies between the stock valuation and the accounting entries
                # may arise.
                # For example, a landed cost of 15 divided in 13 units. If the products leave the
                # stock one unit at a time, the amount related to the landed cost will correspond to
                # round(15/13, 2)*13 = 14.95. To avoid this case, we split the quant in 12 + 1, then
                # record the difference on the new quant.
                # We need to make sure to able to extract at least one unit of the product. There is
                # an arbitrary minimum quantity set to 2.0 from which we consider we can extract a
                # unit and adapt the cost.
                curr_rounding = line.move_id.company_id.currency_id.rounding
                diff_rounded = float_round(diff, precision_rounding=curr_rounding)
                diff_correct = diff_rounded
                quants = line.move_id.quant_ids.sorted(key=lambda r: r.qty, reverse=True)
                quant_correct = False
                if quants\
                        and float_compare(quants[0].product_id.uom_id.rounding, 1.0, precision_digits=1) == 0\
                        and float_compare(line.quantity * diff, line.quantity * diff_rounded, precision_rounding=curr_rounding) != 0\
                        and float_compare(quants[0].qty, 2.0, precision_rounding=quants[0].product_id.uom_id.rounding) >= 0:
                    # Search for existing quant of quantity = 1.0 to avoid creating a new one
                    quant_correct = quants.filtered(lambda r: float_compare(r.qty, 1.0, precision_rounding=quants[0].product_id.uom_id.rounding) == 0)
                    if not quant_correct:
                        quant_correct = quant_obj._quant_split(cr, uid, quants[0], quants[0].qty - 1.0, context=context)
                    else:
                        quant_correct = quant_correct[0]
                        quants = quants - quant_correct
                    diff_correct += (line.quantity * diff) - (line.quantity * diff_rounded)
                    diff = diff_rounded

                quant_dict = {}
                for quant in quants:
                    quant_dict[quant.id] = quant.cost + diff
                if quant_correct:
                    quant_dict[quant_correct.id] = quant_correct.cost + diff_correct
                for key, value in quant_dict.items():
                    quant_obj.write(cr, SUPERUSER_ID, key, {'cost': value}, context=context)
                qty_out = 0
                for quant in line.move_id.quant_ids:
                    if quant.location_id.usage != 'internal':
                        qty_out += quant.qty
                # No es necesario generar asiento contable porque en el primer nivel
                # se controla que los productos tienen que estar confirgurados de forma Periodica
                #if self.pool['res.users'].has_group(cr, uid, 'stock_account.group_inventory_valuation'):
                #    self._create_accounting_entries(cr, uid, line, move_id, qty_out, context=context)
            # No es necesario generar asiento contable porque en el primer nivel
            # se controla que los productos tienen que estar confirgurados de forma Periodica
            #if self.pool['res.users'].has_group(cr, uid, 'stock_account.group_inventory_valuation'):
            #    self.write(cr, uid, cost.id, {'state': 'done', 'account_move_id': move_id}, context=context)
            #    self.pool.get('account.move').post(cr, uid, [move_id], context=context)
            #else:
            self.write(cr, uid, cost.id, {'state': 'done'}, context=context)
        return True