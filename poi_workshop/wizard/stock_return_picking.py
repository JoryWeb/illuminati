# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class StockPickingReturn(models.TransientModel):
    _inherit = 'stock.return.picking'

    # def default_get(self, cr, uid, fields, context=None):
    #     """
    #      To get default values for the object.
    #      @param self: The object pointer.
    #      @param cr: A database cursor
    #      @param uid: ID of the user currently logged in
    #      @param fields: List of fields for which we want default values
    #      @param context: A standard dictionary
    #      @return: A dictionary with default values for all field in ``fields``
    #     """
    #     result1 = []
    #     if context is None:
    #         context = {}
    #     if context and context.get('active_ids', False):
    #         if len(context.get('active_ids')) > 1:
    #             raise UserError(_("You may only return one picking at a time!"))
    #     res = super(stock_return_picking, self).default_get(cr, uid, fields, context=context)
    #     record_id = context and context.get('active_id', False) or False
    #     uom_obj = self.pool.get('product.uom')
    #     pick_obj = self.pool.get('stock.picking')
    #     pick = pick_obj.browse(cr, uid, record_id, context=context)
    #     quant_obj = self.pool.get("stock.quant")
    #     chained_move_exist = False
    #     if pick:
    #         if pick.state != 'done':
    #             raise UserError(_("You may only return pickings that are Done!"))
    #
    #         for move in pick.move_lines:
    #             if move.scrapped:
    #                 continue
    #             if move.move_dest_id:
    #                 chained_move_exist = True
    #             #Sum the quants in that location that can be returned (they should have been moved by the moves that were included in the returned picking)
    #             qty = 0
    #             quant_search = quant_obj.search(cr, uid, [('history_ids', 'in', move.id), ('qty', '>', 0.0), ('location_id', 'child_of', move.location_dest_id.id)], context=context)
    #             for quant in quant_obj.browse(cr, uid, quant_search, context=context):
    #                 if not quant.reservation_id or quant.reservation_id.origin_returned_move_id.id != move.id:
    #                     qty += quant.qty
    #             qty = uom_obj._compute_qty(cr, uid, move.product_id.uom_id.id, qty, move.product_uom.id)
    #             # Aplicable solo para talleres
    #             if move.parts_line:
    #                 if move.parts_line.return_parts:
    #                     result1.append((0, 0, {'product_id': move.product_id.id, 'quantity': qty, 'move_id': move.id}))
    #                 else:
    #                     None
    #             else:
    #                 result1.append((0, 0, {'product_id': move.product_id.id, 'quantity': qty, 'move_id': move.id}))
    #
    #         if len(result1) == 0:
    #             raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)!"))
    #         if 'product_return_moves' in fields:
    #             res.update({'product_return_moves': result1})
    #         if 'move_dest_exists' in fields:
    #             res.update({'move_dest_exists': chained_move_exist})
    #         if 'parent_location_id' in fields and pick.location_id.usage == 'internal':
    #             res.update({'parent_location_id':pick.picking_type_id.warehouse_id and pick.picking_type_id.warehouse_id.view_location_id.id or pick.location_id.location_id.id})
    #         if 'original_location_id' in fields:
    #             res.update({'original_location_id': pick.location_id.id})
    #         if 'location_id' in fields:
    #             res.update({'location_id': pick.location_id.id})
    #     return res
