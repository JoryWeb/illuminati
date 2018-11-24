#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from odoo import api, models, fields

class report_poi_hr_advanced_memo(models.AbstractModel):
    _name = 'report.poi_hr_advanced.memo_print'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']

        report = report_obj._get_report_from_name('poi_hr_advanced.memo_print')

        docs = self.env[report.model].browse(self._ids)

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self._ids),
            'smart_truncate': self.smart_truncate,
        }

        return report_obj.render('poi_hr_advanced.memo_print', docargs)

    def smart_truncate(self, content, length=36, suffix=''):
        if len(content) <= length:
            return content
        else:
            return ' '.join(content[:length+1].split(' ')[0:-1]) + suffix
