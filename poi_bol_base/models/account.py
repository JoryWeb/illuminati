##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from odoo import models, fields, api, _

import odoo.addons.decimal_precision as dp

# MODELS
# account.invoice
# account.journal

MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    # Incrementar precision de tipo de cambio para soportar suficientes decimales para la division 1/6.96
    rate = fields.Float('Rate', digits=(12, 15), help='The rate of the currency to the currency of rate 1')


class AccountAccount(models.Model):
    _inherit = 'account.account'

    ajusta_ufv = fields.Boolean('Aplica ajuste UFV',
                                help="Especifica si esta Cuenta contable esta sujeta al procesamiento masivo de actualización de valor UFV")
    ajusta_usd = fields.Boolean('Aplica ajuste USD',
                                help="Especifica si esta Cuenta contable esta sujeta al procesamiento masivo de actualización de valor Dólar")
    account_aju_ufv_id = fields.Many2one('account.account', string="Cuenta de ajuste UFV (AITB)",
                                         help="Especifica la Cuenta contable contra la cual se lleva el valor de ajuste por una actualización UFV. por lo general es la cuenta de AITB",
                                         domain=[('deprecated', '=', False)])
    account_aju_usd_id = fields.Many2one('account.account', string="Cuenta de ajuste USD",
                                         help="Especifica la Cuenta contable contra la cual se lleva el valor de ajuste por una actualización Dólar.",
                                         domain=[('deprecated', '=', False)])


# no se pueden manipular los tipos de cuenta en V9
# class AccountAccountType(models.Model):
#    _inherit = 'account.account.type'

class AccountTax(models.Model):
    _inherit = 'account.tax'

    account_creditnote_id = fields.Many2one('account.account', u'Cuenta de Notas de crédito',
                                            help=u"Al usar la funcionalidad de Notas de crédito, esta cuenta sera utilizada para contabilizar la reversión de impuestos de períodos anteriores.")
    manual = fields.Boolean('Manual',
                            help="Permitir y aceptar el valor introducido manualmente en la misma factura como resultado calculado.")
    apply_lcv = fields.Boolean('Visible en LCV',
                               help="Especifica si las facturas relacionadas a este impuesto se muestran en el reporte de Libro de Compras y Ventas")
    cost_include = fields.Boolean('Incluir en el costo',
                                  help="Marque esta opción si el monto de este Impuesto sera incluido en el costo con el que entrara el Producto. Aplicable por ejemplo para el caso de Exentos.")
    type_bol = fields.Selection(
        [('none', 'Ninguno'), ('iva', 'IVA'), ('ice', 'ICE'), ('exe', 'Exento'), ('ret', 'Retención')], default='none',
        string="Caso SIN", help="""Denota manejos particulares de Impuestos Nacionales para presentaciones de Libros CV.
                                                                                                - ICE: Impuesto al consumo especifico
                                                                                                - IVA: Impuesto al Valor Agregado
                                                                                                - EXE: Exentos
                                                                                                - Ret: Retenciones""")


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    apply_lcv = fields.Boolean('Visible en LCV',
                               help="Especifica si las facturas relacionadas a este impuesto se muestran en el reporte de Libro de Compras y Ventas")
    type_bol = fields.Selection(
        [('none', 'Ninguno'), ('iva', 'IVA'), ('ice', 'ICE'), ('exe', 'Exento'), ('ret', 'Retención')], default='none',
        string="Caso SIN", help="""Denota manejos particulares de Impuestos Nacionales para presentaciones de Libros CV.
                                                                                                - ICE: Impuesto al consumo especifico
                                                                                                - IVA: Impuesto al Valor Agregado
                                                                                                - EXE: Exentos
                                                                                                - Ret: Retenciones""")


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.one
    @api.depends('bank_payment_type')
    def _get_payment_model(self):
        self.payment_model = self.bank_payment_type.payment_model

    bank_payment_type = fields.Many2one('bol.bank.payment.type', 'Payment Type')

    # Automatic fill on payments
    payment_model = fields.Selection([('check', 'Check'),
                                      ('bank_card', 'Debit,Credit or Prepaid Card'),
                                      ('bank_transfer', 'Bank Transfer'),
                                      ('sigma', 'Sigma'),
                                      ('other', 'Other')], string='Model of fields', compute='_get_payment_model')
    card_code = fields.Integer(string='Card Code')
    card_bank_owner = fields.Char(string='Card or Bank Owner', size=64)
    bank_account_number = fields.Char(string='Bank Account Number', size=16)
    client_code = fields.Char(string='Client Code', size=32)
    other_description = fields.Char(string='Other Description', size=64)


class AccountMove(models.Model):
    _inherit = 'account.move'

    bank_payment_type = fields.Many2one('bol.bank.payment.type', 'Payment Type')
    payment_model = fields.Selection([('check', 'Check'),
                                      ('bank_card', 'Debit,Credit or Prepaid Card'),
                                      ('bank_transfer', 'Bank Transfer'),
                                      ('sigma', 'Sigma'),
                                      ('other', 'Other')], 'Model of fields')
    check_number = fields.Char('Check Number', size=16)
    bank = fields.Many2one('res.bank', 'Bank')
    transaction_date = fields.Date('Transaction Date')
    card_code = fields.Integer('Card Code')
    card_bank_owner = fields.Char('Card or Bank Owner', size=64)
    bank_account_number = fields.Char('Bank Account Number', size=16)
    transaction_number = fields.Char('Transaction Number', size=16)
    client_code = fields.Char('Client Code', size=32)
    other_description = fields.Char('Other Desciption', size=64)
    received_by = fields.Many2one('res.partner', 'Received By')
    caso_aju = fields.Selection([('n', 'No Aplica'), ('ufv', 'UFV'), ('usd', 'USD')], string="Caso de Ajuste",
                                default='n',
                                help="Especifica si es un Asiento resultante del proceso de Ajuste por actualización de valor.")

    @api.onchange('journal_id')
    def onchange_journal(self):

        if not self.journal_id:
            return False

        if self.journal_id.type == "bank":
            self.payment_model = self.journal_id.bank_payment_type.payment_model
            self.bank_payment_type = self.journal_id.bank_payment_type.id
        else:
            self.payment_model = False
            self.bank_payment_type = False


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    _order = "date, id"

    @api.one
    @api.depends('debit', 'credit')
    def _calc_debit_credit(self):

        for line in self:
            debit = line.debit
            credit = line.credit
            if debit > 0:
                self.is_debit = 1
            else:
                self.is_debit = 0

            company = self.move_id.company_id
            curr_sec_id = company.currency_id_sec
            if not company:
                company = self.env.user.company_id
                curr_sec_id = company.currency_id_sec
            self.debit_sec = company.currency_id.with_context(date=line.date).compute(debit, curr_sec_id)
            self.credit_sec = company.currency_id.with_context(date=line.date).compute(credit, curr_sec_id)

    is_debit = fields.Integer(compute='_calc_debit_credit', string=u'Es débito', store=True,
                              help="Campo interno para ordenar los Asientos con los montos Debe primero")
    debit_sec = fields.Float(compute='_calc_debit_credit', digits_compute=dp.get_precision('Account'),
                             string='Debe Sec', store=True)
    credit_sec = fields.Float(compute='_calc_debit_credit', digits_compute=dp.get_precision('Account'),
                              string='Haber Sec', store=True)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    @api.depends('state')
    def _amount_applied(self):

        for payment in self:
            if payment.state != 'posted':
                payment.amount_applied = 0.0
            else:
                currency_journal = payment.journal_id.currency_id.id
                if currency_journal:
                    payment.amount_applied = payment.journal_id.currency_id.compute(payment.amount,
                                                                                    payment.company_id.currency_id)
                else:
                    payment.amount_applied = payment.amount

    bank_payment_type = fields.Many2one('bol.bank.payment.type', string='Payment Type')
    payment_model = fields.Selection([('check', 'Check'),
                                      ('bank_card', 'Debit,Credit or Prepaid Card'),
                                      ('bank_transfer', 'Bank Transfer'),
                                      ('sigma', 'Sigma'),
                                      ('other', 'Other')])
    check_number = fields.Char('Check Number', size=16)
    bank = fields.Many2one('res.bank', string='Bank')
    transaction_date = fields.Date('Transaction Date', default=fields.Date.today())
    card_code = fields.Integer('Card Code')
    card_bank_owner = fields.Char('Card or Bank Owner', size=64)
    bank_account_number = fields.Char('Bank Account Number', size=16)
    transaction_number = fields.Char('Transaction Number', size=16)
    client_code = fields.Integer('Card Code')
    other_description = fields.Char('Other Description', size=64)
    received_by = fields.Many2one('res.partner', 'Received By')
    amount_applied = fields.Float(compute='_amount_applied', store=True, string="Monto Aplicado (Bs.)")

    @api.onchange('journal_id')
    def _onchange_journal(self):

        currency_before = self.currency_id or False

        res = super(AccountPayment, self)._onchange_journal()

        if self.journal_id and self.journal_id.type == 'bank':
            self.payment_model = self.journal_id.bank_payment_type.payment_model
            self.bank_payment_type = self.journal_id.bank_payment_type and self.journal_id.bank_payment_type.id or None
            self.bank = self.journal_id.bank_id and self.journal_id.bank_id.id or None
            self.card_code = self.journal_id.card_code
            self.card_bank_owner = self.journal_id.card_bank_owner
            self.bank_account_number = self.journal_id.bank_account_number
            self.client_code = self.journal_id.client_code
            self.other_description = self.journal_id.other_description
        else:
            self.payment_model = None
            self.bank_payment_type = None
            self.check_number = None
            self.bank = None
            self.card_code = None
            self.card_bank_owner = None
            self.bank_account_number = None
            self.client_code = None
            self.other_description = None
            self.received_by = None
        # Verificar la moneda y establecer tipo de cambio
        if self.journal_id and currency_before:
            if self.currency_id.id != currency_before.id:  # self.journal_id.company_id.currency_id.id:
                amount_curr = currency_before.compute(self.amount,
                                                      self.journal_id.currency_id or self.journal_id.company_id.currency_id)
            else:
                amount_curr = self.invoice_ids.residual or self.amount
            self.amount = amount_curr
        return res


class account_register_payments(models.TransientModel):
    _inherit = "account.register.payments"

    bank_payment_type = fields.Many2one('bol.bank.payment.type', string='Payment Type')
    payment_model = fields.Selection([('check', 'Check'),
                                      ('bank_card', 'Debit,Credit or Prepaid Card'),
                                      ('bank_transfer', 'Bank Transfer'),
                                      ('sigma', 'Sigma'),
                                      ('other', 'Other')])
    check_number = fields.Char('Check Number', size=16)
    bank = fields.Many2one('res.bank', string='Bank')
    transaction_date = fields.Date('Transaction Date', default=fields.Date.today())
    card_code = fields.Integer('Card Code')
    card_bank_owner = fields.Char('Card or Bank Owner', size=64)
    bank_account_number = fields.Char('Bank Account Number', size=16)
    transaction_number = fields.Char('Transaction Number', size=16)
    client_code = fields.Integer('Card Code')
    other_description = fields.Char('Other Description', size=64)
    received_by = fields.Many2one('res.partner', 'Received By')
    amount_applied = fields.Float(compute='_amount_applied', store=True, string="Monto Aplicado (Bs.)")

    @api.onchange('journal_id')
    def _onchange_journal(self):

        context = dict(self._context or {})
        currency_before = self.currency_id or False

        res = super(account_register_payments, self)._onchange_journal()

        if self.journal_id and self.journal_id.type == 'bank':
            self.payment_model = self.journal_id.bank_payment_type.payment_model
            self.bank_payment_type = self.journal_id.bank_payment_type and self.journal_id.bank_payment_type.id or None
            self.bank = self.journal_id.bank_id and self.journal_id.bank_id.id or None
            self.card_code = self.journal_id.card_code
            self.card_bank_owner = self.journal_id.card_bank_owner
            self.bank_account_number = self.journal_id.bank_account_number
            self.client_code = self.journal_id.client_code
            self.other_description = self.journal_id.other_description
        else:
            self.payment_model = None
            self.bank_payment_type = None
            self.check_number = None
            self.bank = None
            self.card_code = None
            self.card_bank_owner = None
            self.bank_account_number = None
            self.client_code = None
            self.other_description = None
            self.received_by = None
        # Verificar la moneda y establecer tipo de cambio
        if self.journal_id and currency_before:
            if self.currency_id.id != currency_before.id:  # self.journal_id.company_id.currency_id.id:
                amount_curr = currency_before.compute(self.amount,
                                                      self.journal_id.currency_id or self.journal_id.company_id.currency_id)
            else:
                active_ids = context.get('active_ids')
                active_model = context.get('active_model')
                invoices = self.env[active_model].browse(active_ids)
                sum_residual = sum(inv.residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] for inv in invoices)
                amount_curr = sum_residual or self.amount
            self.amount = amount_curr
        return res

    @api.multi
    def _prepare_payment_vals(self, invoices):
        """ Hook for extension """
        res = super(account_register_payments, self)._prepare_payment_vals(invoices)
        bank_vals = {
            'payment_model': self.bank_payment_type.payment_model,
            'bank_payment_type': self.bank_payment_type and self.bank_payment_type.id or None,
            'bank': self.bank and self.bank.id or None,
            'transaction_date': self.transaction_date,
            'card_code': self.card_code,
            'check_number': self.check_number,
            'card_bank_owner': self.card_bank_owner,
            'bank_account_number': self.bank_account_number,
            'client_code': self.client_code,
            'other_description': self.other_description,
        }
        res.update(bank_vals)
        return res
