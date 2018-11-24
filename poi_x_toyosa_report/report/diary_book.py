# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api
from odoo.exceptions import Warning, ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    total_debit = fields.Float('Total Debito', compute="_compute_total")
    total_credit = fields.Float('Total Haber', compute="_compute_total")
    total_debit_sec = fields.Float('Total Debito', compute="_compute_total")
    total_credit_sec = fields.Float('Total Haber', compute="_compute_total")

    @api.one
    @api.depends('line_ids')
    def _compute_total(self):
        for line in self.line_ids:
            self.total_debit += line.debit
            self.total_credit += line.credit
            self.total_debit_sec += line.debit_sec
            self.total_credit_sec += line.credit_sec



class NotaeReport(models.AbstractModel):
    _name = 'report.poi_x_toyosa_report.diary_book_template'

    @api.multi
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('poi_x_toyosa_report.diary_book_template')
        docs = self.env[report.model].search([('date','=',data['date'])])

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
