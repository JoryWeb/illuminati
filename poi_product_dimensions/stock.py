##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Coded by: Grover Menacho
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

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api, models
from openerp.tools.float_utils import float_compare, float_round
from openerp.exceptions import UserError
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class StockPicking(models.Model):
    _inherit = 'stock.picking'


    @api.multi
    def action_assign(self):
        """ Realizar la asignación
        se cran los pack.operation donde podemos asignar los
        valores
        en este punto creamos los lotes par asignarlos a los pack.operation
        buscando por producto
        """
        ret = super(StockPicking, self).action_assign()
        for picking in self:
            #Controlar para cuando devoluciones de materiales o anulaciones
            if picking.location_id.usage == 'customer':
                return ret
        pack_lot = self.env['stock.pack.operation.lot']
        production_lot = self.env['stock.production.lot']

        for picking in self:
            if picking.pack_operation_product_ids:
                # for pack in picking.pack_operation_product_ids:
                #     if pack.pack_lot_ids:
                #         pack.pack_lot_ids.unlink()
                #     else:
                #         continue

                for move in picking.move_lines:
                    # if move.product_id.tracking == 'none':
                    #     continue
                    pack_id = False

                    for mv in move.linked_move_operation_ids:
                        pack_id = mv.operation_id.id

                    if not pack_id:
                        pack = self.env['stock.pack.operation'].search([('product_id', '=', move.product_id.id), ('picking_id', '=', move.picking_id.id)])
                        if pack:
                            pack_id = pack[0].id
                    # con procument_id indica que es una venta
                    if move.procurement_id and pack_id:
                        None
                        # lot_ids = production_lot.search([('product_id', '=', move.product_id.id), (
                        # 'dimension_id', '=', move.procurement_id.sale_line_id.product_dimension.id)])
                        #
                        # if not lot_ids:
                        #     lot_id = production_lot.create({
                        #         'name': move.procurement_id.sale_line_id.name,
                        #         'product_id': move.product_id.id,
                        #         'dimencion_id': move.procurement_id.sale_line_id.product_dimension.id,
                        #     })
                        #     pack_lot_id = pack_lot.create({
                        #         'lot_id': lot_id.id,
                        #         'operation_id': pack_id,
                        #         'qty': 0.0,
                        #         'qty_todo': move.product_qty,
                        #     })
                        # else:
                        #     quant_search = self.env['stock.quant'].search(
                        #         [('product_id', '=', move.product_id.id), ('lot_id', '=', lot_ids[0].id),
                        #          ('reservation_id', '=', False), ('location_id.usage', '=', 'internal'),
                        #          ('location_id', '=', move.location_id.id)])
                        #
                        #     qty_total = sum([(q.qty) for q in quant_search])
                        #     if qty_total > move.product_qty:
                        #         pack_lot_id = pack_lot.create({
                        #             'lot_id': lot_ids[0].id,
                        #             'operation_id': pack_id,
                        #             'qty': 0.0,
                        #             'qty_todo': move.product_qty,
                        #         })
                        #     elif qty_total > 0:
                        #         #move.do_unreserve()
                        #         pack_lot_id = pack_lot.create({
                        #             'lot_id': lot_ids[0].id,
                        #             'operation_id': pack_id,
                        #             'qty': 0.0,
                        #             'qty_todo': qty_total,
                        #         })

                    elif pack_id:
                        if picking.check_recu:
                            # Si es recuperado se tiene que crear todas las lineas a una unidad para usar en el proceso de recuperados
                            for x in range(int(move.product_uom_qty)):
                                pack_lot.create({
                                    'lot_id': move.lot_creation_pack.id,
                                    'operation_id': pack_id,
                                    'qty': 1,
                                    'qty_todo': 1,
                                    'secuencia': x + 1,
                                    'causa': move.causa,
                                })
                        else:
                            pack_lot.create({
                                'lot_id': move.lot_creation_pack.id,
                                'operation_id': pack_id,
                                'qty': 0.0,
                                'qty_todo': move.product_qty,
                            })
                #
                # for pack_dos in picking.pack_operation_product_ids:
                #     suma = 0
                #     for pack_lot in pack_dos.pack_lot_ids:
                #         suma = suma + pack_lot.qty_todo
                #
                #     pack_dos.product_qty = suma
        return ret

    @api.multi
    def force_assign(self):
        """ Realizar la asignación
        se cran los pack.operation donde podemos asignar los
        valores
        en este punto creamos los lotes par asignarlos a los pack.operation
        buscando por producto
        """
        ret = super(StockPicking, self).force_assign()
        #if self.location_dest_id.usage != 'transit':
        pack_lot = self.env['stock.pack.operation.lot']
        pack_product = self.env['stock.pack.operation']
        production_lot = self.env['stock.production.lot']
        for picking in self:
            for pack in picking.pack_operation_product_ids:
                if pack.pack_lot_ids:
                    pack.pack_lot_ids.unlink()
                else:
                    continue
            for move in picking.move_lines:
                if move.product_id.tracking == 'none':
                    continue
                pack_id = False
                for mv in move.linked_move_operation_ids:
                    pack_id = mv.operation_id.id

                if not pack_id:
                    pack = self.env['stock.pack.operation'].search([('product_id', '=', move.product_id.id), ('picking_id', '=', move.picking_id.id)])
                    pack_id = pack[0].id
                #con procument_id indica que es una venta
                if move.procurement_id and pack_id:
                    lot_ids = production_lot.search([('product_id', '=', move.product_id.id), ('dimension_id', '=', move.procurement_id.sale_line_id.product_dimension.id)])

                    if not lot_ids:
                        lot_id = production_lot.create({
                            'name': move.procurement_id.sale_line_id.name,
                            'product_id': move.product_id.id,
                            'dimension_id': move.procurement_id.sale_line_id.product_dimension.id,
                        })
                        pack_lot.create({
                            'lot_id': lot_id.id,
                            'operation_id': pack_id,
                            'qty': 0.0,
                            'qty_todo': move.product_qty,
                        })
                    else:
                        pack_lot.create({
                            'lot_id': lot_ids[0].id,
                            'operation_id': pack_id,
                            'qty': 0.0,
                            'qty_todo': move.product_qty,
                        })

                elif pack_id:
                    if picking.check_recu:
                        # Si es recuperado se tiene que crear todas las lineas a una unidad para usar en el proceso de recuperados
                        for x in range(int(move.product_uom_qty)):
                            pack_lot_id = pack_lot.create({
                                'lot_id': move.lot_creation_pack.id,
                                'operation_id': pack_id,
                                'qty': 0,
                                #'qty_todo': 1,
                                'secuencia': x + 1,
                                'causa': move.causa,
                            })
                            pack_lot_id.do_plus()

                    else:
                        pack_lot.create({
                            'lot_id': move.lot_creation_pack.id,
                            'operation_id': pack_id,
                            'qty': 0.0,
                            'qty_todo': move.product_qty,
                        })
        return True


    def _get_dimension_lot_id(self, cr, uid, product_id, dimension_id, context=None):
        stock_lot_pool = self.pool.get('stock.production.lot')
        product_pool = self.pool.get('product.product')
        dimension_pool = self.pool.get('product.dimension')

        lot_ids = stock_lot_pool.search(cr, uid, [('product_id', '=', product_id), ('dimension_id', '=', dimension_id)])

        if lot_ids:
            return lot_ids[0]
        else:
            product_name = product_pool.browse(cr, uid, product_id).name_get()[0][1]
            dimension_name = dimension_pool.browse(cr, uid, dimension_id).name_get()[0][1]

            lot_name=product_name + " ["+dimension_name+"]"

            lot_id=stock_lot_pool.create(cr, uid, {'name': lot_name,
                                                   'product_id': product_id,
                                                   'dimension_id': dimension_id})
            return lot_id

class stock_production_lot(osv.osv):
    _inherit='stock.production.lot'

    _columns = {
        'dimension_id': fields.many2one('product.dimension','Dimension'),
    }

stock_production_lot()

class stock_move(osv.osv):
    _inherit = 'stock.move'

    def action_done(self, cr, uid, ids, context=None):
        """ Process completely the moves given as ids and if all moves are done, it will finish the picking.
        """
        context = context or {}
        picking_obj = self.pool.get("stock.picking")
        quant_obj = self.pool.get("stock.quant")
        uom_obj = self.pool.get("product.uom")
        todo = [move.id for move in self.browse(cr, uid, ids, context=context) if move.state == "draft"]
        if todo:
            ids = self.action_confirm(cr, uid, todo, context=context)
        pickings = set()
        procurement_ids = set()
        #Search operations that are linked to the moves
        operations = set()
        move_qty = {}
        for move in self.browse(cr, uid, ids, context=context):
            if move.picking_id:
                pickings.add(move.picking_id.id)
            move_qty[move.id] = move.product_qty
            for link in move.linked_move_operation_ids:
                operations.add(link.operation_id)

        #Sort operations according to entire packages first, then package + lot, package only, lot only
        operations = list(operations)
        operations.sort(key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (x.pack_lot_ids and -1 or 0))

        for ops in operations:
            if ops.picking_id:
                pickings.add(ops.picking_id.id)
            entire_pack=False
            if ops.product_id:
                #If a product is given, the result is always put immediately in the result package (if it is False, they are without package)
                quant_dest_package_id  = ops.result_package_id.id
            else:
                # When a pack is moved entirely, the quants should not be written anything for the destination package
                quant_dest_package_id = False
                entire_pack=True
            lot_qty = {}
            tot_qty = 0.0
            prod2lot_ids = {}
            for pack_lot in ops.pack_lot_ids:
                if not prod2lot_ids.get(pack_lot.lot_id.id):
                    qty = uom_obj._compute_qty(cr, uid, ops.product_uom_id.id, pack_lot.qty, ops.product_id.uom_id.id)
                    prod2lot_ids[pack_lot.lot_id.id] = [{'lot_id': pack_lot.lot_id.id, 'qty': qty}]
                else:
                    qty = uom_obj._compute_qty(cr, uid, ops.product_uom_id.id, pack_lot.qty, ops.product_id.uom_id.id)
                    prod2lot_ids[pack_lot.lot_id.id].append({'lot_id': pack_lot.lot_id.id, 'qty': qty})
            # Razon por la cual no se puede repetir los lotes en una operación de transferencia
            for prod in prod2lot_ids:
                qty = 0
                for prod_qty in prod2lot_ids.get(prod, []):
                    qty = qty + float(prod_qty['qty'])
                lot_qty[prod] = qty
                tot_qty += qty
            #for pack_lot in ops.pack_lot_ids:
            #    qty = uom_obj._compute_qty(cr, uid, ops.product_uom_id.id, pack_lot.qty, ops.product_id.uom_id.id)
            #    lot_qty[pack_lot.lot_id.id] = qty
            #    tot_qty += pack_lot.qty

            if ops.pack_lot_ids and ops.product_id and float_compare(tot_qty, ops.product_qty, precision_rounding=ops.product_uom_id.rounding) != 0.0:
                raise UserError(_('You have a difference between the quantity on the operation and the quantities specified for the lots. '))

            quants_taken = []
            false_quants = []
            lot_move_qty = {}
            #Group links by move first
            move_qty_ops = {}
            for record in ops.linked_move_operation_ids:
                move = record.move_id
                if not move_qty_ops.get(move):
                    move_qty_ops[move] = record.qty
                else:
                    move_qty_ops[move] += record.qty
            #Process every move only once for every pack operation
            for move in move_qty_ops:
                main_domain = [('qty', '>', 0)]
                self.check_tracking(cr, uid, move, ops, context=context)
                preferred_domain = [('reservation_id', '=', move.id)]
                fallback_domain = [('reservation_id', '=', False)]
                fallback_domain2 = ['&', ('reservation_id', '!=', move.id), ('reservation_id', '!=', False)]
                if not ops.pack_lot_ids:
                    preferred_domain_list = [preferred_domain] + [fallback_domain] + [fallback_domain2]
                    quants = quant_obj.quants_get_preferred_domain(cr, uid, move_qty_ops[move], move, ops=ops, domain=main_domain,
                                                        preferred_domain_list=preferred_domain_list, context=context)
                    quant_obj.quants_move(cr, uid, quants, move, ops.location_dest_id, location_from=ops.location_id,
                                          lot_id=False, owner_id=ops.owner_id.id, src_package_id=ops.package_id.id,
                                          dest_package_id=quant_dest_package_id, entire_pack=entire_pack, context=context)
                else:
                    # Check what you can do with reserved quants already
                    qty_on_link = move_qty_ops[move]
                    rounding = ops.product_id.uom_id.rounding
                    for reserved_quant in move.reserved_quant_ids:
                        if (reserved_quant.owner_id.id != ops.owner_id.id) or (reserved_quant.location_id.id != ops.location_id.id) or \
                                (reserved_quant.package_id.id != ops.package_id.id):
                            continue
                        if not reserved_quant.lot_id:
                            false_quants += [reserved_quant]
                        elif float_compare(lot_qty.get(reserved_quant.lot_id.id, 0), 0, precision_rounding=rounding) > 0:
                            if float_compare(lot_qty[reserved_quant.lot_id.id], reserved_quant.qty, precision_rounding=rounding) >= 0:
                                lot_qty[reserved_quant.lot_id.id] -= reserved_quant.qty
                                quants_taken += [(reserved_quant, reserved_quant.qty)]
                                qty_on_link -= reserved_quant.qty
                            else:
                                quants_taken += [(reserved_quant, lot_qty[reserved_quant.lot_id.id])]
                                lot_qty[reserved_quant.lot_id.id] = 0
                                qty_on_link -= lot_qty[reserved_quant.lot_id.id]
                    lot_move_qty[move.id] = qty_on_link

                if not move_qty.get(move.id):
                    raise UserError(_("The roundings of your Unit of Measures %s on the move vs. %s on the product don't allow to do these operations or you are not transferring the picking at once. ") % (move.product_uom.name, move.product_id.uom_id.name))
                move_qty[move.id] -= move_qty_ops[move]

            #Handle lots separately
            if ops.pack_lot_ids:
                self._move_quants_by_lot(cr, uid, ops, lot_qty, quants_taken, false_quants, lot_move_qty, quant_dest_package_id, context=context)

            # Handle pack in pack
            if not ops.product_id and ops.package_id and ops.result_package_id.id != ops.package_id.parent_id.id:
                self.pool.get('stock.quant.package').write(cr, SUPERUSER_ID, [ops.package_id.id], {'parent_id': ops.result_package_id.id}, context=context)
        #Check for remaining qtys and unreserve/check move_dest_id in
        move_dest_ids = set()
        for move in self.browse(cr, uid, ids, context=context):
            move_qty_cmp = float_compare(move_qty[move.id], 0, precision_rounding=move.product_id.uom_id.rounding)
            if move_qty_cmp > 0:  # (=In case no pack operations in picking)
                main_domain = [('qty', '>', 0)]
                preferred_domain = [('reservation_id', '=', move.id)]
                fallback_domain = [('reservation_id', '=', False)]
                fallback_domain2 = ['&', ('reservation_id', '!=', move.id), ('reservation_id', '!=', False)]
                preferred_domain_list = [preferred_domain] + [fallback_domain] + [fallback_domain2]
                self.check_tracking(cr, uid, move, False, context=context)
                qty = move_qty[move.id]
                quants = quant_obj.quants_get_preferred_domain(cr, uid, qty, move, domain=main_domain, preferred_domain_list=preferred_domain_list, context=context)
                quant_obj.quants_move(cr, uid, quants, move, move.location_dest_id, lot_id=move.restrict_lot_id.id, owner_id=move.restrict_partner_id.id, context=context)

            # If the move has a destination, add it to the list to reserve
            if move.move_dest_id and move.move_dest_id.state in ('waiting', 'confirmed'):
                move_dest_ids.add(move.move_dest_id.id)

            if move.procurement_id:
                procurement_ids.add(move.procurement_id.id)

            #unreserve the quants and make them available for other operations/moves
            quant_obj.quants_unreserve(cr, uid, move, context=context)
        # Check the packages have been placed in the correct locations
        self._check_package_from_moves(cr, uid, ids, context=context)
        #set the move as done
        self.write(cr, uid, ids, {'state': 'done', 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
        self.pool.get('procurement.order').check(cr, uid, list(procurement_ids), context=context)
        #assign destination moves
        if move_dest_ids:
            self.action_assign(cr, uid, list(move_dest_ids), context=context)
        #check picking state to set the date_done is needed
        done_picking = []
        for picking in picking_obj.browse(cr, uid, list(pickings), context=context):
            if picking.state == 'done' and not picking.date_done:
                done_picking.append(picking.id)
        if done_picking:
            picking_obj.write(cr, uid, done_picking, {'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
        return True

    def _move_quants_by_lot(self, cr, uid, ops, lot_qty, quants_taken, false_quants, lot_move_qty, quant_dest_package_id, context=None):
        """
        This function is used to process all the pack operation lots of a pack operation
        For every move:
            First, we check the quants with lot already reserved (and those are already subtracted from the lots to do)
            Then go through all the lots to process:
                Add reserved false lots lot by lot
                Check if there are not reserved quants or reserved elsewhere with that lot or without lot (with the traditional method)
        """
        quant_obj = self.pool['stock.quant']
        fallback_domain = [('reservation_id', '=', False)]
        fallback_domain2 = ['&', ('reservation_id', 'not in', [x for x in lot_move_qty.keys()]), ('reservation_id', '!=', False)]
        preferred_domain_list = [fallback_domain] + [fallback_domain2]
        rounding = ops.product_id.uom_id.rounding
        for move in lot_move_qty:
            move_quants_dict = {}
            move_rec = self.pool['stock.move'].browse(cr, uid, move, context=context)
            # Assign quants already reserved with lot to the correct
            for quant in quants_taken:
                if quant[0] <= move_rec.reserved_quant_ids:
                    move_quants_dict.setdefault(quant[0].lot_id.id, [])
                    move_quants_dict[quant[0].lot_id.id] += [quant]
            false_quants_move = [x for x in false_quants if x[0].reservation_id.id == move]
            for lot in lot_qty:
                move_quants_dict.setdefault(lot, [])
                redo_false_quants = False
                # Take remaining reserved quants with  no lot first
                # (This will be used mainly when incoming had no lot and you do outgoing with)
                while false_quants_move and float_compare(lot_qty[lot], 0, precision_rounding=rounding) > 0 and float_compare(lot_move_qty[move], 0, precision_rounding=rounding) > 0:
                    qty_min = min(lot_qty[lot], lot_move_qty[move])
                    if false_quants_move[0].qty > qty_min:
                        move_quants_dict[lot] += [(false_quants_move[0], qty_min)]
                        qty = qty_min
                        redo_false_quants = True
                    else:
                        qty = false_quants_move[0].qty
                        move_quants_dict[lot] += [(false_quants_move[0], qty)]
                        false_quants_move.pop(0)
                    lot_qty[lot] -= qty
                    lot_move_qty[move] -= qty

                # Search other with first matching lots and then without lots
                if move_rec.restrict_lot_id:
                    if float_compare(lot_move_qty[move], 0, precision_rounding=rounding) > 0 and float_compare(lot_qty[lot], 0, precision_rounding=rounding) > 0 and lot == move_rec.restrict_lot_id.id:
                        # Search if we can find quants with that lot
                        domain = [('qty', '>', 0)]
                        qty = min(lot_qty[lot], lot_move_qty[move])
                        quants = quant_obj.quants_get_preferred_domain(cr, uid, qty, move_rec, ops=ops, lot_id=lot, domain=domain,
                                                            preferred_domain_list=preferred_domain_list, context=context)
                        move_quants_dict[lot] += quants
                        lot_qty[lot] -= qty
                        lot_move_qty[move] -= qty
                else:
                    if float_compare(lot_move_qty[move], 0, precision_rounding=rounding) > 0 and float_compare(lot_qty[lot], 0, precision_rounding=rounding) > 0:
                        # Search if we can find quants with that lot
                        domain = [('qty', '>', 0)]
                        qty = min(lot_qty[lot], lot_move_qty[move])
                        quants = quant_obj.quants_get_preferred_domain(cr, uid, qty, move_rec, ops=ops, lot_id=lot, domain=domain,
                                                            preferred_domain_list=preferred_domain_list, context=context)
                        move_quants_dict[lot] += quants
                        lot_qty[lot] -= qty
                        lot_move_qty[move] -= qty

                #Move all the quants related to that lot/move
                if move_quants_dict[lot]:
                    quant_obj.quants_move(cr, uid, move_quants_dict[lot], move_rec, ops.location_dest_id, location_from=ops.location_id,
                                                    lot_id=lot, owner_id=ops.owner_id.id, src_package_id=ops.package_id.id,
                                                    dest_package_id=quant_dest_package_id, context=context)
                    if redo_false_quants:
                        move_rec = self.pool['stock.move'].browse(cr, uid, move, context=context)
                        false_quants_move = [x for x in move_rec.reserved_quant_ids if (not x.lot_id) and (x.owner_id.id == ops.owner_id.id) \
                                            and (x.location_id.id == ops.location_id.id) and (x.package_id.id == ops.package_id.id)]

    def action_assign(self, cr, uid, ids, no_prepare=False, context=None):
        """ Checks the product type and accordingly writes the state.
        """
        context = context or {}
        quant_obj = self.pool.get("stock.quant")
        uom_obj = self.pool['product.uom']
        to_assign_moves = set()
        main_domain = {}
        todo_moves = []
        operations = set()
        ancestors_list = {}
        self.do_unreserve(cr, uid, [x.id for x in self.browse(cr, uid, ids, context=context) if x.reserved_quant_ids and x.state in ['confirmed', 'waiting', 'assigned']], context=context)
        for move in self.browse(cr, uid, ids, context=context):
            if move.state not in ('confirmed', 'waiting', 'assigned'):
                continue
            if move.location_id.usage in ('supplier', 'inventory', 'production'):
                to_assign_moves.add(move.id)
                #in case the move is returned, we want to try to find quants before forcing the assignment
                if not move.origin_returned_move_id:
                    continue
            if move.product_id.type == 'consu':
                to_assign_moves.add(move.id)
                continue
            else:
                todo_moves.append(move)

                #we always search for yet unassigned quants
                main_domain[move.id] = [('reservation_id', '=', False), ('qty', '>', 0)]

                #if the move is preceeded, restrict the choice of quants in the ones moved previously in original move
                ancestors = self.find_move_ancestors(cr, uid, move, context=context)
                ancestors_list[move.id] = True if ancestors else False
                if move.state == 'waiting' and not ancestors:
                    #if the waiting move hasn't yet any ancestor (PO/MO not confirmed yet), don't find any quant available in stock
                    main_domain[move.id] += [('id', '=', False)]
                elif ancestors:
                    main_domain[move.id] += [('history_ids', 'in', ancestors)]

                #if the move is returned from another, restrict the choice of quants to the ones that follow the returned move
                if move.origin_returned_move_id:
                    main_domain[move.id] += [('history_ids', 'in', move.origin_returned_move_id.id)]
                for link in move.linked_move_operation_ids:
                    operations.add(link.operation_id)
        # Check all ops and sort them: we want to process first the packages, then operations with lot then the rest
        operations = list(operations)
        operations.sort(key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (x.pack_lot_ids and -1 or 0))
        for ops in operations:
            #first try to find quants based on specific domains given by linked operations for the case where we want to rereserve according to existing pack operations
            if not (ops.product_id and ops.pack_lot_ids):
                for record in ops.linked_move_operation_ids:
                    move = record.move_id
                    if move.id in main_domain:
                        qty = record.qty
                        domain = main_domain[move.id]
                        if qty:
                            quants = quant_obj.quants_get_preferred_domain(cr, uid, qty, move, ops=ops, domain=domain, preferred_domain_list=[], context=context)
                            quant_obj.quants_reserve(cr, uid, quants, move, record, context=context)
            else:
                lot_qty = {}
                rounding = ops.product_id.uom_id.rounding
                for pack_lot in ops.pack_lot_ids:
                    lot_qty[pack_lot.lot_id.id] = uom_obj._compute_qty(cr, uid, ops.product_uom_id.id, pack_lot.qty, ops.product_id.uom_id.id)
                for record in ops.linked_move_operation_ids.filtered(lambda x: x.move_id.id in main_domain):
                    move_qty = record.qty
                    move = record.move_id
                    domain = main_domain[move.id]
                    for lot in lot_qty:
                        if float_compare(lot_qty[lot], 0, precision_rounding=rounding) > 0 and float_compare(move_qty, 0, precision_rounding=rounding) > 0:
                            qty = min(lot_qty[lot], move_qty)
                            quants = quant_obj.quants_get_preferred_domain(cr, uid, qty, move, ops=ops, lot_id=lot, domain=domain, preferred_domain_list=[], context=context)
                            quant_obj.quants_reserve(cr, uid, quants, move, record, context=context)
                            lot_qty[lot] -= qty
                            move_qty -= qty


        # Sort moves to reserve first the ones with ancestors, in case the same product is listed in
        # different stock moves.
        todo_moves.sort(key=lambda x: -1 if ancestors_list.get(x.id) else 0)
        for move in todo_moves:
            #then if the move isn't totally assigned, try to find quants without any specific domain
            if (move.state != 'assigned') and not context.get("reserve_only_ops"):
                qty_already_assigned = move.reserved_availability
                qty = move.product_qty - qty_already_assigned
                ban = True
                if move.procurement_id:
                    if move.procurement_id.sale_line_id:
                        lot_ids = self.pool.get('stock.production.lot').search(cr, uid, [('product_id', '=', move.product_id.id), ('dimension_id', '=', move.procurement_id.sale_line_id.product_dimension.id)], {})
                        if lot_ids:
                            self.pool.get('stock.move').write(cr, uid, move.id, {'restrict_lot_id': lot_ids[0]}, {})
                quants = quant_obj.quants_get_preferred_domain(cr, uid, qty, move, domain=main_domain[move.id], preferred_domain_list=[], context=context)
                quant_obj.quants_reserve(cr, uid, quants, move, context=context)

        #force assignation of consumable products and incoming from supplier/inventory/production
        # Do not take force_assign as it would create pack operations
        if to_assign_moves:
            self.write(cr, uid, list(to_assign_moves), {'state': 'assigned'}, context=context)
        if not no_prepare:
            self.check_recompute_pack_op(cr, uid, ids, context=context)

    def _get_total_dimension(self, cr, uid, ids, name, args, context=None):
        res={}
        for line in self.browse(cr, uid, ids):
            res[line.id]={'total_dimension': None, 'total_dimension_display': None}
            if (line.procurement_id.sale_line_id):
                uom_obj=line.procurement_id.sale_line_id.product_dimension.uom_id

                #product_qty=line.sale_line_id.product_uom_qty
                product_qty=line.product_qty
                var_x=line.procurement_id.sale_line_id.product_dimension.var_x
                var_y=line.procurement_id.sale_line_id.product_dimension.var_y
                var_z=line.procurement_id.sale_line_id.product_dimension.var_z

                if line.procurement_id.sale_line_id.product_dimension.metric_type=='lineal':
                    res[line.id]['total_dimension']=var_x*product_qty
                    res[line.id]['total_dimension_display'] = str(var_x*product_qty)+uom_obj.name
                elif line.procurement_id.sale_line_id.product_dimension.metric_type=='area':
                    res[line.id]['total_dimension']=var_x*var_y*product_qty
                    res[line.id]['total_dimension_display'] = str(var_x*var_y*product_qty)+uom_obj.name+u"²"
                elif line.procurement_id.sale_line_id.product_dimension.metric_type=='volume':
                    res[line.id]['total_dimension']=var_x*var_y*var_z*product_qty
                    res[line.id]['total_dimension_display'] = str(var_x*var_y*var_z*product_qty)+uom_obj.name+u"³"
                else:
                    res[line.id]['total_dimension']=None
                    res[line.id]['total_dimension_display']=None
            else:
                if line.picking_id.picking_type_id.code == 'internal':
                    uom_obj = line.lot_creation_pack.dimension_id.uom_id

                    #product_qty=line.sale_line_id.product_uom_qty
                    product_qty=line.product_qty
                    var_x=line.lot_creation_pack.dimension_id.var_x
                    var_y=line.lot_creation_pack.dimension_id.var_y
                    var_z=line.lot_creation_pack.dimension_id.var_z

                    if line.lot_creation_pack.dimension_id.metric_type=='lineal':
                        res[line.id]['total_dimension']=var_x*product_qty
                        res[line.id]['total_dimension_display'] = str(var_x*product_qty)+uom_obj.name
                    elif line.lot_creation_pack.dimension_id.metric_type=='area':
                        res[line.id]['total_dimension']=var_x*var_y*product_qty
                        res[line.id]['total_dimension_display'] = str(var_x*var_y*product_qty)+uom_obj.name+u"²"
                    elif line.lot_creation_pack.dimension_id.metric_type=='volume':
                        res[line.id]['total_dimension']=var_x*var_y*var_z*product_qty
                        res[line.id]['total_dimension_display'] = str(var_x*var_y*var_z*product_qty)+uom_obj.name+u"³"
                    else:
                        res[line.id]['total_dimension']=None
                        res[line.id]['total_dimension_display']=None
                else:
                    res[line.id]['total_dimension']=None
                    res[line.id]['total_dimension_display']=None
        return res

    _columns = {
        'product_dimension': fields.many2one('product.dimension','Dimension'),
        'total_dimension': fields.function(_get_total_dimension, type="float", string="Total Metric w/o unit", store=True, multi="total_dimension"),
        'total_dimension_display': fields.function(_get_total_dimension, type="char", string="Total Metric", multi="total_dimension"),
    }
    
    def get_total_dimension(self, cr, uid, ids, context=None):
        res={}
        for line in self.browse(cr, uid, ids):
            res[line.id]=None
            uom_obj=line.procurement_id.sale_line_id.product_dimension
            
            if line.procurement_id.sale_line_id:
                #product_qty=line.sale_line_id.product_uom_qty
                product_qty=line.product_qty
                var_x=line.procurement_id.sale_line_id.product_dimension.var_x
                var_y=line.procurement_id.sale_line_id.product_dimension.var_y
                var_z=line.procurement_id.sale_line_id.product_dimension.var_z

                if line.procurement_id.sale_line_id.product_dimension.metric_type=='lineal':
                    res[line.id]=var_x*product_qty
                elif line.procurement_id.sale_line_id.product_dimension.metric_type=='area':
                    res[line.id]=var_x*var_y*product_qty
                elif line.procurement_id.sale_line_id.product_dimension.metric_type=='volume':
                    res[line.id]=var_x*var_y*var_z*product_qty
                else:
                    res[line.id]=None
            else:
                if line.picking_id.picking_type_id.code == 'internal':
                    #product_qty=line.sale_line_id.product_uom_qty
                    product_qty=line.product_qty
                    if line.lot_creation_pack.dimension_id:
                        var_x=line.lot_creation_pack.dimension_id.var_x
                        var_y=line.lot_creation_pack.dimension_id.var_y
                        var_z=line.lot_creation_pack.dimension_id.var_z
                    else:
                        #if line.prodlot_id:
                        #    var_x=line.prodlot_id.dimension_id.var_x
                        #    var_y=line.prodlot_id.dimension_id.var_y
                        #    var_z=line.prodlot_id.dimension_id.var_z
                        #else:
                            #return res
                        return res

                    if line.lot_creation_pack.dimension_id.metric_type=='lineal' or line.lot_creation_pack.dimension_id.metric_type=='lineal':
                        res[line.id]=var_x*product_qty
                    elif line.lot_creation_pack.dimension_id.metric_type=='area' or line.lot_creation_pack.dimension_id.metric_type=='area':
                        res[line.id]=var_x*var_y*product_qty
                    elif line.lot_creation_pack.dimension_id.metric_type=='volume' or line.lot_creation_pack.dimension_id.metric_type=='volume':
                        res[line.id]=var_x*var_y*var_z*product_qty
                    else:
                        res[line.id] = None
                else:
                    res[line.id] = None
        return res


    def onchange_product_id(self, cr, uid, ids, product, location_id, location_dest_id, flag=False, context=None):


        res=super(stock_move, self).onchange_product_id(cr, uid, ids, product, loc_id=False,
                            loc_dest_id=False, partner_id=False)

        #res = {}
        #res['value'] = {'qty':qty,'uom':uom, 'qty_uos':qty_uos, 'uos':uos, 'name':name, 'partner_id':partner_id, 'lang':lang, 'update_tax':update_tax, 'date_done':date_done, 'packaging':packaging, 'flag':flag, 'context':context}
        context = context or {}

        #TODO: This pricelist must be according dimensions given on sale order line
        dimension=context.get('product_dimension')
        if dimension and product:
            dim_pool = self.pool.get('product.dimension')
            metric = dim_pool.browse(cr, uid, dimension).get_total_computed()

            warning_msgs=""


            res['value'].update({'price_unit': 0})

            #NBA. Change product description to specify dimension
            dim_name = dim_pool.name_get(cr, uid, dimension) or ''
            name_change = 'name' in res['value'] and  res['value']['name'] or False
            if not name_change:
                prod_data = self.pool.get('product.product').read(cr, uid, [product], ['default_code','name'], context=context)[0]
                name_change = "[%s] %s" % (prod_data['default_code'],prod_data['name'] )
            res['value'].update({'name': "%s (%s)" % (name_change,dim_name[0][1]) })

        #Set the product domain
        if product:
            product_obj=self.pool.get('product.product').browse(cr, uid, product)
            #To be sure that we're adding a domain
            #if not res['domain']:
            res['domain']={}

            dimension_ids=[]

            if product_obj.dimension_ids:
                for dimension in product_obj.dimension_ids:
                    if product_obj.metric_type:
                        if dimension.metric_type==product_obj.metric_type:
                            dimension_ids.append(dimension.id)
                    else:
                        dimension_ids.append(dimension.id)

                res['domain']['product_dimension']=[('id','in',dimension_ids)]
            elif product_obj.metric_type:
                dimension_ids=self.pool.get('product.dimension').search(cr, uid, [('metric_type','=',product_obj.metric_type)])
                res['domain']['product_dimension']=[('id','in',dimension_ids)]

            #To be sure that product_dimension is between dimension_ids
            if dimension_ids:
                if context.get('product_dimension'):
                    if context.get('product_dimension') not in dimension_ids:
                        res['value'].update({'product_dimension' : False})
                        res['value'].update({'name': name_change})
                        if not res.get('warning'):
                            res['warning']={}
                        res['warning'].update({'title': _('Dimension removed'),
                                               'message': _('La dimensión seleccionada no es valida para este producto, por favor seleccione otra dimensión')})
            else:
                res['domain']['product_dimension']=[]

        return res

    def get_metric_type(self, cr, uid, ids, context=None):
        res={}
        for line in self.browse(cr, uid, ids):
            res[line.id]=None
            if line.procurement_id.sale_line_id:
                uom_obj=line.procurement_id.sale_line_id.product_dimension.uom_id

                res[line.id]=line.procurement_id.sale_line_id.product_dimension.metric_type
            else:
                if line.picking_id.picking_type_id.code == 'internal':
                    if line.lot_creation_pack.dimension_id:
                        uom_obj=line.lot_creation_pack.dimension_id.uom_id
                        res[line.id]=line.lot_creation_pack.dimension_id.metric_type
                    else:
                        # if line.prodlot_id:
                        #     uom_obj = line.prodlot_id.dimension_id.uom_id
                        #     res[line.id] = line.prodlot_id.dimension_id.metric_type
                        # else:
                        #     return res
                        return res
                else:
                    res[line.id]=None
        return res
stock_move()