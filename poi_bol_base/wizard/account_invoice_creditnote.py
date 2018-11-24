##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2015 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Author: Jesus Gorostiaga
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
from openerp import models, fields, api, _, tools
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


# class account_invoice_refund(models.Model):
#     _name = 'account.invoice.legacy'
#
#     active_id = fields.Integer('Active_id')
#     cc_nro = fields.Char('Numero de Factura')
#     cc_aut = fields.Char('Autorizacion Nro.')
#     nit = fields.Char('Nit')
#     invoice_line = fields.One2many('account.invoice.legacy.line', 'invoice_id', string='Invoice Lines', readonly=True)
#     amount_untaxed = fields.Float('Total Sin Impuesto')
#     amount_tax = fields.Float('Impuesto')
#     amount_total = fields.Float('Total')
#
#
# class account_invoice_refund_line(models.Model):
#     _name = "account.invoice.legacy.line"
#
#     invoice_id = fields.Many2one('account.invoice.legacy', string='Factura', ondelete='cascade', index=True)
#     uos_id = fields.Many2one('product.uom', string='Unidad de Medida', ondelete='set null', index=True)
#     product_id = fields.Many2one('product.product', string='Producto', ondelete='restrict', index=True)
#     price_unit = fields.Float(string='Precio Unitario', digits= dp.get_precision('Product Price'))
#     price_subtotal = fields.Float(string='Monto Total', digits= dp.get_precision('Account'), readonly=True)
#     price_net = fields.Float(string='Precio Neto', digits= dp.get_precision('Account'))
#     quantity = fields.Float(string='Cantidad', digits= dp.get_precision('Product Unit of Measure'), default=1)
#     discount = fields.Float(string='Descuento (%)', digits= dp.get_precision('Discount'), default=0.0)




class account_invoice_refund_wiz(models.TransientModel):
    _name = 'wiz.invoice_refund'

    cc_nro = fields.Char('Numero de Factura')
    cc_aut = fields.Char('Autorizacion Nro.')
    nit = fields.Char('Nit')
    invoice_line = fields.One2many('account.invoice_refund.line_wiz', 'invoice_id', string='Invoice Lines')
    amount_untaxed = fields.Float('Total Sin Impuesto')
    amount_tax = fields.Float('Impuesto')
    amount_total = fields.Float('Total', required=True)


    @api.model
    def default_get(self, fields):
        res = super(account_invoice_refund_wiz, self).default_get(fields)

        inv_ids = self._context['active_ids']
        if inv_ids and len(inv_ids)>0:
            invoice_o = self.env['account.invoice.legacy']
            invoice_id = invoice_o.search([('active_id', 'in', inv_ids)])
            inv_lines = []
            if invoice_id:
                for invoice in invoice_o.browse(invoice_id.id):
                    for line in invoice.invoice_line:
                        inv_lines.append({'product_id': line.product_id.id, 'price_unit': line.price_unit, 'price_subtotal': line.price_subtotal, 'quantity': line.quantity or 0, 'discount': line.discount })

                res.update({'cc_nro': invoice.cc_nro, 'cc_aut': invoice.cc_aut, 'nit': invoice.nit, 'amount_untaxed': invoice.amount_untaxed, 'amount_tax': invoice.amount_tax, 'amount_total': invoice.amount_total,'invoice_line': inv_lines})

        return res

    @api.multi
    def open_table(self):

        line = []
        inv_ids = self._context['active_ids']
        invoice_o = self.env['account.invoice.legacy']
        invoice_lines = self.env['account.invoice.legacy.line']
        invoice_id = invoice_o.search([('active_id', 'in', inv_ids)])
        inv_lines = []
        if invoice_id:
            i = invoice_o.browse(invoice_id.id)
            for lines_i in i.invoice_line:
                invoice_lines += lines_i
            invoice_lines.unlink()
            for invoice in self.browse(self.id):
                total = 0
                for l in invoice.invoice_line:
                    total = total + l.price_subtotal
                    line.append ((0,0,{'product_id': l.product_id.id, 'price_unit': l.price_unit, 'price_subtotal': l.price_subtotal, 'quantity': l.quantity, 'discount': l.discount}))
                i.cc_nro = invoice.cc_nro
                i.cc_aut = invoice.cc_aut
                i.nit = invoice.nit
                i.invoice_line = line
                i.amount_untaxed = total - (total * 0.13)
                i.amount_tax = total * 0.13
                i.amount_total = total

        else:
            for invoice in self.browse(self.id):
                total = 0
                for l in invoice.invoice_line:
                    total = total + l.price_subtotal
                    line.append ((0,0,{'product_id': l.product_id.id, 'price_unit': l.price_unit, 'price_subtotal': l.price_subtotal, 'quantity': l.quantity, 'discount': l.discount}))
                data = {
                    'active_id': self._context['active_id'],
                    'cc_nro': invoice.cc_nro,
                    'cc_aut': invoice.cc_aut,
                    'nit': invoice.nit,
                    'invoice_line': line,
                    'amount_untaxed': total - (total * 0.13),
                    'amount_tax': total * 0.13,
                    'amount_total': total,

                }
            a = self.env['account.invoice.legacy'].create(data)
            account_invoice = self.env['account.invoice'].browse(self._context['active_id'])
            a = account_invoice.write({'tipo_fac': '6'})    #Marcarla como Nota de credito cliente específicamente

        return True

    @api.onchange('invoice_line')
    def sum_total(self):
        total = 0
        for invoice in self.invoice_line:
            total = invoice.price_subtotal + total
        self.amount_total = total
        self.amount_untaxed = total - (total * 0.13)
        self.amount_tax = total * 0.13



class account_invoice_refund_line_wiz(models.TransientModel):
    _name = 'account.invoice_refund.line_wiz'

    @api.model
    def _default_price_unit(self):
        if not self._context.get('check_total'):
            return 0
        total = self._context['check_total']
        for l in self._context.get('invoice_line', []):
            if isinstance(l, (list, tuple)) and len(l) >= 3 and l[2]:
                vals = l[2]
                price = vals.get('price_unit', 0) * (1 - vals.get('discount', 0) / 100.0)
                total = total - (price * vals.get('quantity'))
                taxes = vals.get('invoice_line_tax_id')
                if taxes and len(taxes[0]) >= 3 and taxes[0][2]:
                    taxes = self.env['account.tax'].browse(taxes[0][2])
                    tax_res = taxes.compute_all(price, vals.get('quantity'),
                        product=vals.get('product_id'), partner=self._context.get('partner_id'))
                    for tax in tax_res['taxes']:
                        total = total - tax['amount']
        return total


    invoice_id = fields.Many2one('wiz.invoice_refund', string='Invoice Reference', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product',
        ondelete='restrict', index=True)

    price_unit = fields.Float(string='Unit Price',
        digits= dp.get_precision('Product Price'),
        default=_default_price_unit)
    price_subtotal = fields.Float(string='Amount', digits= dp.get_precision('Account'))
    quantity = fields.Float(string='Quantity', digits= dp.get_precision('Product Unit of Measure')
      , default=1)
    discount = fields.Float(string='Discount (%)', digits= dp.get_precision('Discount'),
        default=0.0)




    @api.onchange('quantity', 'price_unit', 'discount')
    def check_change(self):
        discount = 0
        total = self.price_unit * self.quantity
        if self.discount > 0:
            discount = self.discount / 100
            discount = total * discount
        self.price_subtotal =  total - discount
