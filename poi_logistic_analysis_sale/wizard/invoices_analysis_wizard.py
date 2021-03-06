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


class invoices_analysis_wizard(models.TransientModel):
    _name = "invoices.analysis.wizard"
    _description = "Invoices analysis Wizard"

    shop_id = fields.Many2one('stock.warehouse','Shop')
    partner_id = fields.Many2one('res.partner', string='Client')
    user_id = fields.Many2one('res.users', string='Salesperson')
    type = fields.Selection([('by_product','By Product'),
                             ('by_products','By Products'),
                             ('by_category','By Category')], string='Type', default='by_product', required=True)
    product_id= fields.Many2one('product.product',string='Product')
    product_categ_id = fields.Many2one('product.category', string='Category')
    product_ids = fields.One2many('invoices.analysis.wizard.lines','wizard_id', String='Products')

    date_from= fields.Date(string='Desde:', size=64)
    date_to= fields.Date(string='Hasta', size=64)


    @api.multi
    def view_report(self):
        report_domain = []
        for data in self:
            if data.type=='by_product':
                domain = [('product_id','=',data.product_id.id)]
                report_domain = expression.AND([domain] + [report_domain])
            elif data.type=='by_category':
                domain = [('categ_id','child_of',data.product_categ_id.id)]
                report_domain = expression.AND([domain] + [report_domain])
            elif data.type=='by_products':
                products = []
                for line in data.product_ids:
                    products.append(line.product_id.id)
                domain = [('product_id','in',products)]
                report_domain = expression.AND([domain] + [report_domain])

            if data.shop_id:
                domain = [('shop_id','=',data.shop_id.id)]
                report_domain = expression.AND([domain] + [report_domain])

            if data.partner_id:
                domain = [('partner_id', '=', data.partner_id.id)]
                report_domain = expression.AND([domain] + [report_domain])

            if data.user_id:
                domain = [('user_id', '=', data.user_id.id)]
                report_domain = expression.AND([domain] + [report_domain])

            if data.date_from:
                domain = [('date_invoice','>=',data.date_from)]
                report_domain = expression.AND([domain] + [report_domain])
            if data.date_to:
                domain = [('date_invoice','<=',data.date_to)]
                report_domain = expression.AND([domain] + [report_domain])

        self.env['m.report.view'].check_and_refresh_materialized_view("product_sale_invoice_list")
        self.env['m.report.view'].check_and_refresh_materialized_view("product_date_sold_returned_invoices")


        data_obj = self.pool.get('ir.model.data')
        model_data_id = self.env['ir.model.data']._get_id('poi_logistic_analysis_sale', 'view_product_date_sold_returned_invoices_graph')
        res_id = self.env['ir.model.data'].browse(model_data_id).res_id
        return {
            'name': _('Sale Invoices Analysis'),
            'domain': report_domain,
            'view_type': 'form',
            'view_mode': 'chart',
            'res_model': 'product.date.sold.returned.invoices',
            'view_id': res_id,
            'context': {},
            'type': 'ir.actions.act_window'
        }


class invoices_analysis_wizard_lines(models.TransientModel):
    """
    For Reporte kardex valorado
    """
    _name = "invoices.analysis.wizard.lines"
    _description = "Invoices analysis Wizard Lines"


    wizard_id = fields.Many2one('invoices.analysis.wizard', 'Wizard')
    product_id= fields.Many2one('product.product',string='Product')
