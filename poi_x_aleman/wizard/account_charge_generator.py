# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning

class AccountCharge(models.TransientModel):
    _name = "account.op.charge.wiz"

    type = fields.Selection(
        string="Tipo",
        selection=[
                ('student', 'Alumno'),
                ('course', 'Clase'),
                ('all', 'Todos'),
        ])

    student_id = fields.Many2one('op.student', 'Alumno')
    course_id = fields.Many2one('op.course', 'Curso')
    type_charge = fields.Many2one('account.op.charge.type', 'Tipo de Cargo', required=True)
    date = fields.Date('Fecha', default=fields.Date.today(), required=True)

    @api.multi
    def action_generate(self):
        return
