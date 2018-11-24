# -*- encoding: utf-8 -*-
from odoo import api, models, fields
from datetime import datetime
import collections

class report_payslip_bol(models.AbstractModel):
    _name = 'report.poi_hr_report.report_payslip_bol'

    @api.model
    def get_report_values(self, docids, data=None):
        domain = []
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('poi_hr_report.report_payslip_bol')
        if data.get('payslip_run', False):
            domain.append(('payslip_run_id','=',data['payslip_run'][0]))

        if data.get('employee_id', False):
            domain.append(('employee_id','in',data['employee_id']))

        if data.get('date_from', False):
            domain.append( ('date_from', '>=', data['date_from']))
        if data.get('date_to', False):
            domain.append( ('date_to', '<=', data['date_to']))

        if data.get('analytic_id', False):
            c_ids = self.env['hr.contract'].search([('analytic_account_id', 'in', data['analytic_id']), ('state', '=', 'open')])
            emp_ids = []
            for c_id in c_ids:
                emp_ids.append(c_id.employee_id.id)
            domain.append(('employee_id','in',emp_ids))

        if data.get('only_posted', False):
             domain.append(('state','=', 'done'))

        payslips = self.env['hr.payslip'].search(domain)

        rules_ids = self.env['hr.salary.rule'].search([('report_id_1', '=', report.id)])



        rules_t = {}
        for p in payslips:
            for r in p.details_by_salary_rule_category.filtered(lambda x: x.salary_rule_id.on_report_1 == True and x.salary_rule_id.report_id_1 and x.salary_rule_id.report_id_1.report_name == 'poi_hr_report.report_payslip_bol').sorted(key=lambda r: r.salary_rule_id.sequence_report_1):
                if r.salary_rule_id.sequence_report_1 not in rules_t:
                    rules_t.update({r.salary_rule_id.sequence_report_1: r.total})
                else:
                    rules_t.update({r.salary_rule_id.sequence_report_1: r.total + rules_t[r.salary_rule_id.sequence_report_1] })

        rules_t = collections.OrderedDict(sorted(rules_t.items()))

        month = 0
        if data.get('date_from', False):
            month = datetime.strptime(data['date_from'], '%Y-%m-%d').month
        elif data.get('payslip_run', False):
            run_id = self.env['hr.payslip.run'].browse(data['payslip_run'][0])
            month = datetime.strptime(run_id.date_start, '%Y-%m-%d').month
        return {

            'doc_ids': self._ids,
            'doc_model': 'hr.payslip',
            'rules': rules_ids,
            'payslips': payslips,
            'rules_t': rules_t,
            'company_id': self.env.user.company_id,
            'report': report,
            'month': self.month_get(month),
        }

        # return {
        #     'doc_ids': self.ids,
        #     'doc_model': self.model,
        #     'data': data['form'],
        #     'docs': docs,
        #     'time': time,
        #     'Accounts': account_res,
        # }

    @api.model
    def render_html(self, docids, data=None):
        domain = []
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_hr_report.report_payslip_bol')
        if data.get('payslip_run', False):
            domain.append(('payslip_run_id','=',data['payslip_run'][0]))

        if data.get('employee_id', False):
            domain.append(('employee_id','in',data['employee_id']))

        if data.get('date_from', False):
            domain.append( ('date_from', '>=', data['date_from']))
        if data.get('date_to', False):
            domain.append( ('date_to', '<=', data['date_to']))

        if data.get('analytic_id', False):
            c_ids = self.env['hr.contract'].search([('analytic_account_id', 'in', data['analytic_id']), ('state', '=', 'open')])
            emp_ids = []
            for c_id in c_ids:
                emp_ids.append(c_id.employee_id.id)
            domain.append(('employee_id','in',emp_ids))

        if data.get('only_posted', False):
             domain.append(('state','=', 'done'))

        payslips = self.env['hr.payslip'].search(domain)

        rules_ids = self.env['hr.salary.rule'].search([('report_id_1', '=', report.id)])



        rules_t = {}
        for p in payslips:
            for r in p.details_by_salary_rule_category.filtered(lambda x: x.salary_rule_id.on_report_1 == True and x.salary_rule_id.report_id_1 and x.salary_rule_id.report_id_1.report_name == 'poi_hr_report.report_payslip_bol').sorted(key=lambda r: r.salary_rule_id.sequence_report_1):
                if r.salary_rule_id.sequence_report_1 not in rules_t:
                    rules_t.update({r.salary_rule_id.sequence_report_1: r.total})
                else:
                    rules_t.update({r.salary_rule_id.sequence_report_1: r.total + rules_t[r.salary_rule_id.sequence_report_1] })

        rules_t = collections.OrderedDict(sorted(rules_t.items()))

        month = 0
        if data.get('date_from', False):
            month = datetime.strptime(data['date_from'], '%Y-%m-%d').month
        elif data.get('payslip_run', False):
            run_id = self.env['hr.payslip.run'].browse(data['payslip_run'][0])
            month = datetime.strptime(run_id.date_start, '%Y-%m-%d').month
        docargs = {

            'doc_ids': self._ids,
            'doc_model': 'hr.payslip',
            'rules': rules_ids,
            'payslips': payslips,
            'rules_t': rules_t,
            'company_id': self.env.user.company_id,
            'report': report,
            'month': self.month_get(month),
        }


        return report_obj.render('poi_hr_report.report_payslip_bol', docargs)



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
