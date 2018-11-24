from odoo import models, fields, api, _, tools
from datetime import date

class HrOthersCode(models.Model):
    _name = "hr.others.code"
    _description = "Codigos Otras Entradas"

    code = fields.Char('Codigo', required=True)
    name = fields.Char('Nombre', required=True)
    note = fields.Text('Descripcion')



class HrOthers(models.Model):
    _name = "hr.others"
    _description = "Otras Entradas y Descuentos"

    @api.multi
    @api.depends('code_id')
    def _compute_code(self):
        for s in self:
            if s.code_id:
                s.code = s.code_id.code

    @api.multi
    def _set_code(self):
        code_obj = self.env['hr.others.code']
        for s in self:
            code_id = code_obj.search([('code', '=', s.code)], limit=1)
            if code_id:
                self.code_id = code_id[0].id


    name = fields.Char('Descripcion', readonly=True, required=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', readonly=True, string='Empleado', required=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', readonly=True, string='Contrato', states={'draft': [('readonly', False)]}, required=True)
    code_id = fields.Many2one('hr.others.code', readonly=True, string='Categoria', states={'draft': [('readonly', False)]})
    code = fields.Char('Codigo', compute="_compute_code", inverse="_set_code", readonly=True, states={'draft': [('readonly', False)]}, required=True)
    date_ref = fields.Date('Fecha Ref. Transaccion', readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Fecha', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    note = fields.Text('Notas', readonly=True, states={'draft': [('readonly', False)]})
    monto = fields.Float('Monto', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('process','En Cola de Proceso'),
        ('done', 'Realizado'),
        ('cancel', 'Cancelado'),
        ],'Status', default='draft')
    company_id = fields.Many2one('res.company', string='Compañia', related="employee_id.company_id", store=True, readonly=True)
    payslip_id = fields.Many2one('hr.payslip', 'Nomina', readonly=True)



    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id.contract_id:
            self.contract_id = self.employee_id.contract_id.id


    @api.multi
    def cancel_other_inputs(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def hr_process_other_inputs(self):
        return self.write({'state': 'process'})

    @api.multi
    def hr_done_other_inputs(self):
        return self.write({'state': 'done'})
