#!/usr/local/bin/python
from odoo import models, fields, api, _, tools
from odoo.tools.translate import _

class HrForm110(models.Model):
    _name = 'hr.form110'
    _description = 'Carga la datos del Formulario 110'

    name = fields.Char('Descripcion', required=True, readonly=True, states={'draft': [('readonly', False)]}, default="Formulario 110")
    employee_id = fields.Many2one('hr.employee', 'Empleado', readonly=True,  required=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', 'Contrato', readonly=True, states={'draft': [('readonly', False)]}, required=True,)
    company_id = fields.Many2one('res.company',  string='Compañia', related="employee_id.company_id", store=True, readonly=True)
    date = fields.Date(string='Fecha', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=fields.Date.today())
    amount = fields.Float('Monto', required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('process', 'En Cola de Proceso'),
        ('done', 'Confirmado'),
        ('cancel', 'Cancelado')], string="Estado", default="draft", readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char('Codigo', default='F110', readonly=True)
    payslip_id = fields.Many2one('hr.payslip', 'Nomina', readonly=True)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id.contract_id:
            self.contract_id = self.employee_id.contract_id.id

    @api.multi
    def cancel_form110(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def hr_done_form110(self):
        return self.write({'state': 'done'})

    @api.multi
    def hr_process_form110(self):
        return self.write({'state': 'process'})
