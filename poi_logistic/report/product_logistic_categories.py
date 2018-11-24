##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

#
# Please note that these reports are not multi-currency !!!
#

from openerp.osv import expression
from openerp import tools

from openerp import models, fields, api, _, tools
from lxml import etree


class PoiProductLogisticCategoriesReport(models.Model):
    _name = 'poi.product.logistic.categories.report'
    _description = 'Product Logistic Categories Report'
    _auto = False

    product_id = fields.Many2one('product.product', string='Product')
    company_id = fields.Many2one('res.company', string='Company')
    product_period_move = fields.Integer(string='Period Category', help='This field is going to categorize based on company logistic range')

    def _select(self, select=False):
        if select:
            select_str= select
        else:
            select_str = """
SELECT product_id, company_id, count(date_grouped) as product_period_move
FROM
(
SELECT product_id, company_id, date_grouped
FROM
(
SELECT
	product_id,
	company_id,
	CASE analysis_range
	WHEN 'daily' THEN cast(date_day||'00'||date_month as integer)
	WHEN 'monthly' THEN date_month
	WHEN 'by_week' THEN extract(week from date)
	END as date_grouped
FROM poi_stock_customer_report
LEFT JOIN res_company rc
ON rc.id = poi_stock_customer_report.company_id
ORDER BY date
) as pickings
GROUP BY product_id, company_id, date_grouped
ORDER BY product_id, company_id, date_grouped
) as group_pickings
GROUP BY product_id, company_id
"""
        return select_str


    def init(self, cr, select=False, mlc=False, mlr=False):
        table = "poi_product_logistic_categories_report"
        cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = '%s';
            """ % table)
        vista = cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        cr.execute("""

            DROP MATERIALIZED VIEW IF EXISTS %s CASCADE;
            CREATE MATERIALIZED VIEW %s as ((
            SELECT row_number() over() as id, *
                FROM ((
                    %s
                )) as asd
            ))""" % (table, table, self._select(select)))


    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: context = {}
        #Nos aseguramos que se actualice si o si al entrar, aunque alguno le mande algun valor por defecto al dominio
        if view_type=="tree":
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "poi_stock_customer_report")
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "poi_product_logistic_categories_report")
        if view_type=="chart":
            view_type="graph"
        res = super(PoiProductLogisticCategoriesReport, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        return res
