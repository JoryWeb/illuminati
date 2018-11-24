# © 2013 Joaquín Gutierrez
# © 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, models, fields, _
from odoo.exceptions import UserError

# Para posible contabilidad en transito
class StockLocation(models.Model):
    _inherit = 'stock.location'
    account_import = fields.Boolean("Contabilidad en Transito")
    valuation_in_account_transit_id = fields.Many2one("account.account", string="Cuenta Entrada Transito",
                                                      domain=[('internal_type', '=', 'other'),
                                                              ('deprecated', '=', False)])
    valuation_out_account_transito_id = fields.Many2one("account.account", string="Cuenta Salida Transito",
                                                        domain=[('internal_type', '=', 'other'),
                                                                ('deprecated', '=', False)])


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _is_internal(self):
        """ Check if the move should be considered as entering the company so that the cost method
        will be able to apply the correct logic.

        :return: True if the move is entering the company else False
        """
        for move_line in self.move_line_ids.filtered(lambda ml: not ml.owner_id):
            if move_line.location_id.usage in ('internal', 'transit') and move_line.location_dest_id.usage in (
            'internal', 'transit'):
                return True
        return False

    # Es necesario evaluar el costo de precio unitario
    # del movimiento origen
    @api.multi
    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        val = super(StockMove, self)._get_price_unit()
        if self.move_orig_ids:
            for move_or in self.move_orig_ids:
                # actualizamos el socio para poder coster movimientos internos
                if not self.picking_id.partner_id:
                    self.picking_id.partner_id = move_or.picking_id.partner_id.id
                if move_or.purchase_line_id:
                    val = move_or.price_unit
                else:
                    val = abs(move_or.price_unit)
        return val

    @api.model
    def _run_fifo(self, move, quantity=None):
        """ Opciones de valor fifo
        - Refactorización, al tratarse de movimientos internos el
        sistema visualiza todos los disponibles sin evaluar el origen
        se trata de obtener solo los movimientos disponibles para
        efectuar las transferencias de almacén

        :param quantity: quantity to value instead of `move.product_qty`
        :returns: valued amount in absolute
        """
        move.ensure_one()

        # Deal with possible move lines that do not impact the valuation.
        valued_move_lines = move.move_line_ids.filtered(lambda
                                                            ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
        valued_quantity = 0
        for valued_move_line in valued_move_lines:
            valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                 move.product_id.uom_id)

        # Find back incoming stock moves (called candidates here) to value this move.
        qty_to_take_on_candidates = quantity or valued_quantity
        # Los candidatos sera reevaluados para obtener solo los de la ubicación origen en caso de transferencias internas
        # y salidas de almacen
        if move.product_id.tracking == 'serial':
            lot_id = False
            for lines in move.move_line_ids:
                lot_id = lines.lot_id.id
            candidates = move.product_id._get_fifo_candidates_in_move_location_lot(move.location_id.id, lot_id)
        else:
            candidates = move.product_id._get_fifo_candidates_in_move_location(move.location_id.id)

        # Es importante para series unicas reservar el del lote seleccionado.

        new_standard_price = 0
        tmp_value = 0  # to accumulate the value taken on the candidates
        for candidate in candidates:
            new_standard_price = candidate.price_unit
            if candidate.remaining_qty <= qty_to_take_on_candidates:
                qty_taken_on_candidate = candidate.remaining_qty
            else:
                qty_taken_on_candidate = qty_to_take_on_candidates

            # As applying a landed cost do not update the unit price, naivelly doing
            # something like qty_taken_on_candidate * candidate.price_unit won't make
            # the additional value brought by the landed cost go away.
            candidate_price_unit = candidate.remaining_value / candidate.remaining_qty
            value_taken_on_candidate = qty_taken_on_candidate * candidate_price_unit
            candidate_vals = {
                'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                'remaining_value': candidate.remaining_value - value_taken_on_candidate,
            }
            candidate.write(candidate_vals)

            qty_to_take_on_candidates -= qty_taken_on_candidate
            tmp_value += value_taken_on_candidate
            if qty_to_take_on_candidates == 0:
                break

        # Update the standard price with the price of the last used candidate, if any.
        if new_standard_price and move.product_id.cost_method == 'fifo':
            move.product_id.sudo().standard_price = new_standard_price

        # If there's still quantity to value but we're out of candidates, we fall in the
        # negative stock use case. We chose to value the out move at the price of the
        # last out and a correction entry will be made once `_fifo_vacuum` is called.
        if qty_to_take_on_candidates == 0:
            move.write({
                'value': -tmp_value if not quantity else move.value or -tmp_value,
                # outgoing move are valued negatively
                'price_unit': -tmp_value / move.product_qty,
            })
        elif qty_to_take_on_candidates > 0:
            last_fifo_price = new_standard_price or move.product_id.standard_price
            negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
            tmp_value += abs(negative_stock_value)
            vals = {
                'remaining_qty': move.remaining_qty + -qty_to_take_on_candidates,
                'remaining_value': move.remaining_value + negative_stock_value,
                'value': -tmp_value,
                'price_unit': -1 * last_fifo_price,
            }
            move.write(vals)
        return tmp_value

    @api.multi
    def _get_accounting_data_for_valuation(self):
        """ Aplicable al modulo de importaciones separar las cuentas contables en inventarios por cuenta de importaciones """
        journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        if self.location_id.valuation_out_account_id:
            acc_src = self.location_id.valuation_out_account_id.id
        elif self.purchase_line_id.order_id.tipo_fac == '3':
            acc_src = accounts_data['import_stock_input'].id
            if not acc_src:
                raise UserError(_('Debe definir la cuenta de importaciones en la categoría del producto'))

        return journal_id, acc_src, acc_dest, acc_valuation

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        """
        Se requiere obtener el costo actualizado por numero de serie
        unico para el momento de la venta
        """
        # solo aplicable a productos con serie unica
        if self.product_id.tracking == 'serial':
            lot_name = ''
            for lines in self.move_line_ids:
                lot_name = lines.lot_id.name

            # Solo buscamos los costeos internos
            move_lines = self.env['stock.move.line'].search([('lot_name', '=', lot_name)])
            for lines in move_lines:
                if cost >= 0:
                    cost = cost + lines.landed_value
                else:
                    cost = cost - lines.landed_value
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        return res
