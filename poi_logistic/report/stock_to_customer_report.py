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


class PoiStockCustomerReport(models.Model):
    _name = 'poi.stock.customer.report'
    _description = 'Stock Customer Report'
    _auto = False

    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Location')
    company_id = fields.Many2one('res.company', string='Company')

    date = fields.Date('Date')
    date_day = fields.Integer('Day')
    date_month = fields.Integer('Month')
    date_year = fields.Integer('Year')

    product_qty = fields.Float(string='Product Quantity')

    def _select(self, select=False):
        if select:
            select_str= select
        else:
            select_str = """
SELECT
	company_id,
	date,
	extract(day from cast(date as timestamp)) as date_day,
	extract(month from cast(date as timestamp)) as date_month,
	extract(year from cast(date as timestamp)) as date_year,
	product_id,
	location_id,
	sum(product_uom_qty) as product_qty
FROM
(
SELECT
	sm.company_id,
	sm.product_id,
	sm.product_uom_qty,
	sm.location_id,
	cast(cast(sm.date as timestamp) + c_interval as date) as date --USING THE NEW c_interval
FROM stock_move sm
LEFT JOIN stock_location sl
	ON sl.id = sm.location_id
LEFT JOIN stock_location sld
	ON sld.id = sm.location_dest_id
LEFT JOIN
	(
		SELECT id, cast(substring(tz_offset from 1 for 3)||':'||substring(tz_offset from 4 for 2) as interval) as c_interval FROM res_company
	) as company_tz
	ON company_tz.id = sm.company_id
WHERE
	sm.state = 'done'
	AND (sl.usage='internal' AND sld.usage='customer')

UNION

SELECT
	sm.company_id,
	sm.product_id,
	-sm.product_uom_qty,
	sm.location_dest_id as location_id,
	cast(cast(sm.date as timestamp) + c_interval as date) as date --USING THE NEW c_interval
FROM stock_move sm
LEFT JOIN stock_location sl
	ON sl.id = sm.location_id
LEFT JOIN stock_location sld
	ON sld.id = sm.location_dest_id
LEFT JOIN
	(
		SELECT id, cast(substring(tz_offset from 1 for 3)||':'||substring(tz_offset from 4 for 2) as interval) as c_interval FROM res_company
	) as company_tz
	ON company_tz.id = sm.company_id
WHERE
	sm.state = 'done'
	AND (sld.usage='internal' AND sl.usage='customer')
) as movements
GROUP BY company_id, location_id, product_id, date
ORDER BY company_id, location_id, product_id, date
"""
        return select_str


    def init(self, cr, select=False, mlc=False, mlr=False):
        table = "poi_stock_customer_report"
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