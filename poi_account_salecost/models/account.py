
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    def get_invoice_line_account(self, type, product, fpos, company):
        # POI: Copia de la función nativa padre, quitando la referencia 'anglo_saxon_accounting' del if (además de sólo in_refund)
        if type in ('in_refund') and product and product.type in ('consu', 'product'):
            if product.tracking == 'serial':
                accounts = product.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)
                if accounts['stock_outinvoice']:
                    return accounts['stock_outinvoice']
        return super(AccountInvoiceLine, self).get_invoice_line_account(type, product, fpos, company)

    @api.model
    def _get_anglo_saxon_price_unit(self):
        self.ensure_one()
        lot = False
        for lines in self.sale_line_ids:
            lot = lines.lot_id
        if lot:
            move_line = self.env['stock.move.line'].search([('lot_name', '=', lot.name)])
            if move_line:
                price = move_line[0].move_id.price_unit + move_line[0].landed_value
            else:
                raise UserError(
                    _('El chasis que trata de facturar no esta aun en inventario'))
        else:
            price = self.product_id.standard_price
        if not self.uom_id or self.product_id.uom_id == self.uom_id:
            return price
        else:
            return self.product_id.uom_id._compute_price(self.product_id.uom_id.id, price, to_uom_id=self.uom_id.id)

    @api.model
    def compute_quant_ufv(self, quant):

        if quant.location_id.usage in ('transit'):
            raise UserError(
                _('La unidad que trata de facturar esta en una ubicación de Transito'))

        poi_ufv = self.env['poi.ufv.inventory.line'].search(
            [('product_id', '=', quant.product_id.id), ('ufv_line.state', '=', 'done')], order='date DESC', limit=1)
        currency = self.env['res.currency'].search([('name', '=', 'UFV')])
        if poi_ufv:
            # En caso de existir una valoración ya realizada procedemos a utilizar ese valor de UFV en esa fecha
            ufv_inicial = poi_ufv.ufv_final
        else:
            # Ubicar la primera fecha de movimiento realizado
            move = self.env['stock.move'].search([('product_id', '=', quant.product_id.id), ('state', '=', 'done')],
                                                 order='date ASC', limit=1)
            # Considerar la 4 horas de difenrencia
            sql_query = """SELECT t0.rate from res_currency_rate t0
                                               WHERE t0.currency_id = %s
                                               AND (t0.name - INTERVAL '4 hours')::timestamp::date = %s::timestamp::date
                                                """
            params = (currency.id, move.date)
            self.env.cr.execute(sql_query, params)
            results = self.env.cr.fetchall()
            rate = 0
            for res in results:
                rate = res[0]
            ufv_inicial = rate

        # Considerar la 4 horas de difenrencia
        if currency:
            sql_query = """SELECT t0.rate from res_currency_rate t0
                                                           WHERE t0.currency_id = %s
                                                           AND (t0.name - INTERVAL '4 hours')::timestamp::date = %s::timestamp::date
                                                            """
            params = (currency.id, self.invoice_id.date_invoice)
            self.env.cr.execute(sql_query, params)
            results = self.env.cr.fetchall()
            rate = 0
            for res in results:
                rate = res[0]
            ufv_final = rate

        debit_account_id = quant.product_id.categ_id.property_stock_valuation_account_id.id
        credit_account_id = quant.product_id.property_stock_account_output_ufv.id
        jornal_id = quant.product_id.categ_id.property_stock_journal.id
        cost_quant = quant.cost
        val_increment = (ufv_final/ufv_inicial) * cost_quant
        diff = val_increment - quant.cost
        self._create_account_move_line_ufv(quant.qty, diff, credit_account_id, debit_account_id, jornal_id)
        quant.cost = val_increment

    @api.model
    def _create_account_move_line_ufv(self, qty, cost, credit_account_id, debit_account_id, journal_id):

        AccountMove = self.env['account.move']
        move_lines = self._prepare_account_move_line_ufv(qty, cost, credit_account_id, debit_account_id)
        if move_lines:
            date = self.invoice_id.date_invoice
            new_account_move = AccountMove.create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': 'AJUSTE UFV CHASIS'})
            new_account_move.post()

    @api.model
    def _prepare_account_move_line_ufv(self, qty, cost, credit_account_id, debit_account_id):
        """
        Generar asiento contable por saldo calculado en transacción UFV

        """
        self.ensure_one()
        valuation_amount = cost
        debit_value = self.company_id.currency_id.round(valuation_amount * qty)
        credit_value = debit_value

        partner_id = self.invoice_id.partner_id.id
        debit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.invoice_id.origin,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': debit_account_id,
        }
        credit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.invoice_id.origin,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id': credit_account_id,
        }
        res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        return res

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice,self).invoice_line_move_line_get()
        # POI: Copia de la función nativa padre, quitando la referencia 'anglo_saxon_accounting' del if
        if self.type in ('out_invoice','out_refund'):
            for i_line in self.invoice_line_ids:
                if i_line.product_id.tracking == 'serial':
                    res_add = self._anglo_saxon_sale_move_lines(i_line)
                    # Además cambiar la cuenta de 'stock_output' por la parametrización de este módulo 'stock_outinvoice'
                    fpos = i_line.invoice_id.fiscal_position_id
                    accounts = i_line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)
                    if not accounts['stock_outinvoice']:
                        raise UserError(_('Por favor debe definir "Cuenta de Salidas Facturadas" para la contabilidad anglosajona'))
                        #res.extend(res_add)
                        #return res
                    dacc = accounts['stock_outinvoice'].id
                    for add in res_add:
                        if add['price'] > 0:
                            add['account_id'] = dacc
                        elif add['price'] < 0:
                            add['account_id'] = accounts['stock_output'].id
                    res.extend(res_add)
        return res

class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.cr_uid_context
    def _get_accounting_data_for_valuation(self, cr, uid, move, context=None):
        journal_id, acc_src, acc_dest, acc_valuation = super(StockQuant, self)._get_accounting_data_for_valuation(cr, uid, move, context=context)

        #POI: En caso de salida a Cliente usar la cuenta de parametrización de este módulo 'stock_outinvoice'
        if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'customer':
            if move.product_id.tracking == 'serial':
                product_obj = self.pool.get('product.template')
                accounts = product_obj.browse(cr, uid, move.product_id.product_tmpl_id.id, context).get_product_accounts()
                if accounts['stock_outinvoice']:
                    acc_dest = accounts['stock_outinvoice'].id
                else:
                    raise UserError(
                        _('Por favor debe definir "Cuenta de Salidas Facturadas" para la contabilidad anglosajona'))

        return journal_id, acc_src, acc_dest, acc_valuation