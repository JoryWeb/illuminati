import logging
from odoo import api, fields, models
from lxml import etree
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class AccountInvoiceLegacyLine(models.Model):
    _inherit = "account.invoice.legacy.line"

    lot_id = fields.Many2one('stock.production.lot', 'Chasis/Lote')


class AccountInvoiceLegacyLineWiz(models.TransientModel):
    _inherit = "account.invoice_refund.line_wiz"
    
    lot_id = fields.Many2one('stock.production.lot', 'Chasis/Lote')


class WizInvoiceRefund(models.TransientModel):
    _inherit = "wiz.invoice_refund"
    

    @api.model
    def default_get(self, fields):
        res = super(WizInvoiceRefund, self).default_get(fields)

        inv_ids = self._context['active_ids']
        if inv_ids and len(inv_ids)>0:
            invoice_o = self.env['account.invoice.legacy']
            invoice_id = invoice_o.search([('active_id', 'in', inv_ids)])
            inv_lines = []
            if invoice_id:
                for invoice in invoice_o.browse(invoice_id.id):
                    for line in invoice.invoice_line:
                        inv_lines.append([0,0,{'product_id': line.product_id.id, 'lot_id': (line.lot_id and line.lot_id.id) or False, 'price_unit': line.price_unit, 'price_subtotal': line.price_subtotal, 'quantity': line.quantity or 0, 'discount': line.discount }])

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
                    line.append ((0,0,{'product_id': l.product_id.id, 'lot_id':(l.lot_id and l.lot_id.id) or False, 'price_unit': l.price_unit, 'price_subtotal': l.price_subtotal, 'quantity': l.quantity, 'discount': l.discount}))
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
                    line.append ((0,0,{'product_id': l.product_id.id, 'lot_id':(l.lot_id and l.lot_id.id) or False, 'price_unit': l.price_unit, 'price_subtotal': l.price_subtotal, 'quantity': l.quantity, 'discount': l.discount}))
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