# © 2013 Joaquín Gutierrez
# © 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

from odoo import api, fields, models, _
from odoo.exceptions import UserError
class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def _create_accounting_entries(self, cr, uid, line, move_id, qty_out, context=None):
        product_obj = self.pool.get('product.template')
        cost_product = line.cost_line_id and line.cost_line_id.product_id
        if not cost_product:
            return False
        accounts = product_obj.browse(cr, uid, line.product_id.product_tmpl_id.id, context=context).get_product_accounts()
        debit_account_id = accounts.get('stock_valuation', False) and accounts['stock_valuation'].id or False
        already_out_account_id = accounts['stock_output'].id
        credit_account_id = line.cost_line_id.account_id.id or cost_product.property_account_expense_id.id or cost_product.categ_id.property_account_expense_categ_id.id
        if not credit_account_id:
            raise UserError(_('Please configure Stock Expense Account for product: %s.') % (cost_product.name))
        lin = self._create_account_move_line(cr, uid, line, move_id, credit_account_id, debit_account_id, qty_out, already_out_account_id, context=context)
        if qty_out == 0:
            if line.quant_id.product_id.tracking == 'serial':
                # Verificar si esta asignado a una factura
                invoice_line = self.pool.get('account.invoice.line').search(cr,uid, [('lot_id','=', line.quant_id.lot_id.id)], {})
                if invoice_line:
                    base_line = {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                    }
                    if not accounts['stock_outinvoice']:
                        raise UserError(_('Por favor debe definir "Cuenta de Salidas Facturadas" para la contabilidad anglosajona'))
                    debit_line = dict(base_line, account_id=already_out_account_id)
                    credit_line = dict(base_line, account_id=accounts['stock_outinvoice'].id)
                    diff = line.additional_landed_cost
                    if diff > 0:
                        debit_line['debit'] = diff
                        credit_line['credit'] = diff
                    else:
                        # negative cost, reverse the entry
                        debit_line['credit'] = -diff
                        credit_line['debit'] = -diff
                    lin.append(debit_line)
                    lin.append(credit_line)

            elif line.move_id.product_id.tracking == 'serial':
                if line.move_id.restrict_lot_id:
                    invoice_line = self.pool.get('account.invoice.line').search(cr, uid,
                                                                                [('lot_id', '=', line.move_id.restrict_lot_id.id)],
                                                                                {})
                    if invoice_line:
                        base_line = {
                            'name': line.name,
                            'product_id': line.product_id.id,
                            'quantity': line.quantity,
                        }
                        if not accounts['stock_outinvoice']:
                            raise UserError(_(
                                'Por favor debe definir "Cuenta de Salidas Facturadas" para la contabilidad anglosajona'))
                        debit_line = dict(base_line, account_id=already_out_account_id)
                        credit_line = dict(base_line, account_id=accounts['stock_outinvoice'].id)
                        diff = line.additional_landed_cost
                        if diff > 0:
                            debit_line['debit'] = diff
                            credit_line['credit'] = diff
                        else:
                            # negative cost, reverse the entry
                            debit_line['credit'] = -diff
                            credit_line['debit'] = -diff
                        lin.append(debit_line)
                        lin.append(credit_line)

        return lin