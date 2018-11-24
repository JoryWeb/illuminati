#!/usr/bin/env python
 # -*- encoding: utf-8 -*-
from openerp import api, models, fields, api, _, tools
from openerp.osv import osv
from openerp.report import report_sxw
from datetime import datetime

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.context = context
        self.localcontext.update({
            'myset':self.myset,
            'myget':self.myget,
            'date': self.check_date,
            'date2': self.check_date2,
            'storage':{
                'test':0.00,
                'total':0.00,
            },
            'check_price': self.check_price_r,
        })


    def myset(self, pair):
        if isinstance(pair, dict):
            self.localcontext['storage'].update(pair)
        return False

    def myget(self, key):
        if key in self.localcontext['storage']:
            return self.localcontext['storage'][key]
        return False

    def check_date(self, date):
        if date:
            datetime_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            date = datetime_object.strftime("%d/%m/%Y")
            return date

    def check_date2(self, date):
        if date:
            datetime_object = datetime.strptime(date, '%Y-%m-%d')
            date = datetime_object.strftime("%d/%m/%Y")
            return date


    def check_price_r(self, product_id=False, order_id=False):
        price = 0.0
        if product_id:
            line_ids = order_id.order_line.filtered(lambda r: r.product_id.id == product_id)
            for l in line_ids:
                price = l.unitario_factor
                break
        return price

class ReportPickingLeftImp(models.AbstractModel):
    _name = 'report.poi_x_implelab_report.stock_picking_imp'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_x_implelab_report.stock_picking_imp')
        picking_id = self.env[report.model].browse(self.ids)
        sale_id = picking_id.sale_id

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': picking_id,
            'order_id': sale_id,
            'check_price': self.check_price_r,
        }


        return report_obj.render(report.report_name, docargs)

    @api.multi
    def check_price_r(self, product_id=False, order_id=False):
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
