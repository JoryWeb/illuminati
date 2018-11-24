#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from openerp import api, models, fields, api, _, tools
from openerp.osv import osv


class ReportSaleOrder(models.AbstractModel):
    _name = 'report.sale.report_saleorder'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_x_implelab_report.sale_order_template_imp')
        order_id = self.env[report.model].browse(self.ids)



        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': order_id,
        }


        return report_obj.render(report.report_name, docargs)
