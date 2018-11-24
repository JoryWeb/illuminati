# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning


class AccountCharge(models.Model):
    _name = "account.op.charge.type"

    code = fields.Char('Codigo')
    name = fields.Char('Nombre')
    type = fields.Selection(
        string="Tipo",
        selection=[
                ('draft', 'Abono'),
                ('send', 'Cargo'),
        ])

class AccountCharge(models.Model):
    _name = "account.op.charge"


    @api.multi
    @api.depends("student_id")
    def _compute_data(self):
        if self.student_id:
            self.family_id

    student_id = fields.Many2one('op.student', 'Alumno', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    type_charge = fields.Many2one('account.op.charge.type', 'Tipo de Cargo', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    date = fields.Date('Fecha', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    date_due = fields.Date('Fecha de Vencimiento', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    year_id = fields.Many2one('op.year', 'Gestion Escolar', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    month_id = fields.Many2one('op.month', 'Mes', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    family_id = fields.Many2one('op.family', 'Familia', compute="_compute_data")
    course_id = fields.Many2one('op.course', 'Curso', readonly=True, compute="_compute_data")
    course_level = fields.Char('Nivel de Curso', readonly=True, compute="_compute_data")

    product_id = fields.Many2one('product.product', 'Producto', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    tax_id = fields.Many2one('account.tax', 'Impuesto', readonly=True, states={'draft':[('readonly',False)]})
    analytic_id = fields.Many2one('account.analytic.account', 'Cuenta Analitica', readonly=True, states={'draft':[('readonly',False)]})
    name = fields.Char('Descripcion', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    amount = fields.Float('Monto', readonly=True, states={'draft':[('readonly',False)]}, required=True)
    priority_id = fields.Many2one('op.priority', 'Prioridad', readonly=True, states={'draft':[('readonly',False)]})

    amount_tax = fields.Float('Impuesto', readonly=True, states={'draft':[('readonly',False)]})
    amount_total = fields.Float('Monto Total', readonly=True, states={'draft':[('readonly',False)]})

    invoice_id = fields.Many2one('account.invoice', 'Factura', readonly=True)
    payment_id = fields.Many2one('account.payment', 'Pago', readonly=True)

    to_bank = fields.Boolean('Para Facturar en Banco', readonly=True, states={'draft':[('readonly',False)]})

    state = fields.Selection(
        string="Estado",
        selection=[
                ('draft', 'Borrador'),
                ('send', 'Confirmado'),
                ('done', 'Pagado'),
                ('cancel', 'Cancelado'),
        ], default='draft', readonly=True, states={'draft':[('readonly',False)]}
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        pricelist = False
        product_id = self.product_id
        product = product_id.with_context(
            year_id=year_id,
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=1,
            date_order=self.date,
            pricelist=pricelist_id,
        )
        price_unit = self._get_display_price(product)
        self.price_unit = price_unit

    @api.multi
    def action_send(self):
        self.state = 'send'

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'
