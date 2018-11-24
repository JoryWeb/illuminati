#!/usr/local/bin/python
from odoo import models, fields, api, _, tools


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    on_report_1 = fields.Boolean('Aparece en Reporte', default=False)
    name_1 = fields.Char('Nombre en Reporte')
    report_id_1 = fields.Many2one('ir.actions.report', 'Reporte', domain=[('model','in',['hr.payslip']), ])
    sequence_report_1 = fields.Integer('Secuencia', default=0)

    on_report_2 = fields.Boolean('Aparece en Reporte', default=False)
    name_2 = fields.Char('Nombre en Reporte')
    report_id_2 = fields.Many2one('ir.actions.report', 'Reporte', domain=[('model','in',['hr.payslip']), ])
    sequence_report_2 = fields.Integer('Secuencia', default=0)
