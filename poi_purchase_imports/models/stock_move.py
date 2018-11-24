# © 2013 Joaquín Gutierrez
# © 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from itertools import groupby
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from operator import itemgetter

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    landed_value = fields.Float(copy=False)

    def name_get(self):
        ret_list = []
        for move in self:
            if move.lot_id:
                name = move.lot_id.name
            else:
                name = move.product_id.name
            ret_list.append((move.id, name))
        return ret_list

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """ search full lot_name """
        if args is None:
            args = []
        recs = self.search([('lot_name', operator, name)] + args, limit=limit)
        return recs.name_get()

# class StockQuant(models.Model):
#     _inherit = 'stock.quant'
#     def _get_quant_name(self):
#         """ Actualizacion del nombre para seleccionar el serie y ubicación
#         """
#         res = {}
#         for q in self:
#             q.name = q.product_id.code or ''
#             if q.lot_id:
#                 q.name = q.lot_id.name
#             q.name += ': ' + str(q.qty) + q.product_id.uom_id.name + ' ' + q.location_id.name
#
#     # Necesitamos asignar los quants/Chasis a una carpeta de importaciones
#     # para que estos solo sean visibles en la carpeta de importaciones creada
#     imports = fields.Many2one("poi.purchase.imports", "Carpeta de Importaciones")
#     name = fields.Char(compute='_get_quant_name')
#
#     def _get_accounting_data_for_valuation(self, cr, uid, move, context=None):
#         """ Aplicable al modulo de importaciones separar las cuentas contables en inventarios por cuenta de importaciones """
#         journal_id, acc_src, acc_dest, acc_valuation = super(StockQuant, self)._get_accounting_data_for_valuation(cr, uid, move, context)
#         accounts_data = move.product_id.product_tmpl_id.get_product_accounts()
#         if move.location_id.valuation_out_account_id:
#             acc_src = move.location_id.valuation_out_account_id.id
#         elif move.purchase_line_id.order_id.tipo_fac == '3':
#             acc_src = accounts_data['import_stock_input'].id
#
#         return journal_id, acc_src, acc_dest, acc_valuation

class StockMove(models.Model):
    _inherit = 'stock.move'

    ## Fix error al crear back order
    # se debe controlar que si proviene de un parcial no cree mas lineas para los lotes
    def _action_assign(self):
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `product_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """
        assigned_moves = self.env['stock.move']
        partially_available_moves = self.env['stock.move']
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            # El objetivo esta en que se debe discriminar los productos por manejo de serie unica de los que son  por lotes y normales
            if move.product_id.tracking == 'serial':
                if (move.location_id.should_bypass_reservation() or move.product_id.type == 'consu') and not move.picking_id.backorder_id:
                #if (move.location_id.should_bypass_reservation() or move.product_id.type == 'consu'):
                    # create the move line(s) but do not impact quants
                    if move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                        for i in range(0, int(move.product_qty - move.reserved_availability)):
                            self.env['stock.move.line'].create(move._prepare_move_line_vals(quantity=1))
                    else:
                        to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                                ml.location_id == move.location_id and
                                                                ml.location_dest_id == move.location_dest_id and
                                                                ml.picking_id == move.picking_id and
                                                                not ml.lot_id and
                                                                not ml.package_id and
                                                                not ml.owner_id)
                        if to_update:
                            to_update[0].product_uom_qty += move.product_qty - move.reserved_availability
                        else:
                            self.env['stock.move.line'].create(move._prepare_move_line_vals(quantity=move.product_qty - move.reserved_availability))
                    assigned_moves |= move
                elif move.picking_id.backorder_id and not move.move_orig_ids:
                    for line in move.move_line_ids:
                        line.product_uom_qty = 1
                    assigned_moves |= move

                else:
                    if not move.move_orig_ids:
                        if move.procure_method == 'make_to_order':
                            continue
                        # If we don't need any quantity, consider the move assigned.
                        need = move.product_qty - move.reserved_availability
                        if float_is_zero(need, precision_rounding=move.product_id.uom_id.rounding):
                            assigned_moves |= move
                            continue
                        # Reserve new quants and create move lines accordingly.
                        available_quantity = self.env['stock.quant']._get_available_quantity(move.product_id,
                                                                                             move.location_id)
                        if available_quantity <= 0:
                            continue
                        taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id,
                                                                        strict=False)
                        if float_is_zero(taken_quantity, precision_rounding=move.product_id.uom_id.rounding):
                            continue
                        if need == taken_quantity:
                            assigned_moves |= move
                        else:
                            partially_available_moves |= move
                    else:
                        # Check what our parents brought and what our siblings took in order to
                        # determine what we can distribute.
                        # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                        # the reserved quantity on the quants, convert it here in
                        # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                        move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
                        keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']

                        def _keys_in_sorted(ml):
                            return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

                        grouped_move_lines_in = {}
                        for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted),
                                            key=itemgetter(*keys_in_groupby)):
                            qty_done = 0
                            for ml in g:
                                qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                            grouped_move_lines_in[k] = qty_done
                        move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move) \
                            .filtered(lambda m: m.state in ['done']) \
                            .mapped('move_line_ids')
                        # As we defer the write on the stock.move's state at the end of the loop, there
                        # could be moves to consider in what our siblings already took.
                        moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
                        moves_out_siblings_to_consider = moves_out_siblings & (
                                    assigned_moves + partially_available_moves)
                        reserved_moves_out_siblings = moves_out_siblings.filtered(
                            lambda m: m.state in ['partially_available', 'assigned'])
                        move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped(
                            'move_line_ids')
                        keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']

                        def _keys_out_sorted(ml):
                            return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

                        grouped_move_lines_out = {}
                        for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted),
                                            key=itemgetter(*keys_out_groupby)):
                            qty_done = 0
                            for ml in g:
                                qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                            grouped_move_lines_out[k] = qty_done
                        for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted),
                                            key=itemgetter(*keys_out_groupby)):
                            grouped_move_lines_out[k] = sum(
                                self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
                        available_move_lines = {key: grouped_move_lines_in[key] - grouped_move_lines_out.get(key, 0) for
                                                key in grouped_move_lines_in.keys()}
                        # pop key if the quantity available amount to 0
                        available_move_lines = dict((k, v) for k, v in available_move_lines.items() if v)

                        if not available_move_lines:
                            continue
                        for move_line in move.move_line_ids.filtered(lambda m: m.product_qty):
                            if available_move_lines.get((move_line.location_id, move_line.lot_id,
                                                         move_line.result_package_id, move_line.owner_id)):
                                available_move_lines[(
                                move_line.location_id, move_line.lot_id, move_line.result_package_id,
                                move_line.owner_id)] -= move_line.product_qty
                        for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                            need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
                            # `quantity` is what is brought by chained done move lines. We double check
                            # here this quantity is available on the quants themselves. If not, this
                            # could be the result of an inventory adjustment that removed totally of
                            # partially `quantity`. When this happens, we chose to reserve the maximum
                            # still available. This situation could not happen on MTS move, because in
                            # this case `quantity` is directly the quantity on the quants themselves.
                            available_quantity = self.env['stock.quant']._get_available_quantity(
                                move.product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                                strict=True)
                            if float_is_zero(available_quantity, precision_rounding=move.product_id.uom_id.rounding):
                                continue
                            taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity),
                                                                            location_id, lot_id, package_id, owner_id)

                            if float_is_zero(taken_quantity, precision_rounding=move.product_id.uom_id.rounding):
                                continue
                            if need - taken_quantity == 0.0:
                                assigned_moves |= move
                                break
                            partially_available_moves |= move
            elif move.location_id.should_bypass_reservation()\
                    or move.product_id.type == 'consu':
                # create the move line(s) but do not impact quants
                if move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    for i in range(0, int(move.product_qty - move.reserved_availability)):
                        self.env['stock.move.line'].create(move._prepare_move_line_vals(quantity=1))
                else:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                            ml.location_id == move.location_id and
                                                            ml.location_dest_id == move.location_dest_id and
                                                            ml.picking_id == move.picking_id and
                                                            not ml.lot_id and
                                                            not ml.package_id and
                                                            not ml.owner_id)
                    if to_update:
                        to_update[0].product_uom_qty += move.product_qty - move.reserved_availability
                    else:
                        self.env['stock.move.line'].create(move._prepare_move_line_vals(quantity=move.product_qty - move.reserved_availability))
                assigned_moves |= move
            else:
                if not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    # If we don't need any quantity, consider the move assigned.
                    need = move.product_qty - move.reserved_availability
                    if float_is_zero(need, precision_rounding=move.product_id.uom_id.rounding):
                        assigned_moves |= move
                        continue
                    # Reserve new quants and create move lines accordingly.
                    available_quantity = self.env['stock.quant']._get_available_quantity(move.product_id, move.location_id)
                    if available_quantity <= 0:
                        continue
                    taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id, strict=False)
                    if float_is_zero(taken_quantity, precision_rounding=move.product_id.uom_id.rounding):
                        continue
                    if need == taken_quantity:
                        assigned_moves |= move
                    else:
                        partially_available_moves |= move
                else:
                    # Check what our parents brought and what our siblings took in order to
                    # determine what we can distribute.
                    # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                    # the reserved quantity on the quants, convert it here in
                    # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                    move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
                    keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']

                    def _keys_in_sorted(ml):
                        return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

                    grouped_move_lines_in = {}
                    for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted), key=itemgetter(*keys_in_groupby)):
                        qty_done = 0
                        for ml in g:
                            qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_in[k] = qty_done
                    move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move)\
                        .filtered(lambda m: m.state in ['done'])\
                        .mapped('move_line_ids')
                    # As we defer the write on the stock.move's state at the end of the loop, there
                    # could be moves to consider in what our siblings already took.
                    moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
                    moves_out_siblings_to_consider = moves_out_siblings & (assigned_moves + partially_available_moves)
                    reserved_moves_out_siblings = moves_out_siblings.filtered(lambda m: m.state in ['partially_available', 'assigned'])
                    move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped('move_line_ids')
                    keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']

                    def _keys_out_sorted(ml):
                        return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

                    grouped_move_lines_out = {}
                    for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                        qty_done = 0
                        for ml in g:
                            qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_out[k] = qty_done
                    for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                        grouped_move_lines_out[k] = sum(self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
                    available_move_lines = {key: grouped_move_lines_in[key] - grouped_move_lines_out.get(key, 0) for key in grouped_move_lines_in.keys()}
                    # pop key if the quantity available amount to 0
                    available_move_lines = dict((k, v) for k, v in available_move_lines.items() if v)

                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(lambda m: m.product_qty):
                        if available_move_lines.get((move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)):
                            available_move_lines[(move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)] -= move_line.product_qty
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
                        # `quantity` is what is brought by chained done move lines. We double check
                        # here this quantity is available on the quants themselves. If not, this
                        # could be the result of an inventory adjustment that removed totally of
                        # partially `quantity`. When this happens, we chose to reserve the maximum
                        # still available. This situation could not happen on MTS move, because in
                        # this case `quantity` is directly the quantity on the quants themselves.
                        available_quantity = self.env['stock.quant']._get_available_quantity(
                            move.product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
                        if float_is_zero(available_quantity, precision_rounding=move.product_id.uom_id.rounding):
                            continue
                        taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity), location_id, lot_id, package_id, owner_id)

                        if float_is_zero(taken_quantity, precision_rounding=move.product_id.uom_id.rounding):
                            continue
                        if need - taken_quantity == 0.0:
                            assigned_moves |= move
                            break
                        partially_available_moves |= move
        partially_available_moves.write({'state': 'partially_available'})
        assigned_moves.write({'state': 'assigned'})
        self.mapped('picking_id')._check_entire_pack()
    #
    # @api.multi
    # def action_done(self):
    #     result = super(StockMove, self).action_done()
    #
    #     for move in self:
    #         if move.imports and move.location_dest_id.usage == 'internal':
    #             import_line = self.env['poi.purchase.imports.line'].search([('move_id', '=', move.id)])
    #             if import_line:
    #                 if move.imports.state != 'done':
    #                     raise UserError(_('Debe cerrar la carpeta de importaciones para realizar este ingreso'))
    #
    #                 if move.imports.expense_lines:
    #                     move_id = move.imports._create_account_move()
    #                     move.imports._create_accounting_entries_stock(move, move_id, 0)
    #                     move_id.post()
    #                 move.quant_ids._price_update(move.standard_price_new)
    #                 move.imports._product_price_update(move, move.standard_price_new, 0)
    #                 # Actualizar la linea actual con los costos correctos
    #
    #                 for imp_line in import_line:
    #                     imp_line.expense_amount = move.product_qty * move.cost_ratio
    #                     imp_line.cost_ratio = move.cost_ratio
    #                     imp_line.product_price_update = move.product_id.standard_price
    #                     imp_line.date_update_price = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #                 # nSolo aplicaria en caso de promedio "Real"
    #                 move.product_price_update_after_done()
    #     return result




