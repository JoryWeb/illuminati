##############################################################################
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
from odoo import models, fields, api

SPLIT_METHOD = [
    ('equal', 'Igual'),
    ('by_quantity', 'Por Cantidad'),
    ('by_current_cost_price', 'Por Precio de Coste'),
    ('by_weight', 'Por Peso'),
    ('by_volume', 'Por Volumen'),
]

class ImportInvoiceLine(models.TransientModel):
    _name = "import.invoice.line.wizard"
    _description = "Import supplier invoice line"

    supplier = fields.Many2one(
        comodel_name='res.partner', string='Supplier', required=True,
        domain="[('supplier',  '=', True)]")
    invoice = fields.Many2one(
        comodel_name='account.invoice', string="Invoice", required=True,
        domain="[('partner_id', '=', supplier), ('type', '=', 'in_invoice'),"
               "('state', 'in', ['open', 'paid', 'draft']),('imports','=',False)]")
    invoice_line = fields.Many2one(
        comodel_name='account.invoice.line', string="Invoice line",
        required=False, domain="[('invoice_id', '=', invoice), ('product_id.landed_cost_ok', '=', True), ('imports','=',False)]"
        )
    #Aplicable solo a metodos de landed cost
    split_method = fields.Selection(SPLIT_METHOD, string='Calculation method', default='by_quantity')
    quant_ids = fields.Many2many('stock.quant', 'landed_quant_import_rel', 'quant_id', 'imp_wiz_id', string='Series', help="Aplicado a caso DUI, para valorar una sola serie")
    #expense_type = fields.Many2one(
    #    comodel_name='purchase.expense.type', string='Expense type',
    #    required=False)

    @api.onchange('supplier')
    def onchange_supplier(self):
        #return {'domain': {'quant_ids': [('imports', '=', 1)]}}
        return {'domain': {'quant_ids': [('imports', '=', self.env.context['active_id'])]}}

    @api.multi
    def action_import_invoice_line(self):
        self.ensure_one()

        if self.invoice_line:
            if self.invoice_line.product_id.landed_cost_ok:
                taxes = self.invoice_line.invoice_line_tax_ids
                invoice_line_tax_ids = self.invoice_line.invoice_id.fiscal_position_id.map_tax(taxes)
                total = self.invoice_line.price_subtotal
                if self.quant_ids:
                    qt_ids = [(4, self.quant_ids.ids)]
                    method = 'lote'
                else:
                    method = 'picking'
                    qt_ids = []

                self.env['poi.purchase.imports.expense'].create({
                    'distribution': self.env.context['active_id'],
                    'invoice_line': self.invoice_line.id,
                    'invoice_id': self.invoice_line.invoice_id.id,
                    'ref': self.invoice_line.name,
                    'expense_amount': total,
                    'split_method': self.split_method,
                    'partner_id': self.supplier.id,
                    'product_id': self.invoice_line.product_id.id,
                    'name': self.invoice_line.name,
                    'currency_id': self.invoice_line.invoice_id.currency_id.id,
                    'expense_line_tax_ids': [(6, 0, invoice_line_tax_ids.ids)],
                    'quants_id': qt_ids,
                    'opcion_gasto': str(method),
                })
                self.invoice_line.imports = self.env.context['active_id']
        else:
            #Si se decide importar mas de una linea en las facturas
            for invoice_line in self.invoice.invoice_line_ids:
                if invoice_line.product_id.landed_cost_ok and not invoice_line.imports:
                    taxes = invoice_line.invoice_line_tax_ids
                    invoice_line_tax_ids = invoice_line.invoice_id.fiscal_position_id.map_tax(taxes)
                    total = invoice_line.price_subtotal
                    if self.quant_ids:
                        qt_ids = [(4, self.quant_ids.ids)]
                        method = 'lote'
                    else:
                        method = 'picking'
                        qt_ids = []
                    self.env['poi.purchase.imports.expense'].create({
                        'distribution': self.env.context['active_id'],
                        'invoice_line': invoice_line.id,
                        'invoice_id': invoice_line.invoice_id.id,
                        'ref': invoice_line.name,
                        'expense_amount': total,
                        'split_method': self.split_method,
                        'partner_id': self.supplier.id,
                        'product_id': invoice_line.product_id.id,
                        'name': invoice_line.name,
                        'currency_id': invoice_line.invoice_id.currency_id.id,
                        'expense_line_tax_ids': [(6, 0, invoice_line_tax_ids.ids)],
                        'quants_id': qt_ids,
                        'opcion_gasto': str(method),
                    })
                    invoice_line.invoice_id.imports = self.env.context['active_id']

