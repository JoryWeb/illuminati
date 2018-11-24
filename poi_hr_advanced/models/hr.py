import logging
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class HrEmployeeReason(models.Model):
    _name = 'hr.employee.reason'
    _description = "Motivos de la baja o Despido"

    name = fields.Char('Descripcion')
    note = fields.Text('Detalle')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    @api.multi
    @api.depends('family_ids')
    def _get_children(self):
        for s in self:
            h = 0
            for f in s.family_ids:
                if f.relationship == 'h':
                    h = h + 1
            s.children = h

    @api.multi
    @api.depends('birthday')
    def _compute_age(self):
        for s in self:
            if not s.birthday:
                return True
            today = date.today()
            born = datetime.strptime(s.birthday, "%Y-%m-%d").date()
            s.age =  today.year - born.year - ((today.month, today.day) < (born.month, born.day))


    @api.multi
    def _compute_family_count(self):
        family = self.env['hr.employee.family']
        for s in self:
            s.family_count = family.search_count([('employee_id', '=', s.id)])

    @api.multi
    def _compute_antiquity(self):
        for s in self:
            date = datetime.strptime(fields.Date.today(), "%Y-%m-%d").date()
            if s.date_entry:
                date_entry = datetime.strptime(s.date_entry, "%Y-%m-%d").date()
                s.antiquity = relativedelta(date, date_entry).years
            else:
                s.antiquity = 0

    family_count = fields.Integer(compute="_compute_family_count", string="Subcidios")
    age = fields.Integer('Edad', compute="_compute_age")
    children = fields.Integer('Numero de Hijos', compute="_get_children", default=0)
    afp_id = fields.Many2one('hr.afps', string='Aseguradora (AFP)')
    date_afp = fields.Date('Fecha de Afiliacion')
    nua = fields.Char('NUA/CUA')
    code_aseg = fields.Char('Matricula Seguro')
    family_ids = fields.One2many('hr.employee.family', 'employee_id', 'Datos Familiares')
    date_entry = fields.Date('Fecha Ingreso', help="Esta fecha sera tomada para el calculo de Antiguedad en caso de estar en blanco se tomara la fecha del contrato.")

    antiquity = fields.Integer('Antiguedad', compute="_compute_antiquity")

    emergency_contact = fields.Char('Contacto de Emergencia')
    emergency_phone = fields.Char('Telefono de Emergencia')
    black_list = fields.Boolean('Lista Negra')
    reason_id = fields.Many2one('hr.employee.reason', 'Motivo', readonly=True)

    ci = fields.Char(string='C.I.', related="address_home_id.ci", readonly=True)
    health_box = fields.Many2one('hr.health.box', 'Cajas de Salud')

    @api.multi
    def toggle_active(self):
        if not self.active:
            self.active = not self.active
        else:
            return {
                'name':_("Motivo de Desactivacion"),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'employee.reason.left',
                'type': 'ir.actions.act_window',
                'search_view_id': False,
                'target': 'new',
            }
