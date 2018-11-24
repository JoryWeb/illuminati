
from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = "stock.picking"
    move_id = fields.Many2one("account.move", string="Asiento Contable", copy=False)

class StockInventory(models.Model):
    _inherit = "stock.inventory"
    move_id = fields.Many2one("account.move", string="Asiento Contable", copy=False)

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        AccountMove = self.env['account.move']
        quantity = self.env.context.get('forced_quantity', self.product_qty)
        quantity = quantity if self._is_in() else -1 * quantity
        ref = self.picking_id.name
        if self.env.context.get('force_valuation_amount'):
            if self.env.context.get('forced_quantity') == 0:
                ref = 'Revaluation of %s (negative inventory)' % ref
            elif self.env.context.get('forced_quantity') is not None:
                ref = 'Correction of %s (modification of past move)' % ref
        move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value),
                                                                                  credit_account_id, debit_account_id)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            company = self.company_id
            curr_sec_id = company.currency_id_sec
            if not company:
                company = self.env.user.company_id
                curr_sec_id = company.currency_id_sec
            if self.picking_id.move_id or self.inventory_id.move_id:
                if self.picking_id:
                    #self.picking_id.move_id.write({'line_ids': move_lines})
                    for move_l in move_lines:
                        move_data = move_l[2]
                        total_asiento = self.picking_id.move_id.amount

                        if move_data['debit'] > 0:
                            move_data['debit_sec'] = company.currency_id.with_context(date=self.date).compute(move_data['debit'], curr_sec_id)
                            move_data['balance'] = move_data['debit']
                            move_data['debit_cash_basis'] = move_data['debit']
                            move_data['credit_cash_basis'] = 0
                            move_data['balance_cash_basis'] = move_data['debit']
                            move_data['amount_currency'] = 0
                            move_data['is_debit'] = 1
                            total_asiento = total_asiento + move_data['debit']
                            self.picking_id.move_id.amount = total_asiento
                        if move_data['credit'] > 0:
                            move_data['credit_sec'] = company.currency_id.with_context(date=self.date).compute(
                                move_data['credit'], curr_sec_id)
                            move_data['balance'] = move_data['credit'] * (-1)
                            move_data['credit_cash_basis'] = move_data['credit']
                            move_data['debit_cash_basis'] = 0
                            move_data['balance_cash_basis'] = move_data['credit'] * (-1)
                            move_data['amount_currency'] = 0
                            move_data['is_debit'] = 0
                        move_data['move_id'] = self.picking_id.move_id.id
                        move_data['journal_id'] = self.picking_id.move_id.journal_id.id
                        move_data['date_maturity'] = self.date
                        move_data['company_id'] = self.company_id.id
                        move_data['partner_id'] = self.picking_id.move_id.partner_id.id
                        account_obj = self.env['account.account'].browse(move_data['account_id'])
                        move_data['user_type_id'] = account_obj.user_type_id.id
                        move_data['tax_exigible'] = True
                        move_data['create_uid'] = self._uid
                        move_data['write_uid'] = self._uid
                        move_data['create_date'] = fields.Datetime.now()
                        move_data['write_date'] = fields.Datetime.now()
                        cursor = self._cr
                        keys = move_data.keys()
                        columns = ','.join(keys)
                        values = ','.join(['%({})s'.format(k) for k in keys])
                        insert = 'insert into account_move_line ({0}) values ({1})'.format(columns, values)
                        cursor.execute(cursor.mogrify(insert, move_data))
                elif self.inventory_id:
                    for move_l in move_lines:
                        move_data = move_l[2]
                        total_asiento = self.inventory_id.move_id.amount
                        if move_data['debit'] > 0:
                            move_data['debit_sec'] = company.currency_id.with_context(date=self.date).compute(
                                move_data['debit'], curr_sec_id)
                            move_data['balance'] = move_data['debit']
                            move_data['debit_cash_basis'] = move_data['debit']
                            move_data['credit_cash_basis'] = 0
                            move_data['balance_cash_basis'] = move_data['debit']
                            move_data['amount_currency'] = 0
                            move_data['is_debit'] = 1
                            total_asiento = total_asiento + move_data['debit']
                            self.inventory_id.move_id.amount = total_asiento
                        if move_data['credit'] > 0:
                            move_data['credit_sec'] = company.currency_id.with_context(date=self.date).compute(
                                move_data['credit'], curr_sec_id)
                            move_data['balance'] = move_data['credit'] * (-1)
                            move_data['credit_cash_basis'] = move_data['credit']
                            move_data['debit_cash_basis'] = 0
                            move_data['balance_cash_basis'] = move_data['credit'] * (-1)
                            move_data['amount_currency'] = 0
                            move_data['is_debit'] = 0
                        move_data['move_id'] = self.inventory_id.move_id.id
                        move_data['journal_id'] = self.inventory_id.move_id.journal_id.id
                        move_data['date_maturity'] = self.date
                        move_data['company_id'] = self.company_id.id
                        move_data['partner_id'] = self.location_id.company_id.partner_id.id
                        account_obj = self.env['account.account'].browse(move_data['account_id'])
                        move_data['user_type_id'] = account_obj.user_type_id.id
                        move_data['tax_exigible'] = True
                        move_data['create_uid'] = self._uid
                        move_data['write_uid'] = self._uid
                        move_data['create_date'] = fields.Datetime.now()
                        move_data['write_date'] = fields.Datetime.now()
                        cursor = self._cr
                        keys = move_data.keys()
                        columns = ','.join(keys)
                        values = ','.join(['%({})s'.format(k) for k in keys])
                        insert = 'insert into account_move_line ({0}) values ({1})'.format(columns, values)
                        cursor.execute(cursor.mogrify(insert, move_data))
            else:
                new_account_move = AccountMove.sudo().create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': date,
                    'ref': ref,
                    'stock_move_id': self.id,
                })
                if self.picking_id:
                    self.picking_id.move_id = new_account_move.id
                elif self.inventory_id:
                    self.inventory_id.move_id = new_account_move.id
                new_account_move.post()


