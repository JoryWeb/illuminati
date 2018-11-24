# -*- encoding: utf-8 -*-
from odoo import api, models, exceptions
from datetime import datetime

class report_voucher_bol(models.AbstractModel):
    _name = 'report.poi_hr_report.report_voucher_bol'

    @api.model
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        config = self.env['hr.voucher.config']
        config_ids = config.search([('id','>', 0)], order="sequence asc")
        report = report_obj._get_report_from_name('poi_hr_report.report_voucher_bol')
        voucher = self.env[report.model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(docids),
            'config_ids': config_ids,
            'employee_payslip_line': self.employee_payslip_line,
            'date': self.date,
        }


    def employee_payslip_line(self, id, code):
        r = self.env['hr.payslip.line'].search([('slip_id','=', id), ('code', '=', code)])
        if r:
            return  r[0].amount
        else:
            return 0

    def date(self, date):
        y, m, d = date.split('-')
        meses = (
            {'mes': '01', 'val': 'Enero'},
            {'mes': '02', 'val': 'Febrero'},
            {'mes': '03', 'val': 'Marzo'},
            {'mes': '04', 'val': 'Abril'},
            {'mes': '05', 'val': 'Mayo'},
            {'mes': '06', 'val': 'Junio'},
            {'mes': '07', 'val': 'Julio'},
            {'mes': '08', 'val': 'Agosto'},
            {'mes': '09', 'val': 'Septiembre'},
            {'mes': '10', 'val': 'Octubre'},
            {'mes': '11', 'val': 'Noviembre'},
            {'mes': '12', 'val': 'Diciembre'},
        )
        f = datetime.strptime(date, '%Y-%m-%d')
        mes = next(filter(lambda x: x['mes'] == m, meses))
        return {
            'dia': d,
            'dia_l': f.strftime("%A"),
            'mes': mes['val'],
            'year': y,
        }
