# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpBatch(models.Model):
    _inherit = 'op.batch'

    code = fields.Char('Code', size=16, required=False)
    start_date = fields.Date(required=False, default=fields.Date.today())
    end_date = fields.Date(required=False, default=fields.Date.today())
    course_id = fields.Many2one('op.course', 'Course', required=False)

    grade = fields.Char('Grado', required=False)
    course_level = fields.Selection(
        [('inicial', 'Inicial'), ('primaria', 'Primaria'), ('secundaria', 'Secundaria')],
        'Nivel de Curso')

