# © 2013 Joaquín Gutierrez
# © 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
import odoo.addons.decimal_precision as dp
from odoo import SUPERUSER_ID

class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'
    quant_ids = fields.Many2many('stock.quant', 'landed_quant_rel', 'quant_id', 'landed_id', string='Quants')
    move_line_ids = fields.Many2many('stock.move.line', 'landed_moveline_rel', 'move_id', 'landed_id', string='Series')
    name = fields.Char('Coste en destino', required=True, index=True, copy=False, default='Nuevo')
    #Mejora de secuencia en landed cost
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.landed.cost') or '/'
        return super(StockLandedCost, self).create(vals)

    def get_valuation_lines_moves(self):
        lines = []

        for move in self.mapped('move_line_ids'):
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            if move.product_id.valuation != 'real_time' or move.product_id.cost_method != 'fifo':
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_line_id': move.id,
                'quantity': move.qty_done,
                'former_cost': move.move_id.price_unit,
                'weight': move.product_id.weight * move.qty_done,
                'volume': move.product_id.volume * move.qty_done
            }
            lines.append(vals)

        if not lines and self.mapped('move_line_ids'):
            raise UserError(_(
                'Debe seleccionar series para validar'))
        return lines


    #Aplicar Calculo de costos
    @api.multi
    def compute_landed_cost_moves(self):
        line_obj = self.env['stock.valuation.adjustment.lines']
        line_obj.search([('cost_id', 'in', [self.id])]).unlink()
        digits = dp.get_precision('Product Price')(self._cr)
        towrite_dict = {}
        for cost in self:
            if not cost.move_line_ids:
                continue
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            vals = self.get_valuation_lines_moves()
            for v in vals:
                for line in cost.cost_lines:
                    v.update({'cost_id': cost.id, 'cost_line_id': line.id})
                    self.env['stock.valuation.adjustment.lines'].create(v)
                total_qty += v.get('quantity', 0.0)
                total_cost += v.get('former_cost', 0.0)
                total_weight += v.get('weight', 0.0)
                total_volume += v.get('volume', 0.0)
                total_line += 1

            for line in cost.cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        else:
                            value = (line.price_unit / total_line)

                        if digits:
                            value = float_round(value, precision_digits=digits[1], rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        if towrite_dict:
            for key, value in towrite_dict.items():
                line_data = line_obj.browse(key)
                line_data.write({'additional_landed_cost': value})
        return True

    #Funcion que valora uno o varios lotes chasis seleccionados
    @api.multi
    def button_validate_moves(self):
        if any(cost.state != 'draft' for cost in self):
            raise UserError(_('Only draft landed costs can be validated'))
        if any(not cost.valuation_adjustment_lines for cost in self):
            raise UserError(_('No valuation adjustments lines. You should maybe recompute the landed costs.'))
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))


        for cost in self:
            for move_line in cost.move_line_ids:
                if not move_line.lot_id.location_id.usage == 'internal':
                    raise UserError(
                        _('Solo puede registrar costos cuando la unidad este en una ubicación interna de la empresa'))
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
            }
            move_id = move.create(move_vals)
            total_asiento = 0.0
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_line_id):
                # Solo podemos asignar los costes en destino a las lineas de movimiento
                #cost_to_add = line.move_line_id.qty_done * line.additional_landed_cost

                new_landed_cost_value = line.move_line_id.landed_value + line.additional_landed_cost
                line.move_line_id.write({
                    'landed_value': new_landed_cost_value
                })
                total_asiento = total_asiento + line.additional_landed_cost
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                #move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)
                move_line = line._create_accounting_entries(move, qty_out)
                for mov_l in move_line:
                    mov_l['move_id'] = move_id.id
                    mov_l['date_maturity'] = self.date
                    mov_l['product_id'] = line.product_id.id
                    if 'debit' in mov_l:
                        mov_l['balance'] = mov_l['debit']
                        mov_l['debit_cash_basis'] = mov_l['debit']
                        mov_l['credit_cash_basis'] = 0
                        mov_l['balance_cash_basis'] = mov_l['debit']
                        mov_l['amount_currency'] = 0
                        mov_l['is_debit'] = 1
                    if 'credit' in mov_l:
                        mov_l['balance'] = mov_l['credit'] * (-1)
                        mov_l['credit_cash_basis'] = mov_l['credit']
                        mov_l['debit_cash_basis'] = 0
                        mov_l['balance_cash_basis'] = mov_l['credit'] * (-1)
                        mov_l['amount_currency'] = 0
                        mov_l['is_debit'] = 0
                    mov_l['company_currency_id'] = self.account_journal_id.company_id.currency_id.id
                    mov_l['ref'] = self.name
                    mov_l['journal_id'] = self.account_journal_id.id
                    mov_l['blocked'] = False
                    mov_l['date'] = self.date
                    mov_l['company_id'] = self.account_journal_id.company_id.id
                    account_obj = self.env['account.account'].browse(mov_l['account_id'])
                    mov_l['user_type_id'] = account_obj.user_type_id.id
                    mov_l['tax_exigible'] = True
                    mov_l['create_uid'] = self._uid
                    mov_l['write_uid'] = self._uid
                    mov_l['create_date'] = fields.Datetime.now()
                    mov_l['write_date'] = fields.Datetime.now()
                    cursor = self._cr
                    keys = mov_l.keys()
                    columns = ','.join(keys)
                    values = ','.join(['%({})s'.format(k) for k in keys])
                    insert = 'insert into account_move_line ({0}) values ({1})'.format(columns, values)
                    cursor.execute(cursor.mogrify(insert, mov_l))

            #move = move.create(move_vals)
            #cost.write({'state': 'done', 'account_move_id': move.id})
            #move.post()
            cost.write({'state': 'done', 'account_move_id': move_id.id})
            move_id.amount = total_asiento
            move_id.post()
        return True

    # Mejoramos la velocidad de creacion de asiento contable evitando el ORM
    @api.multi
    def button_validate(self):
        if any(cost.state != 'draft' for cost in self):
            raise UserError(_('Only draft landed costs can be validated'))
        if any(not cost.valuation_adjustment_lines for cost in self):
            raise UserError(_('No valuation adjustments lines. You should maybe recompute the landed costs.'))
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            for pick in cost.picking_ids:
                if not pick.location_dest_id.usage == 'internal':
                    raise UserError(
                        _('Solo puede registrar costos cuando la mercadería ingrese a una ubicación interna de la empresa'))
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
            }
            move_id = move.create(move_vals)
            total_asiento = 0.0
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                # Prorate the value at what's still in stock
                cost_to_add = (line.move_id.remaining_qty / line.move_id.product_qty) * line.additional_landed_cost

                new_landed_cost_value = line.move_id.landed_cost_value + line.additional_landed_cost
                line.move_id.write({
                    'landed_cost_value': new_landed_cost_value,
                    'value': line.move_id.value + cost_to_add,
                    'remaining_value': line.move_id.remaining_value + cost_to_add,
                    'price_unit': (line.move_id.value + new_landed_cost_value) / line.move_id.product_qty,
                })
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                if line.move_id._is_in():
                    qty_out = line.move_id.product_qty - line.move_id.remaining_qty
                elif line.move_id._is_out():
                    qty_out = line.move_id.product_qty
                #move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)
                total_asiento = total_asiento + line.additional_landed_cost
                move_line = line._create_accounting_entries(move, qty_out)
                for mov_l in move_line:
                    mov_l['move_id'] = move_id.id
                    mov_l['date_maturity'] = self.date
                    mov_l['product_id'] = line.product_id.id
                    if 'debit' in mov_l:
                        mov_l['balance'] = mov_l['debit']
                        mov_l['debit_cash_basis'] = mov_l['debit']
                        mov_l['credit_cash_basis'] = 0
                        mov_l['balance_cash_basis'] = mov_l['debit']
                        mov_l['amount_currency'] = 0
                        mov_l['is_debit'] = 1
                    if 'credit' in mov_l:
                        mov_l['balance'] = mov_l['credit'] * (-1)
                        mov_l['credit_cash_basis'] = mov_l['credit']
                        mov_l['debit_cash_basis'] = 0
                        mov_l['balance_cash_basis'] = mov_l['credit'] * (-1)
                        mov_l['amount_currency'] = 0
                        mov_l['is_debit'] = 0
                    mov_l['company_currency_id'] = self.account_journal_id.company_id.currency_id.id
                    mov_l['ref'] = self.name
                    mov_l['journal_id'] = self.account_journal_id.id
                    mov_l['blocked'] = False
                    mov_l['date'] = self.date
                    mov_l['company_id'] = self.account_journal_id.company_id.id
                    account_obj = self.env['account.account'].browse(mov_l['account_id'])
                    mov_l['user_type_id'] = account_obj.user_type_id.id
                    mov_l['tax_exigible'] = True
                    mov_l['create_uid'] = self._uid
                    mov_l['write_uid'] = self._uid
                    mov_l['create_date'] = fields.Datetime.now()
                    mov_l['write_date'] = fields.Datetime.now()
                    cursor = self._cr
                    keys = mov_l.keys()
                    columns = ','.join(keys)
                    values = ','.join(['%({})s'.format(k) for k in keys])
                    insert = 'insert into account_move_line ({0}) values ({1})'.format(columns, values)
                    cursor.execute(cursor.mogrify(insert, mov_l))
            #move = move.create(move_vals)
            cost.write({'state': 'done', 'account_move_id': move_id.id})
            move_id.amount = total_asiento
            move_id.post()
        return True

class StockValuationAdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'
    move_line_id = fields.Many2one('stock.move.line', string='Series')
    weight = fields.Float(string='Peso', digits=dp.get_precision('Stock Weight'),
                                          help="Peso calculado")

    def _create_accounting_entries(self, move, qty_out):
        # TDE CLEANME: product chosen for computation ?
        cost_product = self.cost_line_id.product_id
        if not cost_product:
            return False
        accounts = self.product_id.product_tmpl_id.get_product_accounts()
        debit_account_id = accounts.get('stock_valuation') and accounts['stock_valuation'].id or False
        already_out_account_id = accounts['stock_output'].id
        credit_account_id = self.cost_line_id.account_id.id or cost_product.property_account_expense_id.id or cost_product.categ_id.property_account_expense_categ_id.id

        if not credit_account_id:
            raise UserError(_('Please configure Stock Expense Account for product: %s.') % (cost_product.name))

        return self._create_account_move_line(move, credit_account_id, debit_account_id, qty_out,
                                              already_out_account_id)

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        AccountMoveLine = []

        base_line = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': 0,
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        diff = self.additional_landed_cost
        if diff > 0:
            debit_line['debit'] = diff
            credit_line['credit'] = diff
        else:
            # negative cost, reverse the entry
            debit_line['credit'] = -diff
            credit_line['debit'] = -diff
        AccountMoveLine.append(debit_line)
        AccountMoveLine.append(credit_line)

        # Create account move lines for quants already out of stock
        if qty_out > 0:
            debit_line = dict(base_line,
                              name=(self.name + ": " + str(qty_out) + _(' already out')),
                              quantity=0,
                              account_id=already_out_account_id)
            credit_line = dict(base_line,
                               name=(self.name + ": " + str(qty_out) + _(' already out')),
                               quantity=0,
                               account_id=debit_account_id)
            diff = diff * qty_out / self.quantity
            if diff > 0:
                debit_line['debit'] = diff
                credit_line['credit'] = diff
            else:
                # negative cost, reverse the entry
                debit_line['credit'] = -diff
                credit_line['debit'] = -diff
            AccountMoveLine.append(debit_line)
            AccountMoveLine.append(credit_line)

            # TDE FIXME: oh dear
            if self.env.user.company_id.anglo_saxon_accounting:
                debit_line = dict(base_line,
                                  name=(self.name + ": " + str(qty_out) + _(' already out')),
                                  quantity=0,
                                  account_id=credit_account_id)
                credit_line = dict(base_line,
                                   name=(self.name + ": " + str(qty_out) + _(' already out')),
                                   quantity=0,
                                   account_id=already_out_account_id)

                if diff > 0:
                    debit_line['debit'] = diff
                    credit_line['credit'] = diff
                else:
                    # negative cost, reverse the entry
                    debit_line['credit'] = -diff
                    credit_line['debit'] = -diff
                AccountMoveLine.append(debit_line)
                AccountMoveLine.append(credit_line)

        return AccountMoveLine