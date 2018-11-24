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
            'date': self.get_date,
            'storage':{'test':0},
        })


    def myset(self, pair):
        if isinstance(pair, dict):
            self.localcontext['storage'].update(pair)
        return False

    def myget(self, key):
        if key in self.localcontext['storage']:
            return self.localcontext['storage'][key]
        return False

    def get_date(self, date):
        if date:
            datetime_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            date = datetime_object.strftime("%d/%m/%Y")
            return date
#
# class report_kardex_printer(osv.AbstractModel):
#     _name = 'report.poi_x_implelab_report.purchase_template_imp_html'
#     _inherit = 'report.abstract_report'
#     _template = 'poi_x_implelab_report.purchase_template_imp_html'
#     _wrapped_report_class = Parser
