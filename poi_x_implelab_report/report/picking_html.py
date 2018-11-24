#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from openerp import api, models, fields, api, _, tools
from openerp.osv import osv


class ReportSaleOrder(models.AbstractModel):
    _name = 'report.poi_x_implelab_report.stock_picking_imp_html'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_x_implelab_report.stock_picking_imp_html')
        picking_id = self.env[report.model].browse(self.ids)
        sale_id = picking_id.sale_id

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': picking_id,
            'order_id': sale_id,
            'get_price': self._get_price,
        }


        return report_obj.render(report.report_name, docargs)

    @api.multi
    def _get_price(self, product_id, order_id):
        price = 0.0
        if product_id:
            line_ids = order_id.order_line.filtered(lambda r: r.product_id.id == product_id)
            for l in line_ids:
                price = l.unitario_factor
                break
        return price

    # @api.multi
    # def _get_total(self, product_id, quantity, order_id):
    #     price = 0.0
    #     total = 0.0
    #     if product_id:
    #         line_ids = order_id.order_line.filtered(lambda r: r.product_id.id == product_id)
    #         for l in line_ids:
    #             price = l.price_unit
    #             total = price * quantity
    #             break
    #     return total
