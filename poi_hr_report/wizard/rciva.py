from odoo import models, fields, api, _, tools
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta


class RcivaPayrollWiz(models.TransientModel):
    _name = 'rciva.payroll.wiz'
    _description = 'Planilla Rc-IVA'

    payslip_run = fields.Many2one('hr.payslip.run', 'Procesamiento de Nomina')
    employee_ids = fields.Many2many('hr.employee', string='Empleados')
    date_from = fields.Date('Periodo', default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Periodo Fin', default=lambda *a: str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    analytic_id = fields.Many2many('account.analytic.account', string="Cuenta Analitica")


    @api.multi
    def open_table(self):
        data = self.read()[0]
        return self.env.ref('poi_hr_report.rciva_payroll_bol').report_action(self, data=data)
