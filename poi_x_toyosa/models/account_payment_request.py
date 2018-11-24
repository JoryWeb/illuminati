from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    no_file = fields.Char("No. File")

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        if self.env.context.get("default_payment_request_id"):
            payment_request_id_default = self.env['account.payment.request'].browse(
                self.env.context.get("default_payment_request_id"))
            rec['no_file'] = payment_request_id_default.no_file or ''
        return rec

class AccountPaymentRequest(models.Model):
    _inherit = 'account.payment.request'

    sale_order_id = fields.Many2one("sale.order", "Orden de Venta")
    lot_id = fields.Many2one("stock.production.lot", "Chasis")
    lot_id_displayed = fields.Many2one("stock.production.lot", "Chasis", related="lot_id")
    case = fields.Selection([('cobranza', 'Cobranza'),
                             ('banco', 'Banco')], string="Caso")

    no_file = fields.Char("No. File")
    no_voucher = fields.Char("No. Voucher")
    bank_id = fields.Many2one("res.bank","Banco")
    payment_date = fields.Date(u"Fecha de Depósito")
    payment_code = fields.Char(u"Código de Depósito")

    @api.multi
    @api.depends('analytic_account_id')
    def _get_first_analytic_account(self):
        for s in self:
            if s.account_analytic_id:
                s.analytic_main_tag = s.account_analytic_id.main_tag
                s.analytic_main_tag_parent = s.account_analytic_id.main_tag_parent

    analytic_account_id = fields.Many2one("account.analytic.account", "Analytic Account", compute=_get_first_analytic_account, store=True)
    analytic_main_tag = fields.Char(u'Categoría', compute=_get_first_analytic_account, store=True)
    analytic_main_tag_parent = fields.Char(u'Categoría raíz', compute=_get_first_analytic_account, store=True)

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        lot_id = False
        if self.sale_order_id:
            for line in self.sale_order_id.order_line:
                if line.lot_id:
                    lot_id = line.lot_id.id
        self.lot_id = lot_id

    @api.multi
    def _prepare_new_payment(self):
        res = super(AccountPaymentRequest, self)._prepare_new_payment()
        res['order_id'] = self.sale_order_id and self.sale_order_id.id or False

        return res
