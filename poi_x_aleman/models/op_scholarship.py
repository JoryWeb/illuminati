# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning


class OpScholarship(models.Model):
    _name = "op.scholarship"

    name = fields.Char("Descripcion")
    line_ids = fields.One2many("op.scholarship.line", 'scholarship_id', 'Becas y Descuentos')
    state = fields.Selection(
        string="Estado",
        selection=[
                ('draft', 'Inicial'),
                ('active', 'Activo'),
                ('archive', 'Archivado'),
        ], default='draft', readonly=True, states={'draft':[('readonly',False)]}
    )

class OpScholarshipLine(models.Model):
    _name = "op.scholarship.line"

    scholarship_id = fields.Many2one("op.scholarship", "Becas y Descuentos")
    name = fields.Char("Nombre")
    discount = fields.Float("Descuento")
    dicount_total = fields.Float('Descuento Total')

    apply_first = fields.Boolean("Aplica Primera Pension")
    apply_regular = fields.Boolean("Aplica Pesion Regular")
    active = fields.Boolean("Activo")

    is_regular = fields.Boolean("Es Regular")
    is_scholarship = fields.Boolean("Es Becado")
    is_child_local = fields.Boolean("Es hijo de Funcionario Local")
    is_child_foreign = fields.Boolean("Es hijo de Funcionario Extranjero")
