# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api
from odoo.exceptions import Warning, ValidationError


class NotaeReport(models.AbstractModel):
    _name = 'report.poi_x_toyosa_report.hojan_report_template'

    @api.multi
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('poi_x_toyosa_report.diary_book_template')
        docs = self.env[report.model].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
