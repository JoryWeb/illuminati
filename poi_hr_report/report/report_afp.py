# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api, _, tools
from datetime import datetime

class report_report_afp(models.AbstractModel):
    _name = 'report.poi_hr_report.report_afp'

    @api.model
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('poi_hr_report.report_afp')
        domain = []
        if data['payslip_run']:
            domain.append(('payslip_run_id','=',data['payslip_run'][0]))

        if data['employee_ids']:
            domain.append(('employee_id','in',data['employee_ids']))

        if data.get('date_from', False):
            domain.append( ('date_from', '>=', data['date_from']))
        if data.get('date_to', False):
            domain.append( ('date_to', '<=', data['date_to']))

        if data['analytic_id']:
            c_ids = self.env['hr.contract'].search([('analytic_account_id', 'in', data['analytic_id'])])
            emp_ids = []
            for c_id in c_ids:
                emp_ids.append(c_id.employee_id.id)
            domain.append(('employee_id','in',emp_ids))


        afp_ids = self.env['hr.afps'].with_context(employee_domain =domain).search([('on_report', '=', True)])

        month = 0
        if data.get('date_from', False):
            month = datetime.strptime(data['date_from'], '%Y-%m-%d').month
        elif data.get('payslip_run', False):
            run_id = self.env['hr.payslip.run'].browse(data['payslip_run'][0])
            month = datetime.strptime(run_id.date_start, '%Y-%m-%d').month

        return {

            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env.user.company_id,
            'afp': afp_ids,
            'month': self.month_get(month),
        }



    def month_get(self, month=0):
        name = ''
        if month == 1:
            name = 'Enero'
        elif month == 2:
            name = 'Febrero'
        elif month == 3:
            name = 'Marzo'
        elif month == 4:
            name = 'Abril'
        elif month == 5:
            name = 'Mayo'
        elif month == 6:
            name = 'Junio'
        elif month == 7:
            name = 'Julio'
        elif month == 8:
            name = 'Agosto'
        elif month == 9:
            name = 'Septiembre'
        elif month == 10:
            name = 'Octubre'
        elif month == 11:
            name = 'Noviembre'
        elif month == 12:
            name = 'Diciembre'
        elif month == 0:
            name = ''
        return name
