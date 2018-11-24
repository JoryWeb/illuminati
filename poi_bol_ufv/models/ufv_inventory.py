# © 2018 Miguel Angel Callisaya Mamani
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3


from odoo import models, fields, exceptions, api, _
from odoo.exceptions import UserError

STATE = [
    ('draft', 'Borrador'),
    ('calculated', 'Calculado'),
    ('cancel', 'Cancelado'),
    ('done', 'Contabilizado'),
]


class PoiUfvInventory(models.Model):
    _name = "poi.ufv.inventory"
    _description = "Plan Anual de Ventas"
    _order = 'name desc'

    name = fields.Char(string='Distribution number', required=True,
                       select=True, default='/')

    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=(lambda self: self.env['res.company']._company_default_get(
            'poi.ufv.inventory')), readonly=True, states={'draft': [('readonly', False)]})

    state = fields.Selection(STATE, string='Status', readonly=True, default='draft')
    date = fields.Date(string='Fecha', required=True, readonly=True, select=True,
                       states={'draft': [('readonly', False)]},
                       default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', string='Creador', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)
    journal_id = fields.Many2one('account.journal', string="Diario")
    account_move_id = fields.Many2one(
        'account.move', 'Asiento Contable',
        copy=False, readonly=True)
    product_id = fields.Many2one('product.product', string=u"Item Valoración")

    date_revisado = fields.Date("Fecha Revisado")
    ufv_inicial = fields.Float(string='UFV Inicial', readonly=True, default=0, states={'draft': [('readonly', False)]})
    ufv_final = fields.Float(string='UFV Final', readonly=True, default=0, states={'draft': [('readonly', False)]})
    note = fields.Text("Notas")
    product_lines = fields.One2many(
        comodel_name='poi.ufv.inventory.line', ondelete="cascade",
        inverse_name='ufv_line', string='Lineas a Valorar')

    @api.onchange('date')
    def onchange_date(self):
        currency = self.env['res.currency'].search([('name', '=', 'UFV')])
        # Considerar la 4 horas de difenrencia
        if currency:
            sql_query = """SELECT t0.rate from res_currency_rate t0
                                                   WHERE t0.currency_id = %s
                                                   AND (t0.name + INTERVAL '4 hours')::timestamp::date = %s::timestamp::date
                                                    """
            params = (currency.id, self.date)
            self.env.cr.execute(sql_query, params)
            results = self.env.cr.fetchall()
            rate = 0
            for res in results:
                rate = res[0]
            self.ufv_final = rate

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('poi.ufv.inventory')
        res_id = super(PoiUfvInventory, self).create(vals)
        return res_id

    @api.one
    def action_done(self):
        for line in self.cost_lines:
            if self.cost_update_type == 'direct':
                line.move_id.quant_ids._price_update(line.standard_price_new)
                self._product_price_update(
                    line.move_id, line.standard_price_new)
                line.move_id.product_price_update_after_done()
        self.state = 'done'

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def import_stock(self):
        if self.ufv_final <= 0:
            raise UserError(_('Debe actualizar el valor UFV de la fecha %s.') % (self.date))
        self.product_lines.unlink()
        lines = self.product_lines.browse([])
        self.ensure_one()
        domain = [('remaining_qty', '>', 0.0)] + self.env['stock.move']._get_in_base_domain()
        candidates = self.env['stock.move'].search(domain, order='date, id')
        for candidate in candidates:
            value_line = {
                'ufv_final': self.ufv_final,
                'ufv_inicial': self.get_ufv_date(candidate.product_id.id, candidate),
                'date_purchase': candidate.date,
                'product_id': candidate.product_id.id,
                'move_id': candidate.id,
                'location_id': candidate.location_dest_id.id,
                'qty': candidate.remaining_qty,
                'method': candidate.product_id.cost_method,
                'price_unit': candidate.remaining_value / candidate.remaining_qty,
                'cost_total': candidate.remaining_value,
            }
            lines += lines.new(value_line)

        self.product_lines = lines
        self.state = 'calculated'
        return True

    @api.one
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def get_ufv_date(self, product_id, move_id):
        poi_ufv = self.env['poi.ufv.inventory.line'].search(
            [('product_id', '=', product_id), ('ufv_line.state', '=', 'done')], order='date_purchase DESC', limit=1)
        if poi_ufv:
            # En caso de existir una valoración ya realizada procedemos a utilizar ese valor de UFV en esa fecha
            return poi_ufv.ufv_final
        else:
            # Ubicar la primera fecha de movimiento realizado en funcion de la compra
            move = self.env['stock.move'].search([('product_id', '=', product_id), ('state', '=', 'done')],
                                                 order='date ASC', limit=1)
            currency = self.env['res.currency'].search([('name', '=', 'UFV')])
            # Considerar la 4 horas de difenrencia
            sql_query = """SELECT t0.rate from res_currency_rate t0
                                       WHERE t0.currency_id = %s
                                       AND (t0.name + INTERVAL '4 hours')::timestamp::date = %s::timestamp::date
                                        """
            params = (currency.id, move_id.date)
            self.env.cr.execute(sql_query, params)
            results = self.env.cr.fetchall()
            rate = 0
            for res in results:
                rate = res[0]
            return rate

    @api.multi
    def apply_ufv_cost(self):
        if not self.journal_id:
            raise UserError(_('Por favor definir el diario contable'))
        if not self.product_id:
            raise UserError(_('Por favor definir el producto de Costeo'))
        # Por cada linea que tenga un costo Real se generara un Landed Costo de Actualización
        move = self.env['account.move']
        move_vals = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'ref': self.name,
            'line_ids': [],
        }
        move_id = move.create(move_vals)
        total_asiento = 0.0
        for line in self.product_lines:
            # if line.method == 'real':
            cost_to_add = (line.move_id.remaining_qty / line.move_id.product_qty) * line.amount_adjustment
            new_ufv_cost_value = line.move_id.ufv_cost_value + line.amount_adjustment
            line.move_id.write({
                'ufv_cost_value': new_ufv_cost_value,
                'value': line.move_id.value + cost_to_add,
                'remaining_value': line.move_id.remaining_value + cost_to_add,
                'price_unit': (line.move_id.value + new_ufv_cost_value) / line.move_id.product_qty,
            })
            # else:
            # Actualizar Costo Unitario
            #    line.product_id.sudo().write({'standard_price': line.new_price})
            #    move_id = self._create_account_move()
            #    self._create_accounting_entries(line, move_id, self.product_id)
            # move_vals['line_ids'] += line._create_accounting_entries(move, 0)
            # Actualisamos las lineas de asiento contable con
            # inserts para tenerlo generado
            total_asiento = total_asiento + line.amount_adjustment
            move_line = line._create_accounting_entries(move, 0)
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
                mov_l['company_currency_id'] = self.company_id.currency_id.id
                mov_l['ref'] = line.move_id.name + ' UFV'
                mov_l['journal_id'] = self.journal_id.id
                mov_l['blocked'] = False
                mov_l['date'] = self.date
                mov_l['company_id'] = self.company_id.id
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

            line.state = 'done'

        self.write({'state': 'done', 'account_move_id': move_id.id})
        move_id.amount = total_asiento
        move_id.post()


class PoiUfvInventoryLine(models.Model):
    _name = "poi.ufv.inventory.line"
    _description = "Lineas de Plan anual"

    @api.one
    @api.depends('qty', 'cost_total_ufv')
    def _compute_ufv_line(self):
        self.price_unit_ufv = self.cost_total_ufv / self.qty

    @api.one
    @api.depends('price_unit_ufv', 'cost_total_ufv')
    def _compute_ufv_total(self):
        if self.ufv_inicial != 0:
            self.cost_total_ufv = self.cost_total * (self.ufv_final / self.ufv_inicial)
        else:
            self.cost_total_ufv = 0.0

    @api.one
    @api.depends('cost_total_ufv', 'qty')
    def _compute_ufv_price_unit(self):
        if self.qty > 0:
            self.amount_adjustment = self.cost_total_ufv - self.cost_total
        else:
            self.amount_adjustment = 0

    name = fields.Char(string=u'Nombre')
    ufv_line = fields.Many2one(
        comodel_name='poi.ufv.inventory', string='UFV',
        ondelete='cascade', required=True)
    state = fields.Selection(STATE, string='Estado', readonly=True, default='draft')
    ufv_inicial = fields.Float(string='UFV Inicial')
    ufv_final = fields.Float(string='UFV Final')
    product_id = fields.Many2one("product.product", string=u"Product")
    move_id = fields.Many2one("stock.move", string=u"Movimiento")
    move_line_id = fields.Many2one("stock.move.line", string=u"Linea - Lote")
    lot_id = fields.Many2one("stock.production.lot", string=u"Lote")
    location_id = fields.Many2one("stock.location", string=u"Ubicación")
    method = fields.Char(string="Metodo")
    date_purchase = fields.Date(string="Fecha Compra")
    qty = fields.Float(string='Cantidad')
    price_unit = fields.Float(string='Costo Unitario')
    cost_total = fields.Float(string='Costo sin Ajuste')
    cost_total_ufv = fields.Float(string=u'Valor Actualizado', compute=_compute_ufv_total)
    amount_adjustment = fields.Float(string='Ajuste', compute=_compute_ufv_price_unit)
    price_unit_ufv = fields.Float(string=u'Costo Unitario Reposición', compute=_compute_ufv_line)

    def _create_accounting_entries(self, move, qty_out=0):
        # TDE CLEANME: product chosen for computation ?
        cost_product = self.ufv_line.product_id
        if not cost_product:
            return False
        accounts = self.product_id.product_tmpl_id.get_product_accounts()
        debit_account_id = accounts.get('stock_valuation') and accounts['stock_valuation'].id or False
        already_out_account_id = accounts['stock_output'].id
        credit_account_id = cost_product.property_account_expense_id.id or cost_product.categ_id.property_account_expense_categ_id.id

        if not credit_account_id:
            raise UserError(_('Please configure Stock Expense Account for product: %s.') % (cost_product.name))

        return self._create_account_move_line(move, credit_account_id, debit_account_id, qty_out,
                                              already_out_account_id)

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        """
        Generar las lineas de asiento contable para los valores UFV
        """
        AccountMoveLine = []

        base_line = {
            'name': self.ufv_line.name,
            'product_id': self.product_id.id,
            'quantity': 0,
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        diff = self.amount_adjustment
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
