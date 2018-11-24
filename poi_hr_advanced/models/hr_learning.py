from odoo import models, fields, api, _, tools

class HrLearningPlace(models.Model):
    _name = 'hr.learning.place'
    _description = 'Educacion y Experiencias del Empleado'

    name = fields.Char('Lugar')


class HrLearningType(models.Model):
    _name = 'hr.learning.type'
    _description = 'Educacion y Experiencias del Empleado'

    name = fields.Char('Tipo')


class HrLearning(models.Model):
    _name = 'hr.learning'
    _description = 'Educacion y Experiencias del Empleado'

    employee_id = fields.Many2one('hr.employee', 'Empleado')
    note = fields.Text('Descripcion')
    date_from = fields.Date('De')
    date_to = fields.Date('Hasta')
    place = fields.Many2one('hr.learning.place', 'Lugar')
    type_id = fields.Many2one('hr.learning.type', 'Tipo')
    internal = fields.Boolean('Interno', help="Al Marcar esta opcion, La experiencia o educacion se llevo dentro de la Empresa ")
    company_id = fields.Many2one('res.company', 'Compañia', related="employee_id.company_id", store=True, readonly=True)

class HrEmployee(models.Model):
    _description = 'Empleado'
    _inherit = 'hr.employee'

    @api.multi
    def _learning_count(self):
        allowance = self.env['hr.learning']
        for s in self:
            s.learning_count = allowance.search_count([('employee_id', '=', s.id)])

    learning_count = fields.Integer(compute="_learning_count", string="Subcidios")
