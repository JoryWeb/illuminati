import time
from datetime import datetime
from odoo import models, fields, api, _, tools
from dateutil.relativedelta import relativedelta

class HrPlaning(models.Model):
    _name = 'hr.planing'
    _description = 'Planificacion de Trabajo Avanzada'

    name = fields.Char('Descripcion', required=True, readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char('Codigo')
    # period_id = fields.Many2one('hr.period', string='Periodo', readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date('Periodo', default=lambda *a: time.strftime('%Y-%m-01'))
    date_end = fields.Date('Periodo Fin', default=lambda *a: str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self._context.get('company_id', self.env.user.company_id.id), readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
    	('draft', 'Abierto'),
    	('done', 'Cerrado')], 'Estado', default="draft")
    line = fields.One2many('hr.planing.line', 'planing_id', 'lineas de Planeacion', readonly=True, states={'draft': [('readonly', False)]})

    @api.multi
    def hr_update_planing(self):
        return self.write({'state': 'done'})

class HrPlaningLine(models.Model):
    _name = 'hr.planing.line'
    _description = 'Planificacion de Trabajo'
    _order = "name asc"

    @api.multi
    @api.depends('employee_id')
    def _get_department(self):
        for s in self:
            s.department_id = s.employee_id.department_id

    @api.multi
    @api.depends('employee_id')
    def _get_company(self):
        for s in self:
            s.company_id = s.employee_id.company_id


    planing_id = fields.Many2one('hr.planing', 'Planeacion', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True)
    name = fields.Char('Nombre', related="employee_id.name", store=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Departamento', compute="_get_department")
    #new_department = fields.Many2one('hr.department', 'Departamento Destino', help="Si se ecuentra en blanco no tendra ninguna modificacion")
    company_id = fields.Many2one('res.company', related="employee_id.company_id", string='Compañia', compute="_get_company")
    working_hours = fields.Many2one('resource.calendar', 'Planificacion de Trabajo')
    company_id = fields.Many2one('res.company', 'Compañia', related="employee_id.company_id", store=True, readonly=True)
