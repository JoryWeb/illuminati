##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Poiesis Consulting
#    autor: Grover Menacho
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


from openerp.osv import fields,osv
import openerp.tools
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.report import report_sxw
from openerp import models, fields, api, _, tools
import time
from datetime import datetime, timedelta
from openerp.osv import expression
from openerp import SUPERUSER_ID


class report_kardex_wizard(models.TransientModel):
    """
    For Reporte kardex valorado
    """
    _inherit = "poi.report.kardex.wizard"


    @api.multi
    def view_kardex_graph_stock(self):

        data = self.read()[0]

        report_domain = []

        if data['date_from']:
            date_from = str(data['date_from'])
            domain = [('date','>=',date_from + ' 00:00:00')]
            report_domain = expression.AND([domain] + [report_domain])
        if data['date_to']:
            date_to = str(data['date_to'])
            domain = [('date','<=',date_to + ' 23:59:59')]
            report_domain = expression.AND([domain] + [report_domain])
        if data['product_id']:
            product_id = str(data['product_id'][0])
            domain = [('product_id','=',int(product_id))]
            report_domain = expression.AND([domain] + [report_domain])
        if data['location_id']:
            location_id = str(data['location_id'][0])
            domain = [('location_id','=',int(location_id))]
            report_domain = expression.AND([domain] + [report_domain])

        # self.env['m.report.view'].check_and_refresh_materialized_view("poi_report_kardex_inv")
        self.env['m.report.view'].check_and_refresh_materialized_view("poi_stock_kardex_analysis")

        data_obj = self.pool.get('ir.model.data')
        model_data_id = self.env['ir.model.data']._get_id('poi_logistic_analysis_stock', 'view_poi_stock_kardex_analysis_graph')
        res_id = self.env['ir.model.data'].browse(model_data_id).res_id
        return {
            'domain': report_domain,
            'name': _('Stock Statistics'),
            'view_type': 'form',
            'view_mode': 'chart',
            'res_model': 'poi.stock.kardex.analysis',
            'view_id': res_id,
            'context': {},
            'type': 'ir.actions.act_window'
        }