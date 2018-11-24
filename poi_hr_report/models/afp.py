import logging
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class HrAfps(models.Model):
    _inherit = "hr.afps"

    on_report = fields.Boolean("Aparece en Reporte", default=False)
    sequence = fields.Integer('Secuencia')
    line_ids = fields.One2many('hr.afps.report.line', 'afp_id', string="Lineas de Reporte")
    amount_total = fields.Float('Total', compute="_compute_total")


    @api.multi
    def _compute_total(self):
        for s in self:
            s.amount_total = sum(l.total for l in s.line_ids)


class HrAfpConfigLine(models.Model):
    _name = "hr.afps.report.line"
    _description = "Configuracion Reportes"

    afp_id = fields.Many2one('hr.afps', string="Afp", ondelete='cascade', index=True)
    name = fields.Char(string="Nombre en Reporte")
    salary_rules_id = fields.Many2one('hr.salary.rule', 'Regla Salarial')
    note = fields.Char('Nota')
    sequence = fields.Integer('Secuencia')
    group_id = fields.Many2one('hr.report.config.group', 'Grupo')
    total = fields.Float('Total', compute="_compute_total")

    @api.multi
    def _compute_total(self):
        if self.env.context.get('employee_domain', False):
            domain = self.env.context.get('employee_domain', False)
            pay_obj = self.env['hr.payslip']
            payslip_ids = pay_obj.search(domain)
            for s in self:
                total = 0
                for p in pay_obj.search([('employee_id.afp_id', '=', s.afp_id.id),('id', '=', payslip_ids.ids)]):
                    total += sum(l.total for l in p.details_by_salary_rule_category.filtered(lambda x: x.salary_rule_id.id == s.salary_rules_id.id))
                s.total = total
        else:
            for s in self:
                s.total = 0
