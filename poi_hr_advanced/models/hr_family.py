import logging
from odoo import fields, models, api, _
from datetime import datetime, date

_logger = logging.getLogger(__name__)


class HrEmployeeFamily(models.Model):
    _name = 'hr.employee.family'
    _description = 'Familia del Empleado'

    @api.one
    @api.depends('date_born')
    def _get_age(self):
        for s in self:
            if not s.date_born:
                return True
            today = date.today()
            born = datetime.strptime(s.date_born, "%Y-%m-%d").date()
            s.age =  today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    employee_id = fields.Many2one('hr.employee','Empleado')
    name = fields.Char('Datos del Familiar')
    date_born = fields.Date('Fecha de Nacimiento')
    age = fields.Integer('Edad', compute="_get_age", readonly=True)
    code_aseg = fields.Char('Matricula Seguro')
    note = fields.Text('Notas')
    # company_id = fields.Many2one('res.company', string='Compañia', related="employee_id.company_id", store=True, readonly=True)
    relationship = fields.Selection([
        ('h', 'Hijo(a)'),
        ('c', 'Esposo(a)'),
        ('p', 'Padres'),
        ('o', 'Otro'),
        ], 'Parentesco', default="h")
    occupation_id = fields.Many2one('hr.family.occupation', 'Ocupacion')


class HrFamilyOccupation(models.Model):
    _name = 'hr.family.occupation'
    _description = 'Ocupacion'

    name = fields.Char('Ocupacion')
