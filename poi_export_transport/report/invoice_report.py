#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, models

from odoo.addons.poi_bol_base.models.amount_to_text_es import to_word, MONEDAS


class ReportInvoiceExport(models.AbstractModel):
    _name = 'report.poi_sale_export.invoice_export_template'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_sale_export.invoice_export_template')
        inv_id = self.env[report.model].browse(self._ids)
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': inv_id,
            'to_word': to_word,
        }

        if inv_id and inv_id.tipo_fac == '13':
            return report_obj.render('poi_sale_export.invoice_export_template', docargs)

        return report_obj.render('poi_bol_cc.basic_invoice', docargs)
