##############################################################################
#
#    Odoo Module
#    Copyright (C) 2015 Grover Menacho (<http://www.grovermenacho.com>).
#    Copyright (C) 2015 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Grover Menacho
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
from odoo.exceptions import ValidationError, Warning
from odoo.tools.float_utils import float_round


class AccountPaymentRequestType(models.Model):
    _name = 'account.payment.request.type'
    _description = 'Account Payment Request Types'

    name = fields.Char(string='Name')
    default_mode = fields.Selection([('document', 'Based on Documents'),
                                     ('new', 'Advanced Request')], 'Mode')
    force_po_inv = fields.Boolean(string='Force PO/Invoices')
    force_pr = fields.Boolean(string='Force Purchase Receipt')
    force_notes = fields.Boolean(string='Force Notes')
    default_function = fields.Selection([('payment', 'Generates Payment'),
                                         ('move', 'Generate Moves')], string='Default Function')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        ondelete='set null', default=lambda self: self.env.user.company_id.id)
    payment_type = fields.Selection([('outbound', 'Outbound'),
                                     ('inbound', 'Inbound')], string="Payment Type")
    # We'll use payment_type like account.payment


class AccountPaymentRequest(models.Model):
    _name = 'account.payment.request'
    _inherit = ['mail.thread']
    _description = 'Account Payment Requests'

    @api.multi
    @api.depends('document_ids.amount_applied', 'document_ids.pay', 'document_ids.currency_id', 'company_id','amount_currency_id','amount_requested','payment_ids.state','movement_ids.state')
    def _compute_amount(self):
        for s in self:
            amount_total = 0.0
            amount_paid = 0.0

            if s.default_mode == 'document':
                for doc in s.document_ids:
                    if not doc.pay:
                        continue
                    if s.amount_currency_id and s.amount_currency_id != doc.currency_id:
                        amount_total += doc.currency_id.compute(doc.amount_applied, s.amount_currency_id)
                    else:
                        amount_total += doc.amount_applied

            else:
                amount_total = s.amount_requested

            if s.payment_ids:
                for payment in s.payment_ids:
                    if payment.state != "draft":
                        if s.amount_currency_id and s.amount_currency_id != payment.currency_id:
                            amount_paid += payment.currency_id.compute(payment.amount, s.amount_currency_id)     #s.amount_currency_id.compute(payment.amount, payment.currency_id)
                        else:
                            amount_paid += payment.amount

            if s.movement_ids:
                for m in s.movement_ids:
                    for p in m.payment_ids:
                        if p.state != 'draft':
                            amount_paid += p.currency_id.compute(p.amount, s.amount_currency_id)

            s.amount_total = amount_total
            s.amount_paid = amount_paid
            s.amount_open = amount_total - amount_paid

    @api.multi
    @api.depends('rendition_ids', 'amount_paid', 'total_rendition')
    def _compute_check_rendition(self):
        for s in self:
            if s.total_rendition >= s.amount_paid:
                s.check_rendition = True
            else:
                s.check_rendition = False

    payment_type = fields.Selection([('outbound','Outbound'),
                                     ('inbound','Inbound')], string="Payment Type")
    #We'll use payment_type like account.payment

    name = fields.Char(string='Name')
    type_request = fields.Many2one('account.payment.request.type', 'Type Request')
    default_mode = fields.Selection([('document', 'Based on Documents'),
                                     ('new', 'Advanced Request')], 'Mode', related='type_request.default_mode',
                                    store=True)
    date_request = fields.Date(string='Date Request', default=lambda self: fields.Date.today())
    user_id = fields.Many2one('res.users', 'Requestor', default=lambda self: self.env.user, required=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('requested', 'Requested'),
                              ('confirmed', 'Confirmed'),
                              ('closed', 'Closed'),
                              ('cancel', 'Cancel'),
                              ('partial', 'Partially paid'),
                              ('rejected', 'Rejected')], string='State', default='draft')
    partner_id = fields.Many2one('res.partner', 'Provider')
    issued_to_requestor = fields.Boolean(string='Issued to Requestor')
    document_ids = fields.One2many('account.payment.request.document', 'request_id', 'Documents')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    amount_total = fields.Float(string='Total',
                                store=True, readonly=True, compute='_compute_amount')
    amount_paid = fields.Float(string='Monto pagado',
                               store=True, readonly=True, compute='_compute_amount')
    amount_open = fields.Float(string='Monto abierto',
                                store=True, readonly=True, compute='_compute_amount')
    notes = fields.Text('Notes')
    default_function = fields.Selection([('payment', 'Generates Payment'),
                                         ('move', 'Generate Moves')], related='type_request.default_function',
                                        string='Default Function')
    journal_id = fields.Many2one('account.journal', string=u"Método de Pago") #i18n is not working...
    account_analytic_id = fields.Many2one('account.analytic.account', u"Cuenta analítica", required=True)

    amount_requested = fields.Float('Amount Requested')
    amount_currency_id = fields.Many2one('res.currency', 'Currency',
                                         default=lambda self: self.env.user.company_id.currency_id, required=True)

    payment_ids = fields.One2many('account.payment', 'payment_request_id', 'Payments')
    movement_ids = fields.One2many('account.cash.movement', 'payment_request_id', 'Movements')
    #Detalles banco
    payment_method_id = fields.Many2one('account.payment.method', string='Tipo de pago', domain="[('payment_type','=',payment_type)]")
    payment_method_code = fields.Char(related='payment_method_id.code',
                                      help="Technical field used to adapt the interface to the payment type selected.",
                                      readonly=True)
    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method',
                                         help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    bank_payment_type = fields.Many2one('bol.bank.payment.type', string='Payment Type')
    payment_model = fields.Selection([('check', 'Check'),
                                      ('bank_card', 'Debit,Credit or Prepaid Card'),
                                      ('bank_transfer', 'Bank Transfer'),
                                      ('sigma', 'Sigma'),
                                      ('other', 'Other')])
    check_number = fields.Char('Check Number', size=16)
    bank = fields.Many2one('res.bank', string='Bank')
    transaction_date = fields.Date('Transaction Date', default=lambda self: fields.Date.today())
    card_code = fields.Integer('Card Code')
    card_bank_owner = fields.Char('Card or Bank Owner', size=64)
    bank_account_number = fields.Char('Bank Account Number', size=16)
    transaction_number = fields.Char('Transaction Number', size=16)
    client_code = fields.Integer('Card Code')
    other_description = fields.Char('Other Description', size=64)
    received_by = fields.Many2one('res.partner', 'Received By')
    #poi_bank:
    bank_id = fields.Many2one('res.bank', 'Bank')
    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account')
    transaction_date = fields.Date("Transaction Date", default=fields.Date.today())
    transaction_number = fields.Char("Transaction Number")
    bank_card_issuer = fields.Selection([('visa', 'Visa'),
                                         ('master_card', 'Master Card'),
                                         ('american_express', 'American Express')], 'Card Issuer')
    bank_card_type = fields.Selection([('debit', 'Debit'),
                                       ('credit', 'Credit'),
                                       ('prepaid', 'Prepaid')], 'Card Type')
    other_payment_data = fields.Char('Other Payment Data')
    # Outbound payments
    checkbook_id = fields.Many2one('res.bank.account.checkbook', string='Checkbook')
    check_id = fields.Many2one('res.bank.account.check', 'Check')
    bank_card_id = fields.Many2one('res.bank.card', 'Card')
    # Inbound Payments
    bank_card_code = fields.Char('Bank Card Code', help='Last digits of card')
    check_rendition = fields.Boolean('Rendicion Completa', compute="_compute_check_rendition", store=True)
    total_rendition = fields.Float('Rendicion Total')
    one_pay_only = fields.Boolean('Realizar un Solo Pago', default=False, help="Al macar esta opcion se realizara un solo pago para varias facturas.")

    no_voucher = fields.Char("No. Voucher")
    bank_id = fields.Many2one("res.bank","Banco")
    payment_date = fields.Date(u"Fecha de Depósito")
    payment_code = fields.Char(u"Código de Depósito")


    @api.multi
    @api.depends('payment_type', 'journal_id')
    def _compute_hide_payment_method(self):
        for s in self:
            if not s.journal_id:
                s.hide_payment_method = True
                return
            journal_payment_methods = s.payment_type == 'inbound' and s.journal_id.inbound_payment_method_ids or s.journal_id.outbound_payment_method_ids
            s.hide_payment_method = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            self.amount_currency_id = self.journal_id.currency_id and self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id

        if self.journal_id and self.journal_id.type == 'bank':
            self.payment_model = self.journal_id.bank_payment_type.payment_model
            self.bank_payment_type = self.journal_id.bank_payment_type and self.journal_id.bank_payment_type.id or None
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

    @api.multi
    @api.depends('payment_ids', 'movement_ids')
    def _get_count(self):
        for r in self:
            v = 0
            m = 0
            for payment in self.payment_ids:
                v += 1
            for movement in self.movement_ids:
                m += 1

            self.payment_count = v
            self.movement_count = m

    payment_count = fields.Integer('Payments', compute=_get_count)
    movement_count = fields.Integer('Cash Movements', compute=_get_count)

    rendition_ids = fields.One2many("account.expenses.rendition","payment_request_id", "Rendition Lines")

    _order = "id desc"

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        default['state'] = 'draft'
        return super(AccountPaymentRequest, self).copy(default)


    @api.multi
    def _get_request_data(self, partner_id):
        res = []

        purchase_obj = self.env['purchase.order']
        purchase_domain = [('invoice_ids', '=', False), ('partner_id', '=', partner_id),
                           ('state', 'in', ['sent', 'bid', 'confirmed', 'approved', 'purchase'])]

        invoice_obj = self.env['account.invoice']
        invoice_domain = [('type', '=', 'in_invoice'), ('state', '=', 'open'), ('partner_id', '=', partner_id)]

        # LET'S GET PURCHASES FIRST
        for p in  purchase_obj.search(purchase_domain):
            res.append({
                'type': 'purchase',
                'document': p.name,
                'balance': p.amount_total,
                'amount_applied': p.amount_total,
                'currency_id': p.currency_id,
                'source_document': 'purchase.order,' + str(p.id),
                'res_id': p.id,
            })
        # LET'S GET INVOICES THEN
        for i in invoice_obj.search(invoice_domain):
            res.append({
                'type': 'invoice',
                'document': i.number,
                'balance': i.residual,
                'amount_applied': i.residual,
                'currency_id': i.currency_id,
                'source_document': 'account.invoice,' + str(i.id),
                'res_id': i.id,
            })

        return res

    @api.onchange('partner_id', 'type_request')
    def onchange_payment_request(self):
        if self.partner_id and self.type_request:
            r = []
            if self.type_request.force_po_inv:
                r = r + self._get_request_data(partner_id)

            self.document_ids = r

    @api.multi
    def action_request(self):
        seq = self.env['ir.sequence']
        for request in self:
            if request.one_pay_only:
                for d in request.document_ids.filtered(lambda x: x.pay == True):
                    if d.currency_id != request.amount_currency_id.id:
                        raise ValidationError('No se puede Seleccionar documentos de Monedas Distintas para realizar un solo Pago.')

            if request.type_request.force_notes and not request.notes:
                raise ValidationError(_('You must fill the Notes field.'))
            if request.type_request.force_po_inv:
                one_sel = False
                for doc in request.document_ids:
                    if doc.pay:
                        one_sel = True
                        break
                if not one_sel:
                    raise ValidationError(_("Tiene que seleccionar al menos un documento con la opción 'Pagar'."))

            if request.default_function == 'payment':
                if request.partner_id.partner_type == 'customer':
                    if not request.partner_id.property_prepaid_account_receivable_id:
                        raise ValidationError(_('La cuenta de Anticipo Clientes no se encuetra definida.'))
                else:
                    if not request.partner_id.property_prepaid_account_payable_id:
                        raise ValidationError(_('La cuenta de Anticipo Proveedores no se encuetra definida.'))

            if request.payment_type == 'outbound':
                code = seq.next_by_code('payment.request') or '/'
                request.write({'state': 'requested', 'name': code})
            else:
                code = seq.next_by_code('payment.request.inbound') or '/'
                request.write({'state': 'confirmed', 'name': code})
        return True

    @api.multi
    def _prepare_new_payment(self):
        if not self.journal_id:
            aj = self.env['account.journal']
            ajs = aj.search([('type', 'in', ['bank', 'cash'])])
            if ajs:
                journal_id = ajs[0].id
            else:
                journal_id = False
        else:
            journal_id = self.journal_id.id

        res = {
            'journal_id': journal_id,
            'payment_date': self.date_request,
            # 'communication': self.communication,
            # 'invoice_ids': [(4, inv.id, None) for inv in self._get_invoices()],
            'payment_type': self.payment_type,
            'amount': self.amount_open or self.amount_total,
            'currency_id': self.amount_currency_id.id,
            'partner_id': self.partner_id and self.partner_id.id or self.user_id.partner_id.id,
            'payment_request_id': self.id,
            'is_prepaid': True,
            'account_analytic_id': self.account_analytic_id and self.account_analytic_id.id or False,
            'payment_method_id': self.payment_method_id and self.payment_method_id.id or False,

            'bank_id': self.bank_id and self.bank_id.id or False,
            'bank_account_id': self.bank_account_id and self.bank_account_id.id or False,
            'bank_card_issuer': self.bank_card_issuer,
            'bank_card_type': self.bank_card_type,
            'other_payment_data': self.other_payment_data,
            'bank_card_id': self.bank_card_id and self.bank_card_id.id or False,
        }

        if self.payment_type == 'outbound':
            res['payment_method_id'] = self.env.ref('account.account_payment_method_manual_out') and self.env.ref('account.account_payment_method_manual_out').id or False
            res['partner_type'] = 'supplier'
        else:
            res['payment_method_id'] = self.env.ref('account.account_payment_method_manual_in') and self.env.ref(
                'account.account_payment_method_manual_in').id or False
            res['partner_type'] = 'customer'
        return res

    @api.multi
    def create_new_prepayment(self):
        ap = self.env['account.payment']
        ap_id = ap.create(self._prepare_new_payment())
        return True

    def _prepare_new_movement(self):
        aj = self.env['account.journal']
        ajs = aj.search([('type', 'in', ['bank', 'cash'])])
        res = {
            'journal_id': ajs and ajs[0].id or False,
            'ref': self.name,
            'date': self.date_request,
            'payment_request_id': self.id,
            'account_analytic_id': self.account_analytic_id.id,
            'line_ids': [(0, 0, {'partner_id': self.user_id.partner_id.id,
                                 'account_id': self.user_id.partner_id.property_account_receivable_id.id,
                                 'debit': self.amount_open,
                                 'currency_id': self.amount_currency_id.id,
                                 })]
        }

        res = {
            'payment_request_id': self.id,
            'partner_id': self.user_id.partner_id.id,
            'ref': self.name,
            'date': self.date_request,
            'amount': self.amount_open,
            'currency_id': self.amount_currency_id.id,
            'account_analytic_id': self.account_analytic_id.id,
        }

        return res

    def create_new_movement(self):
        acm = self.env['account.cash.movement']
        acm_id = acm.create(self._prepare_new_movement())
        return True

    @api.multi
    def action_approve(self):

        self.write({'state': 'confirmed'})
        done = self.do_create()

        return done

    @api.multi
    def do_create(self):

        if self.default_mode == 'document':
            if self.one_pay_only and self.document_ids.filtered(lambda doc: doc.type == 'invoice') and self.type_request.default_function == 'payment':
                self.create_one_payment()

            else:
                for doc in self.document_ids:
                    if doc.type == 'purchase' and self.type_request.default_function == 'payment':
                        doc.create_prepayment()
                    elif doc.type == 'invoice' and self.type_request.default_function == 'payment':
                        doc.create_payment()
                    elif self.type_request.default_function == 'move':
                        doc.create_movement()
        else:
            if self.type_request.default_function == 'move':
                self.create_new_movement()
            else:
                self.create_new_prepayment()

        return True

    @api.multi
    def action_reject(self):
        self.write({'state': 'rejected'})
        return True

    @api.multi
    def action_close(self):
        self.write({'state': 'closed'})
        return True

    @api.multi
    def test_inbound_paid(self):
        precision = self.env['decimal.precision'].precision_get('Account')
        for request in self:
            total_paid = 0.0
            payments = self.env['account.payment'].search([('payment_request_id','=',request.id),('state','!=','draft')])
            for p in payments:
                if p.state != 'draft':
                    total_paid += p.currency_id.compute(p.amount, request.amount_currency_id)
            if float_round(total_paid, precision_digits=precision) >= float_round(request.amount_total, precision_digits=precision):
                request.state = 'closed'
            elif float_round(total_paid, precision_digits=precision) > 0.0:
                request.state = 'partial'

    @api.multi
    def test_outbound_paid(self):
        precision = self.env['decimal.precision'].precision_get('Account')
        for request in self:
            total_paid = 0.0
            for r in request.rendition_ids:
                if r.state == 'done':
                    total_paid += r.invoice_total
            for p in request.payment_ids:
                if p.state != 'draft':
                    total_paid += p.currency_id.compute(p.amount, request.amount_currency_id)
            for m in request.movement_ids:
                for p in m.payment_ids:
                    if p.state != 'draft':
                        total_paid += p.currency_id.compute(p.amount, request.amount_currency_id)

            if float_round(total_paid, precision_digits=precision) >= float_round(request.amount_total, precision_digits=precision):
                request.state = 'closed'
            elif float_round(total_paid, precision_digits=precision) > 0.0:
                request.state = 'partial'

    @api.multi
    def create_one_payment(self):
        payment = self.env['account.payment'].create(self._prepare_one_payment())
        # payment.post()
        return True


    @api.multi
    def _prepare_one_payment(self, prepayment=False):
        journal_id = self.journal_id.id
        amount_applied = 0.0
        amount_paid = self.amount_paid or 0.0

        # if self.currency_id and self.currency_id != self.request_id.company_id.currency_id:
        #     amount_applied = self.currency_id.compute(self.amount_applied - amount_paid, self.request_id.company_id.currency_id)
        # else:
        amount_applied = self.amount_open

        res = {
            'journal_id': journal_id,
            'payment_date': self.date_request,
            #'communication': self.communication,
            # 'invoice_ids': [(4, inv.id, None) for inv in self._get_invoices()],
            'invoice_ids': [(4, inv.res_id, None) for inv in self.document_ids.filtered(lambda x: x.pay == True)],
            'payment_type': 'outbound',
            'amount': amount_applied,
            'currency_id': self.amount_currency_id.id,
            'partner_id': self.partner_id and self.partner_id.id or self.user_id.partner_id.id,
            'partner_type': 'supplier',
            'payment_request_id': self.id,
            'is_prepaid': prepayment,
            'account_analytic_id': self.account_analytic_id and self.account_analytic_id.id or False,
            'payment_method_id': self.payment_method_id and self.payment_method_id.id or (self.env.ref('account.account_payment_method_manual_out') and self.env.ref('account.account_payment_method_manual_out').id or False),

            'bank_id': self.bank_id and self.bank_id.id or False,
            'bank_account_id': self.bank_account_id and self.bank_account_id.id or False,
            'bank_card_issuer': self.bank_card_issuer,
            'bank_card_type': self.bank_card_type,
            'other_payment_data': self.other_payment_data,
            'bank_card_id': self.bank_card_id and self.bank_card_id.id or False,
        }
        return res

class AccountPaymentRequestDocument(models.Model):
    _name = 'account.payment.request.document'
    _description = 'Account Payment Request Documents'

    request_id = fields.Many2one('account.payment.request', string='Request')
    pay = fields.Boolean('Pay')
    type = fields.Selection([('purchase', 'Purchase Order'),
                             ('invoice', 'Purchase Invoice')], string='Type')
    document = fields.Char('Document')
    balance = fields.Float('Balance')
    fee_number = fields.Integer('Fee')
    amount_applied = fields.Float('Amount Applied')
    currency_id = fields.Many2one('res.currency', 'Currency')
    source_document = fields.Char(string='Source Document')
    res_id = fields.Integer('Document ID')

    @api.multi
    def open_document(self):
        for subtask in self:
            if not self.source_document:
                return {}

            return {
                'type': 'ir.actions.act_window',
                'name': self.type == 'purchase' and 'Purchase' or 'Invoice',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': self.source_document.split(",")[0],
                'res_id': int(self.source_document.split(",")[1]),
                'target': 'current',
            }

    @api.multi
    def _prepare_payment(self, prepayment=False):

        if not self.request_id.journal_id:
            aj = self.env['account.journal']
            ajs = aj.search([('type', 'in', ['bank', 'cash'])])
            if ajs:
                journal_id = ajs[0].id
            else:
                journal_id = False
        else:
            journal_id = self.request_id.journal_id.id

        amount_applied = 0.0
        amount_paid = self.request_id.amount_paid or 0.0

        if self.currency_id and self.currency_id != self.request_id.company_id.currency_id:
            amount_applied = self.currency_id.compute(self.amount_applied - amount_paid, self.request_id.company_id.currency_id)
        else:
            amount_applied = self.amount_applied - amount_paid

        res = {
            'journal_id': journal_id,
            'payment_date': self.request_id.date_request,
            #'communication': self.communication,
            #'invoice_ids': [(4, inv.id, None) for inv in self._get_invoices()],
            'payment_type': 'outbound',
            'amount': amount_applied,
            'currency_id': self.currency_id.id,
            'partner_id': self.request_id.partner_id and self.request_id.partner_id.id or self.request_id.user_id.partner_id.id,
            'partner_type': 'supplier',
            'payment_request_id': self.request_id.id,
            'is_prepaid': prepayment,

            'account_analytic_id': self.request_id.account_analytic_id and self.request_id.account_analytic_id.id or False,
            'payment_method_id': self.request_id.payment_method_id and self.request_id.payment_method_id.id or (self.env.ref('account.account_payment_method_manual_out') and self.env.ref('account.account_payment_method_manual_out').id or False),

            'bank_id': self.request_id.bank_id and self.request_id.bank_id.id or False,
            'bank_account_id': self.request_id.bank_account_id and self.request_id.bank_account_id.id or False,
            'bank_card_issuer': self.request_id.bank_card_issuer,
            'bank_card_type': self.request_id.bank_card_type,
            'other_payment_data': self.request_id.other_payment_data,
            'bank_card_id': self.request_id.bank_card_id and self.request_id.bank_card_id.id or False,
        }

        if self.type == 'invoice':
            res['invoice_ids'] = [(4, self.res_id, None)]
            res['writeoff_account_id'] = self.env['account.invoice'].browse(self.res_id).account_id.id

        return res

    @api.multi
    def create_prepayment(self):
        ap = self.env['account.payment']
        if self.pay:
            ap_id = ap.create(self._prepare_payment(prepayment=True))
        return True

    @api.multi
    def create_payment(self):
        ap = self.env['account.payment']
        move_line_pool = self.env['account.move.line']
        if self.pay:
            aj = self.env['account.journal']
            ajs = aj.search([('type', 'in', ['bank', 'cash'])])

            ap_id = ap.create(self._prepare_payment(prepayment=False))
            """move_line_ids = move_line_pool.search([('state', '=', 'valid'), ('account_id.type', '=', 'payable'),
                                                   ('reconcile_id', '=', False),
                                                   ('partner_id', '=', self.request_id.partner_id.id)])

            if self.type == 'invoice':
                for line in move_line_ids:
                    amount_applied = 0.0

                    if self.currency_id and self.currency_id != self.request_id.company_id.currency_id:
                        amount_applied = self.currency_id.compute(self.amount_applied,
                                                                  self.request_id.company_id.currency_id)
                    else:
                        amount_applied = self.amount_applied

                    if line.invoice.id == self.res_id:
                        av_id.write({'line_dr_ids': [(0, 0, {'name': line.move_id.name,
                                                             'type': 'dr',
                                                             'move_line_id': line.id,
                                                             'account_id': line.account_id.id,
                                                             'amount_original': line.debit > 0.0 and line.debit or line.credit,
                                                             'amount': amount_applied,
                                                             'date_original': line.date,
                                                             'date_due': line.date_maturity,
                                                             # 'amount_unreconciled': amount_unreconciled,
                                                             'currency_id': self.currency_id.id})]})"""
                        # av_id.with_context({'invoice_id': self.res_id}).recompute_voucher_lines(self.request_id.partner_id.id, ajs and ajs[0].id or False, self.amount_applied, self.currency_id.id, 'payment', self.request_id.date_request)
        return True

    def _prepare_movement(self):
        aj = self.env['account.journal']
        ajs = aj.search([('type', 'in', ['bank', 'cash'])])
        res = {
            'journal_id': ajs and ajs[0].id or False,
            'ref': self.request_id.name,
            'date': self.request_id.date_request,
            'payment_request_id': self.request_id.id,
            'line_ids': [(0, 0, {'partner_id': self.request_id.partner_id.id,
                                 'account_id': self.request_id.partner_id.property_account_receivable_id.id,
                                 'debit': self.amount_applied,
                                 'currency_id': self.currency_id.id,
                                 })]
        }

        res = {
            'payment_request_id': self.request_id.id,
            'partner_id': self.request_id.partner_id.id,
            'ref': self.request_id.name,
            'date': self.request_id.date_request,
            'amount': self.amount_applied,
        }

        return res

    def create_movement(self):
        acm = self.env['account.cash.movement']
        if self.pay:
            acm_id = acm.create(self._prepare_movement())
        return True


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_request_id = fields.Many2one('account.payment.request', 'Payment Request')

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        base_document = False
        if self.env.context.get("default_payment_request_id"):
            base_document = self.env['account.payment.request'].browse(self.env.context.get("default_payment_request_id"))
            rec['payment_request_id'] = base_document.id
            rec['currency_id'] = base_document.amount_currency_id.id
            rec['amount'] = base_document.amount_open or base_document.amount_total or 0.0
            if base_document.journal_id:
                rec['journal_id'] = base_document.journal_id.id
            rec['communication'] = base_document.name

            if base_document.bank_id:
                rec['bank_id'] = base_document.bank_id.id
            rec['transaction_date'] = base_document.payment_date
            rec['transaction_number'] = base_document.payment_code
            rec['other_payment_data'] = base_document.no_voucher

            #We mark it as prepaid
            rec['is_prepaid'] = True
        elif self.env.context.get("default_cash_movement_id"):
            base_document = self.env['account.cash.movement'].browse(self.env.context.get("default_cash_movement_id"))
            rec['cash_movement_id'] = base_document.id
            rec['currency_id'] = base_document.currency_id.id
            rec['amount'] = base_document.amount or 0.0

        #Map accordingly
        if base_document:
            if base_document.account_analytic_id:
                rec['analytic_account_id'] = base_document.account_analytic_id.id
            if base_document.payment_type == 'outbound':
                rec['payment_type'] = 'outbound'
                rec['partner_type'] = 'supplier'
            else:
                rec['payment_type'] = 'inbound'
                rec['partner_type'] = 'customer'
            rec['partner_id'] = base_document.partner_id and base_document.partner_id.id or base_document.user_id.partner_id.id


        return rec

    @api.onchange('journal_id')
    def _onchange_journal(self):

        currency_before = self.currency_id and self.currency_id.id or False
        amount_before = self.amount or False

        res = super(AccountPayment, self)._onchange_journal()

        if self.env.context.get("default_payment_request_id") or self.env.context.get("default_cash_movement_id"):
            if currency_before:
                self.currency_id = currency_before
            if amount_before:
                self.amount = amount_before

        return res

    @api.multi
    def post(self):
        for payment in self:
            super(AccountPayment, self).post()
            request = payment.payment_request_id or (payment.cash_movement_id and payment.cash_movement_id.payment_request_id or False)
            if request:
                if request.payment_type == 'inbound':
                    request.test_inbound_paid()
                if request.payment_type == 'outbound':
                    request.test_outbound_paid()

    def action_validate_invoice_payment(self):
        """ Posts a payment used to pay an invoice. This function only posts the
        payment by default but can be overridden to apply specific post or pre-processing.
        It is called by the "validate" button of the popup window
        triggered on invoice form by the "Register Payment" button.
        """

        if any(len(record.invoice_ids) != 1 for record in self)  and not self.env.context['active_model'] == 'account.payment.request':
            # For multiple invoices, there is account.register.payments wizard
            raise UserError(_("This method should only be called to process a single invoice's payment."))
        return self.post()


class AccountCashMovement(models.Model):
    _inherit = 'account.cash.movement'

    payment_request_id = fields.Many2one('account.payment.request', 'Payment Request')
