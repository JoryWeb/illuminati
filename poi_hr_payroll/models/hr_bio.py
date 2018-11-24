import time
from datetime import date
from datetime import datetime
from dateutil import relativedelta
from odoo import models, fields, api, _, tools
from odoo.osv import expression

class HrBio(models.Model):
    _name = 'hr.bio'
    _description = 'Biometrico'

    name = fields.Char('Descripcion', required=True)
    date_start = fields.Date('Periodo', default=lambda *a: time.strftime('%Y-%m-01'))
    date_end = fields.Date('Periodo Fin', default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    state = fields.Selection([
        ('draft', 'Abierto'),
        ('close', 'Cerrado')], 'Estado', default="draft")
    line_ids = fields.One2many('hr.bio.line', 'bio_id', 'Lineas Biometrico')


    @api.multi
    def hr_done_bio(self):
        return self.write({'state': 'done'})

    @api.multi
    def hr_process_bio(self):
        planing_obj = self.env['hr.planing']
        holidays_obj = self.env['hr.holidays']
        table = []
        if self.company_id:
            table = expression.AND([table]+[[('company_id', '=', self.company_id.id)]])
        table = expression.AND([table]+[[('period_id', '=', self.period_id.id)]])
        planing_ids = planing_obj.search(table)
        for l in self.line_ids:
            holidays_ids = holidays_obj.search(expression.AND([table]+[[('date_from', '>=', l.date),('date_to', '<=', l.date)]]))
            for h in holidays_ids:
                l.note = h.name
                l.state = 'c'
                l.edit = True
        return True


class HrBioLine(models.Model):
    _name = 'hr.bio.line'
    _description = 'Lineas del Biometrico'
    _order = "employee_id asc, date asc, date_in asc"

    bio_id = fields.Many2one('hr.bio', 'Biometrico')
    employee_id = fields.Many2one('hr.employee', 'Empleado', required=True)
    date = fields.Date('Fecha', inverse="_get_state")
    date_in = fields.Float('Hora de Ingreso', inverse="_get_state")
    date_out = fields.Float('Hora de Salida', inverse="_get_state")
    working_hours = fields.Many2one('resource.calendar', 'Planificacion de Trabajo')
    note = fields.Char('Observaciones')
    state = fields.Selection([
        ('i', 'Importado'),
        ('m', 'Correccion Manual'),
        ('s', 'Corregido Sistema')], 'Estado', default="i")
    retraso = fields.Float('Retraso', inverse="_get_state")
    edit = fields.Boolean('Editado', readonly=True)

    @api.multi
    def _get_state(self):
        for s in self:
            self.state = 'm'
            self.edit = True


class HrBioConfig(models.Model):
    _name = 'hr.bio.config'
    _description = ' Configuracion Biometrico'

    name = fields.Char('name')
    active = fields.Boolean('Activo', default=False)
    delay_time = fields.Float('Tiempo de Retraso Permitido')
    company_id = fields.Many2one('res.company')
