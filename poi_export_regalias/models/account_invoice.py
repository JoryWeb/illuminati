# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    n_regalias = fields.Char(string=u'Número Orden Regalías')
    date_payment_seneracom = fields.Date(string=u'Fecha Pago Seneracom')
    date_expiration_seneracom = fields.Date(string=u'Vence')
    ref_payment_seneracom = fields.Char(string=u'Referencia Pago')
    amount_pay_seneracom = fields.Float(string=u'Monto')

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price_royalties(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        date_inv = self.invoice_id._get_currency_rate_date() or fields.Date.today()
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(
                date=date_inv).compute(price_subtotal_signed,
                                       self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1

        # calcular regalias
        royalties_data = self.env['payment.royalties'].search(
            [('date_update', '<=', date_inv), ('date_expiration', '>=', date_inv)])

        for roy in royalties_data:
            value = roy.value
            if roy.type_value == 'porcentaje' and value > 0:
                self.value_royalties = (price_subtotal_signed * sign)*(value/100)
            else:
                self.value_royalties = value

    value_royalties = fields.Monetary(string=u"Regalía Ref", currency_field='company_currency_id', store=True,
                                      compute='_compute_price_royalties')
