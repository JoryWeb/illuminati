#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from openerp import api, models, fields, api, _, tools
from openerp.osv import osv
from openerp.addons.poi_bol_base.models.amount_to_text_es import to_word, MONEDAS
from itertools import ifilter
from openerp.report import report_sxw

class ReportAccountInvoice(models.AbstractModel):
    _name = 'report.poi_x_alina_report.account_asset_report_alina_t'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_x_alina_report.account_asset_report_alina_t')
        line_obj = self.env['account.move.line']

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self._ids),
            'to_word': to_word,
            'get_payment': self._get_payment,
            'line_obj': line_obj,

        }

        return report_obj.render('poi_x_alina_report.account_asset_report_alina_t', docargs)

    @api.multi
    def _get_payment(self, move_id):
        if move_id.src:
            model, id = move_id.src.split(",")
            if model == 'account.payment':
                payment_id = self.env[model].browse(int(id))
                return payment_id
