#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api, _, tools
from odoo.addons.poi_bol_base.models.amount_to_text_es import to_word, MONEDAS

class ReportHrFiniquito(models.AbstractModel):
    _name = 'report.poi_hr_payroll.finiquito_template'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_hr_payroll.finiquito_template')

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self._ids),
            'to_word': to_word,
        }

        return report_obj.render('poi_hr_payroll.finiquito_template', docargs)
