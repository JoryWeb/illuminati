#!/usr/local/bin/python
from odoo import models, fields, api, _, tools

class HrAccident(models.Model):
    _name = 'hr.accident'
    _description = 'Registro de Accidentes del lo Empleados'

    name = fields.Char('Descripcion', required=True)
    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True)
    type = fields.Selection([
    	('a', 'Accidente'),
    	('am', 'Accidente con Muerte'),
    	('e', 'Enfermedad'),], string="Tipo", required=True)
    category_id = fields.Many2one('hr.accident.category', string='Categoria')
    date = fields.Date('Fecha del Accidente')
    # period_id = fields.Many2one('hr.period', string='Periodo', required=True)
    note = fields.Text('Notas')

class HrAccidentCategory(models.Model):
    _name = 'hr.accident.category'
    _description = 'Categorias del Accidente'

    name = fields.Char('Categoria', required=True)
    note = fields.Text('Descripcion')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _accident_count(self):
        allowance = self.env['hr.accident']
        for s in self:
            s.accident_count = allowance.search_count([('employee_id', '=', s.id)])

    accident_count = fields.Integer(compute="_accident_count", string="Subcidios")
