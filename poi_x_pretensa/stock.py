##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2011 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Author: Nicolas Bustillos
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

from openerp import netsvc
from openerp.tools.translate import _
from openerp.report import report_sxw
from openerp.addons.report_webkit import webkit_report
from openerp.tools.float_utils import float_compare, float_round
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from datetime import datetime


class stock_recu_pret(report_sxw.rml_parse):
    def __init__(self, cr, uid, ids, context):
        super(stock_recu_pret, self).__init__(cr, uid, ids, context=context)
        picking_id = context.get('active_id')
        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id
        nit = company_id.nit
        logo = company_id.logo
        actividad = company_id.actividad

        stock_move = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', picking_id)])
        entrada = self.pool.get('stock.picking').browse(cr, uid, picking_id)
        fecha_entrada = entrada.date_done

        salida = self.pool.get('stock.picking').browse(cr, uid, picking_id)
        fecha_salida = salida.date_done

        if (fecha_entrada):
            fecha_entrada = datetime.strptime(fecha_entrada, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")

        if (fecha_salida):
            fecha_salida = datetime.strptime(fecha_salida, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")

        total_line = 0
        discount_line = 0
        i = 0
        for acc_line in self.pool.get('stock.move').browse(cr, uid, stock_move, context=context):
            i = i + 1

        total_filas_extra = 40 - i
        n = total_filas_extra
        self.total_recuperado = 0.0
        self.localcontext.update({
            'fecha_entrada': fecha_entrada,
            'fecha_salida': fecha_salida,
            'my_recuperado': self._reporte_recuperados(cr, uid, picking_id),
            'numero_filas': n,
            'total_recuperado': self.total_recuperado,

        })

    #def _get_total_recuperado(self):
    #    return self.total_recuperado

    def _reporte_recuperados(self, cr, uid, picking_id, *args):

        res = {}
        query_to_exe = """
          select
          row_number() over() as id,
          return_pack_lot,
          default_code,
          var_x,
          string_agg(codigo_ret, ', ') as codigos_ret,
          sum(valor_ret) as total,
          (var_x - sum(valor_ret)) as desperdicio,
          string_agg(valor_ret::TEXT, ' | ') as codigos_ret,
          causa
        FROM (
          SELECT
            t0.return_pack_lot,
            t7.default_code,
            t8.var_x,
            t3.default_code AS codigo_ret,
            t4.var_x        AS valor_ret,
            t5.causa
          FROM stock_pack_operation_lot t0
            INNER JOIN stock_pack_operation t1 ON t1.id = t0.operation_id
            INNER JOIN stock_production_lot t2 ON t2.id = t0.lot_id
            INNER JOIN product_product t3 ON t3.id = t2.product_id
            INNER JOIN product_dimension t4 ON t4.id = t2.dimension_id

            INNER JOIN stock_pack_operation_lot t5 ON t5.id = t0.return_pack_lot
            INNER JOIN stock_production_lot t6 ON t6.id = t5.lot_id
            INNER JOIN product_product t7 ON t7.id = t6.product_id
            INNER JOIN product_dimension t8 ON t8.id = t6.dimension_id
          WHERE t1.picking_id = """ + str(picking_id) + """
        ) as foo
         GROUP BY return_pack_lot, default_code, var_x, causa
order by default_code
         """  # , #(picking_id))
        cr.execute(query_to_exe)
        res_total = self.cr.fetchall()
        for totales in res_total:
            self.total_recuperado = self.total_recuperado + float(totales[6])

        cr.execute(query_to_exe)
        res = cr.fetchall()
        if not res:
            raise osv.except_osv('No hay registros', 'No existen registros a recuperar')
            return False
        else:
            return res


webkit_report.WebKitParser('report.recu.pretensa.webkit',
                           'stock.picking',
                           'addons/poi_x_pretensa/report/print_recu_pret.mako',
                           parser=stock_recu_pret)


class stock_move_operation_link(osv.osv):
    """
    Table making the link between stock.moves and stock.pack.operations to compute the remaining quantities on each of these objects
    """
    _inherit = "stock.move.operation.link"
    _description = "Link between stock moves and pack operations"

    _columns = {
        'lot_id': fields.many2one('stock.production.lot', 'Lote', ondelete="cascade"),
    }


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def quitar_reserva(self, cr, uid, picking_ids, context=None):
        """
          Will remove all quants for picking in picking_ids
        """
        moves_to_unreserve = []
        pack_line_to_unreserve = []
        for picking in self.browse(cr, uid, picking_ids, context=context):
            moves_to_unreserve += [m.id for m in picking.move_lines if m.state not in ('done', 'cancel')]
            pack_line_to_unreserve += [p.id for p in picking.pack_operation_ids]
        if moves_to_unreserve:
            if pack_line_to_unreserve:
                self.pool.get('stock.pack.operation').unlink(cr, uid, pack_line_to_unreserve, context=context)
            self.pool.get('stock.move').do_unreserve(cr, uid, moves_to_unreserve, context=context)

    def recompute_remaining_qty(self, cr, uid, picking, done_qtys=False, context=None):

        def _create_link_for_index(operation_id, index, product_id, qty_to_assign, quant_id=False):
            move_dict = prod2move_ids[product_id][index]
            qty_on_link = min(move_dict['remaining_qty'], qty_to_assign)
            self.pool.get('stock.move.operation.link').create(cr, uid, {'move_id': move_dict['move'].id,
                                                                        'operation_id': operation_id,
                                                                        'qty': qty_on_link,
                                                                        'reserved_quant_id': quant_id},
                                                              context=context)
            if move_dict['remaining_qty'] == qty_on_link:
                prod2move_ids[product_id].pop(index)
            else:
                move_dict['remaining_qty'] -= qty_on_link
            return qty_on_link

        def _create_link_for_quant(operation_id, quant, qty):
            """create a link for given operation and reserved move of given quant, for the max quantity possible, and returns this quantity"""
            if not quant.reservation_id.id:
                return _create_link_for_product(operation_id, quant.product_id.id, qty)
            qty_on_link = 0
            for i in range(0, len(prod2move_ids[quant.product_id.id])):
                if prod2move_ids[quant.product_id.id][i]['move'].id != quant.reservation_id.id:
                    continue
                qty_on_link = _create_link_for_index(operation_id, i, quant.product_id.id, qty, quant_id=quant.id)
                break
            return qty_on_link

        def _create_link_for_product(operation_id, product_id, qty):
            '''method that creates the link between a given operation and move(s) of given product, for the given quantity.
            Returns True if it was possible to create links for the requested quantity (False if there was not enough quantity on stock moves)'''
            qty_to_assign = qty
            prod_obj = self.pool.get("product.product")
            product = prod_obj.browse(cr, uid, product_id)
            rounding = product.uom_id.rounding
            qtyassign_cmp = float_compare(qty_to_assign, 0.0, precision_rounding=rounding)
            if prod2move_ids.get(product_id):
                while prod2move_ids[product_id] and qtyassign_cmp > 0:
                    qty_on_link = _create_link_for_index(operation_id, 0, product_id, qty_to_assign, quant_id=False)
                    qty_to_assign -= qty_on_link
                    qtyassign_cmp = float_compare(qty_to_assign, 0.0, precision_rounding=rounding)
            return qtyassign_cmp == 0

        def _create_link_for_index_lot(pack_lot, move_dict, quant_id=False):

            rounding = pack_lot.operation_id.product_id.uom_id.rounding
            qtyassign_cmp = float_compare(pack_lot.qty, 0.0, precision_rounding=rounding)
            qty_as = 0
            if pack_lot.qty > move_dict['move'].product_qty:
                qty_as = move_dict['move'].product_qty
            else:
                qty_as = pack_lot.qty

            self.pool.get('stock.move.operation.link').create(cr, uid, {'move_id': move_dict['move'].id,
                                                                        'operation_id': pack_lot.operation_id.id,
                                                                        'qty': qty_as,
                                                                        'reserved_quant_id': quant_id,
                                                                        'lot_id': move_dict['lot_id']}, context=context)
            return qtyassign_cmp == 0

        def _create_link_for_product_lot(pack_lot):
            '''method that creates the link between a given operation and move(s) of given product, for the given quantity.
            Returns True if it was possible to create links for the requested quantity (False if there was not enough quantity on stock moves)'''
            qty_to_assign = pack_lot.qty
            prod_obj = self.pool.get("product.product")
            product_id = pack_lot.operation_id.product_id.id
            product = prod_obj.browse(cr, uid, product_id)
            rounding = product.uom_id.rounding
            qtyassign_cmp = float_compare(qty_to_assign, 0.0, precision_rounding=rounding)
            i = 0
            #for pack_lot in pack_lots:
            # Aca entra 4 Veces
            if prod2move_ids.get(product_id):
                for prod_move in prod2move_ids[product_id]:
                    if 'lot_id' in prod_move:
                        if prod_move['lot_id'] == pack_lot.lot_id.id:
                            _create_link_for_index_lot(pack_lot, prod_move, quant_id=False)
            return qtyassign_cmp == 0
        if picking.location_id.usage != 'internal' or picking.location_dest_id.usage not in ('customer', 'transit'):
            return super(stock_picking, self).recompute_remaining_qty(cr, uid, picking, done_qtys=done_qtys, context=context)
        uom_obj = self.pool.get('product.uom')
        package_obj = self.pool.get('stock.quant.package')
        quant_obj = self.pool.get('stock.quant')
        link_obj = self.pool.get('stock.move.operation.link')
        lot_obj = self.pool.get('stock.production.lot')
        quants_in_package_done = set()
        prod2move_ids = {}
        still_to_do = []
        still_to_do_lot = []
        # make a dictionary giving for each product, the moves and related quantity that can be used in operation links
        moves = sorted([x for x in picking.move_lines if x.state not in ('done', 'cancel')],
                       key=lambda x: (((x.state == 'assigned') and -2 or 0) + (x.partially_available and -1 or 0)))
        # Adicionalmente podemos asignar el lote en cada movimiento
        for move in moves:
            lot_ids = []
            if move.lot_creation_pack:
                lot_ids.append(move.lot_creation_pack.id)
            else:
                lot_ids = lot_obj.search(cr, uid, [('product_id', '=', move.product_id.id), (
                    'dimension_id', '=', move.procurement_id.sale_line_id.product_dimension.id)], {})

            # Si el manejo es por lotes usar lot_ids
            if lot_ids:
                if not prod2move_ids.get(move.product_id.id):
                    prod2move_ids[move.product_id.id] = [
                        {'move': move, 'remaining_qty': move.product_qty, 'lot_id': lot_ids[0]}]
                else:
                    prod2move_ids[move.product_id.id].append(
                        {'move': move, 'remaining_qty': move.product_qty, 'lot_id': lot_ids[0]})

            # El producto es de uso normal
            else:
                if not prod2move_ids.get(move.product_id.id):
                    prod2move_ids[move.product_id.id] = [
                        {'move': move, 'remaining_qty': move.product_qty}]
                else:
                    prod2move_ids[move.product_id.id].append(
                        {'move': move, 'remaining_qty': move.product_qty})

        need_rereserve = False
        # sort the operations in order to give higher priority to those with a package, then a serial number
        operations = picking.pack_operation_ids
        operations = sorted(operations, key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (
            x.package_id and -2 or 0) + (x.pack_lot_ids and -1 or 0))
        # Eliminar operaciones existentes para empezar de nuevo desde cero
        links = link_obj.search(cr, uid, [('operation_id', 'in', [x.id for x in operations])], context=context)
        if links:
            link_obj.unlink(cr, uid, links, context=context)
        # 1) Primero, trate de crear enlaces cuando los cuants puedan ser identificados sin ninguna duda
        pack_lot_serial = False
        for ops in operations:
            lot_qty = {}
            for packlot in ops.pack_lot_ids:
                lot_qty[packlot.lot_id.id] = uom_obj._compute_qty(cr, uid, ops.product_uom_id.id, packlot.qty,
                                                                  ops.product_id.uom_id.id)
                # Para cada operación, crear los vínculos con el movimiento de existencias buscando en los equivalentes reservado quants,
                # y deffer la operación si hay alguna ambigüedad en el movimiento para seleccionar
            if ops.package_id and not ops.product_id and (not done_qtys or ops.qty_done):
                # Paquete completo
                quant_ids = package_obj.get_content(cr, uid, [ops.package_id.id], context=context)
                for quant in quant_obj.browse(cr, uid, quant_ids, context=context):
                    remaining_qty_on_quant = quant.qty
                    if quant.reservation_id:
                        # Evitar que los cuantes sean contados dos veces
                        quants_in_package_done.add(quant.id)
                        qty_on_link = _create_link_for_quant(ops.id, quant, quant.qty)
                        remaining_qty_on_quant -= qty_on_link
                    if remaining_qty_on_quant:
                        still_to_do.append((ops, quant.product_id.id, remaining_qty_on_quant))
                        need_rereserve = True
            elif ops.product_id.id:
                # Check moves with same product
                product_qty = ops.qty_done if done_qtys else ops.product_qty
                qty_to_assign = uom_obj._compute_qty_obj(cr, uid, ops.product_uom_id, product_qty,
                                                         ops.product_id.uom_id, context=context)
                precision_rounding = ops.product_id.uom_id.rounding
                for move_dict in prod2move_ids.get(ops.product_id.id, []):
                    move = move_dict['move']
                    # Verificar si el movimiento tiene quants reservados
                    if move.reserved_quant_ids:
                        for quant in move.reserved_quant_ids:
                            if float_compare(qty_to_assign, 0, precision_rounding=precision_rounding) != 1:
                                break
                            if quant.id in quants_in_package_done:
                                continue

                            # check if the quant is matching the operation details
                            if ops.package_id:
                                flag = quant.package_id == ops.package_id
                            else:
                                flag = not quant.package_id.id
                            flag = flag and (ops.owner_id.id == quant.owner_id.id)
                            if flag:
                                if not lot_qty:
                                    max_qty_on_link = min(quant.qty, qty_to_assign)
                                    qty_on_link = _create_link_for_quant(ops.id, quant, max_qty_on_link)
                                    qty_to_assign -= qty_on_link
                                else:
                                    if lot_qty.get(quant.lot_id.id):  # if there is still some qty left
                                        max_qty_on_link = min(quant.qty, qty_to_assign, lot_qty[quant.lot_id.id])
                                        qty_on_link = _create_link_for_quant(ops.id, quant, max_qty_on_link)
                                        qty_to_assign -= qty_on_link
                                        lot_qty[quant.lot_id.id] -= qty_on_link
                                        # En caso de no tener reservas aplicamos a negativo
                                        # else:

                qty_assign_cmp = float_compare(qty_to_assign, 0, precision_rounding=precision_rounding)
                if qty_assign_cmp > 0:
                    # Qty reservado es menos que qty puesto en operaciones. Necesitamos crear un enlace, pero se aplazó después de procesar
                    # Todos los quants (porque no dejan opción en su movimiento relacionado y necesitan ser procesados con mayor prioridad)
                    if ops.pack_lot_ids:
                        for packlot in ops.pack_lot_ids:
                            still_to_do_lot += [(packlot)]
                    else:
                        still_to_do += [(ops, ops.product_id.id, qty_to_assign)]
                    need_rereserve = True

        # 2) Luego, procese la parte restante
        all_op_processed = True

        # Verificar si existe lotes asigandos a la operación de almacén
        for packlot in still_to_do_lot:
            if hasattr(packlot, 'operation_id'):
                if packlot.operation_id.product_id.tracking in ('serial', 'lot'):
                    all_op_processed = _create_link_for_product_lot(packlot) and all_op_processed
        for ops, product_id, remaining_qty in still_to_do:
            all_op_processed = _create_link_for_product(ops.id, product_id, remaining_qty) and all_op_processed
        return (need_rereserve, all_op_processed)

    def _get_total_metric(self, cr, uid, ids, field_names, arg=None, context=None):

        res = {}

        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = {}
            sum_metric = 0.0
            sum_metric_m2 = 0.0
            sum_metric_m3 = 0.0
            sum_weight = 0.0
            top_uom = ''
            for line in picking.move_lines:
                tot_dim = line.get_total_dimension()[line.id] or 0.0
                metric_type = line.get_metric_type()[line.id]
                if (metric_type) == 'lineal':
                    sum_metric += tot_dim
                    sum_metric_m2 += 0.0
                    sum_metric_m3 += 0.0
                else:
                    if (metric_type) == 'area':
                        sum_metric_m2 += tot_dim
                        sum_metric += 0.0
                        sum_metric_m3 += 0.0
                    else:
                        if (metric_type) == 'volume':
                            sum_metric_m3 += tot_dim
                            sum_metric_m2 += 0.0
                            sum_metric += 0.0
                        else:
                            sum_metric += 0.0
                            sum_metric_m2 += 0.0
                            sum_metric_m3 += 0.0
                sum_weight += (
                                  line.product_id and line.product_id.weight or 0.0) * tot_dim  # * (line.product_qty or 0.0)

                if line.product_dimension:
                    top_uom = line.procurement_id.sale_line_id.product_dimension and line.procurement_id.sale_line_id.product_dimension.uom_id.name or line.product_dimension.uom_id.name or ''
                else:
                    top_uom = 'm'

                res[picking.id]['total_metric'] = str(sum_metric) + ' ' + top_uom

                res[picking.id]['total_metric_m2'] = str(sum_metric_m2) + ' ' + top_uom + u"²"

                res[picking.id]['total_metric_m3'] = str(sum_metric_m3) + ' ' + top_uom + u"³"

                res[picking.id]['total_weight'] = sum_weight / 46  # División para quintales

                # res[picking.id]['vendedor'] =

        return res

    _columns = {
        'check_recu': fields.boolean('Recuperar'),
        'transportista': fields.many2one('res.partner', 'Transportista'),
        'placa': fields.char('Placa', size=8),
        'total_metric': fields.function(_get_total_metric, multi='totals', type='char', size=10,
                                        string=u'Total métrica (m)', store=True, readonly=True),
        'total_metric_m2': fields.function(_get_total_metric, multi='totals', type='char', size=10,
                                           string=u'Total métrica (m²)', store=True, readonly=True),
        'total_metric_m3': fields.function(_get_total_metric, multi='totals', type='char', size=10,
                                           string=u'Total métrica (m³)', store=True, readonly=True),
        'total_weight': fields.function(_get_total_metric, multi='totals', type='float', string=u'Total quintales',
                                        store=True, readonly=True),
        'tipo_entrega': fields.selection([('planta', 'En planta'), ('obra', 'En obra')], 'Entrega', readonly=True),
        'socio_ref': fields.many2one('res.partner', 'Socio Referente', readonly=True),
        'picking_id': fields.many2one('stock.picking', 'Recuperación de:'),
    }

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial picking and moves done.
        @param partial_datas : Dictionary containing details of partial picking
                          like partner_id, partner_id, delivery_date,
                          delivery moves with product_id, product_qty, uom
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        sequence_obj = self.pool.get('ir.sequence')
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids, context=context):
            new_picking = None
            complete, too_many, too_few = [], [], []
            move_product_qty, prodlot_ids, product_avail, partial_qty, product_uoms = {}, {}, {}, {}, {}
            for move in pick.move_lines:
                if move.state in ('done', 'cancel'):
                    continue
                partial_data = partial_datas.get('move%s' % (move.id), {})
                product_qty = partial_data.get('product_qty', 0.0)
                move_product_qty[move.id] = product_qty
                product_uom = partial_data.get('product_uom', False)
                product_price = partial_data.get('product_price', 0.0)
                product_currency = partial_data.get('product_currency', False)
                prodlot_id = partial_data.get('prodlot_id')
                prodlot_ids[move.id] = prodlot_id
                product_uoms[move.id] = product_uom
                partial_qty[move.id] = uom_obj._compute_qty(cr, uid, product_uoms[move.id], product_qty,
                                                            move.product_uom.id)
                if move.product_qty == partial_qty[move.id]:
                    complete.append(move)
                elif move.product_qty > partial_qty[move.id]:
                    too_few.append(move)
                else:
                    too_many.append(move)

                # Average price computation
                if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
                    product = product_obj.browse(cr, uid, move.product_id.id)
                    move_currency_id = move.company_id.currency_id.id
                    context['currency_id'] = move_currency_id
                    qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)

                    if product.id in product_avail:
                        product_avail[product.id] += qty
                    else:
                        product_avail[product.id] = product.qty_available

                    if qty > 0:
                        new_price = currency_obj.compute(cr, uid, product_currency,
                                                         move_currency_id, product_price)
                        new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                                                           product.uom_id.id)
                        if product.qty_available <= 0:
                            new_std_price = new_price
                        else:
                            # Get the standard price
                            amount_unit = product.price_get('standard_price', context=context)[product.id]
                            new_std_price = ((amount_unit * product_avail[product.id]) \
                                             + (new_price * qty)) / (product_avail[product.id] + qty)
                        # Write the field according to price type field
                        product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price})

                        # Record the values that were chosen in the wizard, so they can be
                        # used for inventory valuation if real-time valuation is enabled.
                        move_obj.write(cr, uid, [move.id],
                                       {'price_unit': product_price,
                                        'price_currency_id': product_currency})

            for move in too_few:
                product_qty = move_product_qty[move.id]
                if not new_picking:
                    new_picking_name = pick.name
                    self.write(cr, uid, [pick.id],
                               {'name': sequence_obj.get(cr, uid,
                                                         'stock.picking.%s' % (pick.type)),
                                })
                    new_picking = self.copy(cr, uid, pick.id,
                                            {
                                                'name': new_picking_name,
                                                'move_lines': [],
                                                'state': 'draft',
                                            })
                if product_qty != 0:
                    defaults = {
                        'product_qty': product_qty,
                        'product_uos_qty': product_qty,  # TODO: put correct uos_qty
                        'picking_id': new_picking,
                        'state': 'assigned',
                        'move_dest_id': False,
                        'price_unit': move.price_unit,
                        'product_uom': product_uoms[move.id]
                    }
                    prodlot_id = prodlot_ids[move.id]
                    if prodlot_id:
                        defaults.update(prodlot_id=prodlot_id)
                    move_obj.copy(cr, uid, move.id, defaults)
                    # lot_id=self._get_dimension_lot_id(cr, uid, line.product_id.id, line.product_dimension.id, context=context)
                move_obj.write(cr, uid, [move.id],
                               {
                                   'product_qty': move.product_qty - partial_qty[move.id],
                                   'product_uos_qty': move.product_qty - partial_qty[move.id],
                                   # TODO: put correct uos_qty
                                   'prodlot_id': move.prodlot_id.id,
                                   'tracking_id': False,
                               })

            if new_picking:
                move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
            for move in complete:
                defaults = {'product_uom': product_uoms[move.id], 'product_qty': move_product_qty[move.id]}
                if prodlot_ids.get(move.id):
                    defaults.update({'prodlot_id': prodlot_ids[move.id]})
                move_obj.write(cr, uid, [move.id], defaults)
            for move in too_many:
                product_qty = move_product_qty[move.id]
                defaults = {
                    'product_qty': product_qty,
                    'product_uos_qty': product_qty,  # TODO: put correct uos_qty
                    'product_uom': product_uoms[move.id]
                }
                prodlot_id = prodlot_ids.get(move.id)
                if prodlot_ids.get(move.id):
                    defaults.update(prodlot_id=prodlot_id)
                if new_picking:
                    defaults.update(picking_id=new_picking)
                move_obj.write(cr, uid, [move.id], defaults)

            # At first we confirm the new picking (if necessary)
            if new_picking:
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                # Then we finish the good picking
                self.write(cr, uid, [pick.id], {'backorder_id': new_picking})
                self.action_move(cr, uid, [new_picking], context=context)
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
                delivered_pack_id = new_picking
                back_order_name = self.browse(cr, uid, delivered_pack_id, context=context).name
                self.message_post(cr, uid, ids,
                                  body=_("Back order <em>%s</em> has been <b>created</b>.") % (back_order_name),
                                  context=context)
            else:
                self.action_move(cr, uid, [pick.id], context=context)
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
                delivered_pack_id = pick.id

            delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}

            ###########################################################################
            sum_metric = 0.0
            sum_metric_m2 = 0.0
            sum_metric_m3 = 0.0
            sum_weight = 0.0
            top_uom = ''
            result = []
            picking_id = self.pool.get('stock.picking').browse(cr, uid, new_picking, context=context)
            vale1 = 0
            if picking_id:

                lista = set(pick.move_lines).difference(picking_id.move_lines)
                for line in lista:
                    tot_dim = line.get_total_dimension()[line.id] or 0.0
                    metric_type = line.get_metric_type()[line.id]
                    if (metric_type) == 'lineal':
                        sum_metric += tot_dim
                        sum_metric_m2 += 0.0
                        sum_metric_m3 += 0.0
                    else:
                        if (metric_type) == 'area':
                            sum_metric_m2 += tot_dim
                            sum_metric += 0.0
                            sum_metric_m3 += 0.0
                        else:
                            if (metric_type) == 'volume':
                                sum_metric_m3 += tot_dim
                                sum_metric_m2 += 0.0
                                sum_metric += 0.0
                            else:
                                sum_metric += 0.0
                                sum_metric_m2 += 0.0
                                sum_metric_m3 += 0.0
                    sum_weight += (
                                      line.product_id and line.product_id.weight or 0.0) * tot_dim  # * (line.product_qty or 0.0)
                    top_uom = line.procurement_id.sale_line_id.product_dimension and line.procurement_id.sale_line_id.product_dimension.uom_id.name or ''

                    total_metric = str(sum_metric) + ' ' + top_uom

                    total_metric_m2 = str(sum_metric_m2) + ' ' + top_uom + u"²"

                    total_metric_m3 = str(sum_metric_m3) + ' ' + top_uom + u"³"

                    total_weight = sum_weight / 46

                picking_obj = self.pool.get('stock.picking')

                defaults = {
                    'total_metric': total_metric,
                    'total_metric_m2': total_metric_m2,
                    'total_metric_m3': total_metric_m3,
                    'total_weight': total_weight
                }

                picking_obj.write(cr, uid, [pick.id], defaults)

            #######################-------------------------------###########################################################

            sum_metric = 0.0
            sum_metric_m2 = 0.0
            sum_metric_m3 = 0.0
            sum_weight = 0.0
            top_uom = ''

            picking_id = self.pool.get('stock.picking').browse(cr, uid, new_picking, context=context)
            if not picking_id:
                picking_id = pick
            for line in picking_id.move_lines:
                tot_dim = line.get_total_dimension()[line.id] or 0.0
                metric_type = line.get_metric_type()[line.id]
                if (metric_type) == 'lineal':
                    sum_metric += tot_dim
                    sum_metric_m2 += 0.0
                    sum_metric_m3 += 0.0
                else:
                    if (metric_type) == 'area':
                        sum_metric_m2 += tot_dim
                        sum_metric += 0.0
                        sum_metric_m3 += 0.0
                    else:
                        if (metric_type) == 'volume':
                            sum_metric_m3 += tot_dim
                            sum_metric_m2 += 0.0
                            sum_metric += 0.0
                        else:
                            sum_metric += 0.0
                            sum_metric_m2 += 0.0
                            sum_metric_m3 += 0.0
                sum_weight += (
                                  line.product_id and line.product_id.weight or 0.0) * tot_dim  # * (line.product_qty or 0.0)
                top_uom = line.procurement_id.sale_line_id.product_dimension and line.procurement_id.sale_line_id.product_dimension.uom_id.name or ''

                total_metric = str(sum_metric) + ' ' + top_uom

                total_metric_m2 = str(sum_metric_m2) + ' ' + top_uom + u"²"

                total_metric_m3 = str(sum_metric_m3) + ' ' + top_uom + u"³"

                total_weight = sum_weight / 46

            picking_obj = self.pool.get('stock.picking')

            defaults = {
                'total_metric': total_metric,
                'total_metric_m2': total_metric_m2,
                'total_metric_m3': total_metric_m3,
                'total_weight': total_weight
            }

            picking_obj.write(cr, uid, [picking_id.id], defaults)

        return res


stock_picking()


class stock_move(osv.osv):
    _inherit = 'stock.move'

    def _get_product_availability(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids, False)
        for move in self.browse(cr, uid, ids, context=context):
            if move.state == 'done':
                res[move.id] = move.product_qty
            else:
                availability = 0
                res[move.id] = min(move.product_qty, availability)
        return res

    def _get_string_qty_information(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids, '')
        for move in self.browse(cr, uid, ids, context=context):
            info = _(' (reserved)')
            res[move.id] = info
        return res

    _columns = {
        'product_recu': fields.many2one('product.product', 'Prod. Recuperar'),
        'serial_recu': fields.many2one('stock.production.lot', 'N° de Serie Recu'),
        'id_recu': fields.many2one('stock.move', 'Id. Recu'),
        'stock_move_split': fields.char('Id split recu', size=64),
        'obs_recu': fields.text('Causas no conformidad'),
        'availability': fields.function(_get_product_availability, type='float', string='Forecasted Quantity',
                                        readonly=False,
                                        help='Quantity in stock that can still be reserved for this move'),
        'string_availability_info': fields.function(_get_string_qty_information, type='text', string='Availability',
                                                    readonly=False,
                                                    help='Show various information on stock availability for this move'),
    }


stock_move()


# class poi_stock_product_add_wizard2(osv.osv):
#     _inherit = 'poi_stock.product_add.wizard'
#     _columns = {
#         'picking_id_recu': fields.many2one('stock.picking', 'Recuperación de:'),
#     }
#
#     def onchange_product_recu(self, cr, uid, ids, product_id=False, product_add_lines=False):
#         form_add = {}
#         if product_id > 0:
#             form_add = {
#                 'value':{'product_qty': 0, 'prodlot_id': False, 'product_add_lines': []},
#             }
#             last_row = len(product_add_lines) - 1
#             for i, prod_line in enumerate(product_add_lines):
#                 if prod_line[2]:
#                     if i == last_row:
#                         prod_line[2]['product_recu'] = product_id
#                     form_add['value']['product_add_lines'].append(prod_line[2])
#
#
#         return form_add
#
#     def onchange_picking_id(self, cr, uid, ids, picking_id_recu=False, context=None):
#         sp_obj = self.pool.get('stock.picking')
#         ctx = context
#         if context is None:
#             context = {}
#         #defaults
#         res = {'value':{
#                       'product_add_lines': False,
#                       }
#               }
#         picking_id = sp_obj.search(cr, uid, [('id', '=', picking_id_recu)], context=context)
#
#         if not picking_id:
#             return res
#         picking = sp_obj.browse(cr, uid, picking_id[0], context=context)
#
#         lines = []
#
#         for sm in picking.move_lines:
#
#             product_id=sm.product_id.id
#             if product_id:
#                 product_obj = self.pool.get('product.product')
#                 stock_actual = product_obj.get_product_available(cr, uid, [product_id], context=context) or False
#             lines.append((0,0,{'product_id': sm.product_id.id, 'id_recu': sm.id, 'product_qty':sm.product_qty, 'prodlot_id': sm.prodlot_id.id, 'stock': stock_actual[product_id] or 0.0, 'product_uom': sm.product_uom.id}))
#
#             stocklines_obj = self.pool.get('poi_stock.product_add.lines')
#             stocklines_id = stocklines_obj.create(cr, uid, {
#                             'wiz_id': ids[0],
#                             'prodlot_id': sm.prodlot_id.id,
#                             'product_id': sm.product_id.id,
#                             'product_uom': sm.product_uom.id,
#                             'product_qty':sm.product_qty,
#                             'stock': stock_actual[product_id] or 0.0},
#                              context=context)
#         return {'view_mode' : 'tree,form','type': 'ir.actions.act_window'}
#         #return res
#
#
#     def onchange_serial_recu(self, cr, uid, ids, product_id=False, product_add_lines=False):
#         form_add = {}
#         if product_id > 0:
#             form_add = {
#                 'value':{'product_qty': 0, 'prodlot_id': False, 'product_add_lines': []},
#             }
#             last_row = len(product_add_lines) - 1
#             for i, prod_line in enumerate(product_add_lines):
#                 if prod_line[2]:
#                     if i == last_row:
#                         prod_line[2]['serial_recu'] = product_id
#                     form_add['value']['product_add_lines'].append(prod_line[2])
#
#
#         return form_add
#
#     def copy_lines(self, cr, uid, ids, context=None):
#
#         move_obj = self.pool.get('stock.move')
#         for wiz in self.browse(cr, uid, ids, context=context):
#
#             for line in wiz.product_add_lines:
#                 move_line = {
#                     'picking_id': wiz.picking_id.id,
#                     'date' : wiz.picking_id.date or False,
#                     'date_expected' : wiz.picking_id.min_date or wiz.picking_id.date or False,
#                     'name': line.product_id.partner_ref,
#                     'product_id': line.product_id.id,
#                     'product_uom': line.product_id.uom_id.id,
#                     'product_uos': line.product_id.uos_id and line.product_id.uos_id.id or False,
#                     'product_qty': line.product_qty,
#                     'prodlot_id': line.prodlot_id and line.prodlot_id.id or False,
#                     'obs_recu': line.obs_recu or False,
#                     'location_id': wiz.picking_id.location_id.id or False,
#                     'location_dest_id': wiz.picking_id.location_dest_id.id or False,
#                 }
#                 move_obj.create(cr, uid, move_line, context=context)
#
#         res = {}
#
#         for picking in self.pool.get('stock.picking').browse(cr, uid, [wiz.picking_id.id], context=context):
#             res[picking.id] = {}
#             sum_metric = 0.0
#             sum_metric_m2 = 0.0
#             sum_metric_m3 = 0.0
#             sum_weight = 0.0
#             top_uom = ''
#             for line in picking.move_lines:
#                 tot_dim = line.get_total_dimension()[line.id] or 0.0
#                 metric_type=line.get_metric_type()[line.id]
#                 if (metric_type)=='lineal':
#                     sum_metric += tot_dim
#                     sum_metric_m2 += 0.0
#                     sum_metric_m3 += 0.0
#                 else:
#                     if (metric_type)=='area':
#                         sum_metric_m2 += tot_dim
#                         sum_metric += 0.0
#                         sum_metric_m3 += 0.0
#                     else:
#                         if (metric_type)=='volume':
#                             sum_metric_m3 += tot_dim
#                             sum_metric_m2 += 0.0
#                             sum_metric += 0.0
#                         else:
#                             sum_metric += 0.0
#                             sum_metric_m2 += 0.0
#                             sum_metric_m3 += 0.0
#                 sum_weight += (line.product_id and line.product_id.weight or 0.0) * tot_dim #* (line.product_qty or 0.0)
#
#                 if line.product_dimension:
#                     top_uom = line.procurement_id.sale_line_id.product_dimension and line.procurement_id.sale_line_id.product_dimension.uom_id.name or line.product_dimension.uom_id.name or ''
#                 else:
#                     top_uom='m'
#
#                 res[picking.id]['total_metric'] = str(sum_metric) + ' ' + top_uom
#
#                 res[picking.id]['total_metric_m2'] = str(sum_metric_m2) + ' ' + top_uom+u"²"
#
#                 res[picking.id]['total_metric_m3'] = str(sum_metric_m3) + ' ' + top_uom+u"³"
#
#                 res[picking.id]['total_weight'] = sum_weight / 46     #División para quintales
#
#         self.pool.get('stock.picking').write(cr, uid, wiz.picking_id.id, {'total_metric': str(sum_metric) + ' ' + top_uom,'total_metric_m2': str(sum_metric_m2) + ' ' + top_uom+u"²",'total_metric_m3': str(sum_metric_m3) + ' ' + top_uom+u"³",'total_weight': sum_weight / 46}, context=context)
#
#         return {'view_mode' : 'tree,form','type': 'ir.actions.act_window_close'}
#
# poi_stock_product_add_wizard2()

# class product_add_line(osv.osv):
#     _inherit = 'poi_stock.product_add.lines'
#
#
#     _columns = {
#
#     'product_recu': fields.many2one('product.product', 'Prod. Recuperar'),
#     'serial_recu': fields.many2one('stock.production.lot', 'Serial. Recuperar'),
#     'obs_recu': fields.text('Causas no conformidad'),
#
#     }
#
# product_add_line()
#
# class split_in_production_lot(osv.osv_memory):
#     _inherit = "stock.move.split"
#
#     def split_lot(self, cr, uid, ids, context=None):
#         """ To split a lot"""
#         if context is None:
#             context = {}
#         res = self.split(cr, uid, ids, context.get('active_ids'), context=context)
#         return {'type': 'ir.actions.act_window_close'}
#
#     def split(self, cr, uid, ids, move_ids, context=None):
#         """ To split stock moves into serial numbers
#
#         :param move_ids: the ID or list of IDs of stock move we want to split
#         """
#         if context is None:
#             context = {}
#         assert context.get('active_model') == 'stock.move',\
#              'Incorrect use of the stock move split wizard'
#         inventory_id = context.get('inventory_id', False)
#         prodlot_obj = self.pool.get('stock.production.lot')
#         inventory_obj = self.pool.get('stock.inventory')
#         move_obj = self.pool.get('stock.move')
#         new_move = []
#         for data in self.browse(cr, uid, ids, context=context):
#             for move in move_obj.browse(cr, uid, move_ids, context=context):
#                 move_qty = move.product_qty
#                 quantity_rest = move.product_qty
#                 uos_qty_rest = move.product_uos_qty
#                 new_move = []
#                 if data.use_exist:
#                     lines = [l for l in data.line_exist_ids if l]
#                 else:
#                     lines = [l for l in data.line_ids if l]
#                 total_move_qty = 0.0
#                 for line in lines:
#                     quantity = line.quantity
#                     total_move_qty += quantity
#                     if total_move_qty > move_qty:
#                         raise osv.except_osv(_('Processing Error!'), _('Serial number quantity %d of %s is larger than available quantity (%d)!') \
#                                 % (total_move_qty, move.product_id.name, move_qty))
#                     if quantity <= 0 or move_qty == 0:
#                         continue
#                     quantity_rest -= quantity
#                     uos_qty = quantity / move_qty * move.product_uos_qty
#                     uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
#                     if quantity_rest < 0:
#                         quantity_porrest = quantity
#                         self.pool.get('stock.move').log(cr, uid, move.id, _('Unable to assign all lots to this move!'))
#                         return False
#                     default_val = {
#                         'product_qty': quantity,
#                         'product_uos_qty': uos_qty,
#                         'state': move.state
#                     }
#                     if quantity_rest > 0:
#                         current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
#                         if inventory_id and current_move:
#                             inventory_obj.write(cr, uid, inventory_id, {'move_ids': [(4, current_move)]}, context=context)
#                         new_move.append(current_move)
#
#                     if quantity_rest == 0:
#                         current_move = move.id
#                     prodlot_id = False
#                     if data.use_exist:
#                         prodlot_id = line.prodlot_id.id
#                         product_id = line.prodlot_id.product_id.id
#                     if not prodlot_id:
#                         prodlot_id = prodlot_obj.create(cr, uid, {
#                             'name': line.name,
#                             'product_id': move.product_id.id},
#                         context=context)
#                         product_id=move.product_id.id
#
#                     move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'product_id':product_id ,'state':move.state, 'stock_move_split': line.wizard_exist_id.id})
#
#                     update_val = {}
#                     if quantity_rest > 0:
#                         update_val['product_qty'] = quantity_rest
#                         update_val['product_uos_qty'] = uos_qty_rest
#                         update_val['state'] = move.state
#                         move_obj.write(cr, uid, [move.id], update_val)
#
#         return new_move
#
#
# split_in_production_lot()

class recu_in_production_lot(osv.osv_memory):
    _name = "stock.move.recu"
    _description = "Productos Recuperados Almacen"

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(recu_in_production_lot, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
            if 'product_id' in fields:
                res.update({'product_id': move.product_id.id})
            if 'product_uom' in fields:
                res.update({'product_uom': move.product_uom.id})
            if 'qty' in fields:
                res.update({'qty': move.product_qty})
            if 'use_exist' in fields:
                res.update({'use_exist': (move.picking_id and move.picking_id.type == 'out' and True) or False})
            if 'location_id' in fields:
                res.update({'location_id': move.location_id.id})
        return res

    _columns = {
        'qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'product_id': fields.many2one('product.product', 'Product', required=True, select=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure'),
        'line_ids': fields.one2many('stock.move.recu.lines', 'wizard_id', 'Serial Numbers'),
        'line_exist_ids': fields.one2many('stock.move.recu.lines', 'wizard_exist_id', 'Serial Numbers'),
        'use_exist': fields.boolean('Existing Serial Numbers',
                                    help="Check this option to select existing serial numbers in the list below, otherwise you should enter new ones line by line."),
        'location_id': fields.many2one('stock.location', 'Source Location')
    }

    def split_lot(self, cr, uid, ids, context=None):
        """ To split a lot"""
        if context is None:
            context = {}
        res = self.split(cr, uid, ids, context.get('active_ids'), context=context)
        return {'type': 'ir.actions.act_window_close'}

    def split(self, cr, uid, ids, move_ids, context=None):
        """ To split stock moves into serial numbers

        :param move_ids: the ID or list of IDs of stock move we want to split
        """
        if context is None:
            context = {}
        assert context.get('active_model') == 'stock.move', \
            'Incorrect use of the stock move split wizard'
        inventory_id = context.get('inventory_id', False)
        prodlot_obj = self.pool.get('stock.production.lot')
        inventory_obj = self.pool.get('stock.inventory')
        move_obj = self.pool.get('stock.move')
        new_move = []
        for data in self.browse(cr, uid, ids, context=context):
            for move in move_obj.browse(cr, uid, move_ids, context=context):
                move_qty = move.product_qty
                quantity_rest = move.product_qty
                uos_qty_rest = move.product_uos_qty
                new_move = []
                if data.use_exist:
                    lines = [l for l in data.line_exist_ids if l]
                else:
                    lines = [l for l in data.line_ids if l]
                total_move_qty = 0.0
                for line in lines:
                    quantity = line.quantity
                    total_move_qty += quantity
                    if total_move_qty > move_qty:
                        raise osv.except_osv(_('Processing Error!'), _(
                            'Serial number quantity %d of %s is larger than available quantity (%d)!') \
                                             % (total_move_qty, move.product_id.name, move_qty))
                    if quantity <= 0 or move_qty == 0:
                        continue
                    quantity_rest -= quantity
                    uos_qty = quantity / move_qty * move.product_uos_qty
                    uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
                    if quantity_rest < 0:
                        quantity_rest = quantity
                        self.pool.get('stock.move').log(cr, uid, move.id, _('Unable to assign all lots to this move!'))
                        return False
                    default_val = {
                        'product_qty': quantity,
                        'product_uos_qty': uos_qty,
                        'state': move.state
                    }
                    if quantity_rest > 0:
                        current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
                        if inventory_id and current_move:
                            inventory_obj.write(cr, uid, inventory_id, {'move_ids': [(4, current_move)]},
                                                context=context)
                        new_move.append(current_move)

                    if quantity_rest == 0:
                        current_move = move.id
                    prodlot_id = False
                    if data.use_exist:
                        prodlot_id = line.prodlot_id.id
                    if not prodlot_id:
                        prodlot_id = prodlot_obj.create(cr, uid, {
                            'name': line.name,
                            'product_id': move.product_id.id},
                                                        context=context)

                    move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'state': move.state})

                    update_val = {}
                    if quantity_rest > 0:
                        update_val['product_qty'] = quantity_rest
                        update_val['product_uos_qty'] = uos_qty_rest
                        update_val['state'] = move.state
                        move_obj.write(cr, uid, [move.id], update_val)

        return new_move


recu_in_production_lot()


class stock_move_recu_lines_exist(osv.osv_memory):
    _name = "stock.move.recu.lines"
    _description = "Productos recuperados lineas"
    _columns = {
        'name': fields.char('Serial Number', size=64),
        'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'wizard_id': fields.many2one('stock.move.recu', 'Parent Wizard'),
        'wizard_exist_id': fields.many2one('stock.move.recu', 'Parent Wizard (for existing lines)'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Serial Number'),
    }
    _defaults = {
        'quantity': 1.0,
    }

    def onchange_lot_id(self, cr, uid, ids, prodlot_id=False, product_qty=False,
                        loc_id=False, product_id=False, uom_id=False, context=None):
        return self.pool.get('stock.move').onchange_lot_id(cr, uid, [], prodlot_id, product_qty,
                                                           loc_id, product_id, uom_id, context)


class stock_inventory_line_recu(osv.osv_memory):
    _inherit = "stock.move.recu"
    _name = "stock.inventory.line.recu"
    _description = "Productos Recuperados Lineas de Inventario"

    _columns = {
        'line_ids': fields.one2many('stock.inventory.line.recu.lines', 'wizard_id', 'Serial Numbers'),
        'line_exist_ids': fields.one2many('stock.inventory.line.recu.lines', 'wizard_exist_id', 'Serial Numbers'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False)
        res = {}
        line = self.pool.get('stock.inventory.line').browse(cr, uid, record_id, context=context)
        if 'product_id' in fields:
            res.update({'product_id': line.product_id.id})
        if 'product_uom' in fields:
            res.update({'product_uom': line.product_uom.id})
        if 'qty' in fields:
            res.update({'qty': line.product_qty})
        return res

    def split(self, cr, uid, ids, line_ids, context=None):
        """ To split stock inventory lines according to serial numbers.

        :param line_ids: the ID or list of IDs of inventory lines we want to split
        """
        if context is None:
            context = {}
        assert context.get('active_model') == 'stock.inventory.line', \
            'Incorrect use of the inventory line split wizard.'
        prodlot_obj = self.pool.get('stock.production.lot')
        ir_sequence_obj = self.pool.get('ir.sequence')
        line_obj = self.pool.get('stock.inventory.line')
        new_line = []
        for data in self.browse(cr, uid, ids, context=context):
            for inv_line in line_obj.browse(cr, uid, line_ids, context=context):
                line_qty = inv_line.product_qty
                quantity_rest = inv_line.product_qty
                new_line = []
                if data.use_exist:
                    lines = [l for l in data.line_exist_ids if l]
                else:
                    lines = [l for l in data.line_ids if l]
                for line in lines:
                    quantity = line.quantity
                    if quantity <= 0 or line_qty == 0:
                        continue
                    quantity_rest -= quantity
                    if quantity_rest < 0:
                        quantity_rest = quantity
                        break
                    default_val = {
                        'product_qty': quantity,
                    }
                    if quantity_rest > 0:
                        current_line = line_obj.copy(cr, uid, inv_line.id, default_val)
                        new_line.append(current_line)
                    if quantity_rest == 0:
                        current_line = inv_line.id
                    prodlot_id = False
                    if data.use_exist:
                        prodlot_id = line.prodlot_id.id
                    if not prodlot_id:
                        prodlot_id = prodlot_obj.create(cr, uid, {
                            'name': line.name,
                            'product_id': inv_line.product_id.id},
                                                        context=context)
                    line_obj.write(cr, uid, [current_line], {'prod_lot_id': prodlot_id})
                    prodlot = prodlot_obj.browse(cr, uid, prodlot_id)

                    update_val = {}
                    if quantity_rest > 0:
                        update_val['product_qty'] = quantity_rest
                        line_obj.write(cr, uid, [inv_line.id], update_val)

        return new_line


class stock_inventory_recu_lines(osv.osv_memory):
    _inherit = "stock.move.recu.lines"
    _name = "stock.inventory.line.recu.lines"
    _description = "Inventario Productos Recuperados"
    _columns = {
        'wizard_id': fields.many2one('stock.inventory.line.recu', 'Parent Wizard'),
        'wizard_exist_id': fields.many2one('stock.inventory.line.recu', 'Parent Wizard'),
    }
