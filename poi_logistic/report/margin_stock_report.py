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


class PoiMarginStockReport(models.Model):
    _name = 'poi.margin.stock.report'
    _description = 'Margin Stock Report'
    _auto = False

    name = fields.Char(string='Name')
    categ_id = fields.Many2one('product.category', string='Category')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('product.uom', string='Product UoM')
    location_id = fields.Many2one('stock.location', string='Location')
    company_id = fields.Many2one('res.company', string='Company')
    min_qty = fields.Float(string='Min. Quantity')
    sec_qty = fields.Float(string='Sec. Quantity')
    max_qty = fields.Float(string='Max. Quantity')
    type = fields.Selection([('location','Location'),
                             ('company','Company')], string='Control Type')

    qty = fields.Float(string='Actual Location Qty.')
    reserved_qty = fields.Float(string='Location Reserved Qty.')

    c_qty = fields.Float(string='Actual Company Qty')
    cr_qty = fields.Float(string='Actual Company Reserved Qty')

    breaking_point = fields.Float(string='Breaking Point')

    state = fields.Selection([('out_of_stock', 'Out of Stock'),
                              ('below_minimal','Below Minimal'),
                              ('below_security_percentage','Below Security Percentage'),
                              ('on_rule', 'On Rule'),
                              ('over_maximum', 'Over Maximum')], string='State')


    def _select(self, select=False):
        if select:
            select_str= select
        else:
            select_str = """
SELECT
	name,
	categ_id,
	product_id,
	product_uom,
	CASE WHEN type='location' THEN location_id ELSE null END as location_id,
	CASE WHEN type='company' THEN company_id ELSE null END as company_id,
	min_qty,
	(min_qty * (1+(security_percentage/100))) as sec_qty,
	max_qty,
	type,
	CASE WHEN type='location' THEN qty ELSE 0.0 END as qty,
	CASE WHEN type='location' THEN reserved_qty ELSE 0.0 END as reserved_qty,
	c_qty,
	cr_qty,
	CASE WHEN min_qty != 0.0
	THEN
		CASE WHEN type='location' THEN (coalesce(qty, 0.0) - coalesce(reserved_qty, 0.0)) / min_qty ELSE (coalesce(c_qty, 0.0) - coalesce(cr_qty, 0.0)) / min_qty END
	ELSE
		0.0
	END as breaking_point,
	CASE
	--LOCATION
	WHEN type='location' AND (qty-reserved_qty) <= 0.0 THEN 'out_of_stock'
	WHEN type='location' AND (qty-reserved_qty) > 0.0 AND (qty-reserved_qty) < min_qty THEN 'below_minimal'
	WHEN type='location' AND (qty-reserved_qty) >= min_qty AND (qty-reserved_qty) < (min_qty * (1+(security_percentage/100))) THEN 'below_security_percentage'
	WHEN type='location' AND (qty-reserved_qty) >= (min_qty * (1+(security_percentage/100))) AND (qty-reserved_qty) <= max_qty THEN 'on_rule'
	WHEN type='location' AND (qty-reserved_qty) > max_qty THEN 'over_maximum'
	--COMPANY
	WHEN type='company' AND (c_qty-cr_qty) <= 0.0 THEN 'out_of_stock'
	WHEN type='company' AND (c_qty-cr_qty) > 0.0 AND (c_qty-cr_qty) < min_qty THEN 'below_minimal'
	WHEN type='company' AND (c_qty-cr_qty) >= min_qty AND (c_qty-cr_qty) < (min_qty * (1+(security_percentage/100))) THEN 'below_security_percentage'
	WHEN type='company' AND (c_qty-cr_qty) >= (min_qty * (1+(security_percentage/100))) AND (c_qty-cr_qty) <= max_qty THEN 'on_rule'
	WHEN type='company' AND (c_qty-cr_qty) > max_qty THEN 'over_maximum'
	END as state
FROM (
SELECT
	psc.name,
	pt.categ_id,
	psc.product_id,
	psc.product_uom,
	psc.location_id,
	psc.company_id,
	CASE WHEN psc.margin_calculation = 'manual' THEN psc.min_qty
	ELSE
		CASE WHEN psc.automatic_minimum_calculation = 'based_on_last_months' AND psc.type = 'location' THEN get_logistic_min_qty_location_month(psc.location_id, psc.automatic_period, psc.product_id)
		WHEN psc.automatic_minimum_calculation = 'based_on_last_days' AND psc.type = 'location' THEN get_logistic_min_qty_location_day(psc.location_id, psc.automatic_period, psc.product_id)
		WHEN psc.automatic_minimum_calculation = 'based_on_last_months' AND psc.type = 'company' THEN get_logistic_min_qty_company_month(psc.company_id, psc.automatic_period, psc.product_id)
		WHEN psc.automatic_minimum_calculation = 'based_on_last_days' AND psc.type = 'company' THEN get_logistic_min_qty_company_day(psc.company_id, psc.automatic_period, psc.product_id)
		WHEN psc.automatic_minimum_calculation = 'based_on_month' THEN 0.0
		END
	END as min_qty,
	psc.security_percentage,
	psc.max_qty,
	psc.type,
	stock.qty,
	stock.reserved_qty,
	c_stock.c_qty,
	c_stock.cr_qty
FROM product_stock_control psc
LEFT JOIN poi_actual_stock_report stock
	ON stock.product_id = psc.product_id AND stock.location_id = psc.location_id
LEFT JOIN
(
SELECT product_id, company_id, sum(qty) as c_qty, sum(reserved_qty) as cr_qty
FROM poi_actual_stock_report pasr
LEFT JOIN stock_location sl
ON sl.id = pasr.location_id
GROUP BY sl.company_id, product_id
) as c_stock
	ON c_stock.product_id = psc.product_id AND c_stock.company_id = psc.company_id
LEFT JOIN product_product pp
ON pp.id = psc.product_id
LEFT JOIN product_template pt
ON pp.product_tmpl_id = pt.id) as rep
"""
        return select_str


    def init(self, cr, select=False, mlc=False, mlr=False):
        table = "poi_margin_stock_report"
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
CREATE OR REPLACE FUNCTION get_logistic_min_qty_location_month(plocation_id int, report_interval int, pproduct_id int) RETURNS numeric AS $$
    DECLARE
	min_qty numeric;
        BEGIN
		SELECT coalesce(avg(product_qty), 0.0) as min_qty into min_qty
		FROM
		(
		SELECT product_id, sum(product_qty) as product_qty, date_month, date_year
		FROM poi_stock_customer_report r
		LEFT JOIN
			(
				SELECT id, cast(substring(tz_offset from 1 for 3)||':'||substring(tz_offset from 4 for 2) as interval) as c_interval FROM res_company
			) as company_tz
			ON company_tz.id = r.company_id
		WHERE date < cast(date_trunc('month', cast(cast(now() as timestamp) + c_interval as date)) as date)
			AND date >= cast(date_trunc('month', cast(cast(now() as timestamp) + c_interval as date)) as date) - cast(cast(report_interval as integer)||' months' as interval)
			AND product_id = pproduct_id
			AND location_id = plocation_id
		GROUP BY product_id, date_month, date_year) as r;
	RETURN min_qty;
	END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_logistic_min_qty_company_month(pcompany_id int, report_interval int, pproduct_id int) RETURNS numeric AS $$
    DECLARE
	min_qty numeric;
        BEGIN
		SELECT coalesce(avg(product_qty), 0.0) as min_qty into min_qty
		FROM
		(
		SELECT product_id, sum(product_qty) as product_qty, date_month, date_year
		FROM poi_stock_customer_report r
		LEFT JOIN
			(
				SELECT id, cast(substring(tz_offset from 1 for 3)||':'||substring(tz_offset from 4 for 2) as interval) as c_interval FROM res_company
			) as company_tz
			ON company_tz.id = r.company_id
		WHERE date < cast(date_trunc('month', cast(cast(now() as timestamp) + c_interval as date)) as date)
			AND date >= cast(date_trunc('month', cast(cast(now() as timestamp) + c_interval as date)) as date) - cast(cast(report_interval as integer)||' months' as interval)
			AND product_id = pproduct_id
			AND company_id = pcompany_id
		GROUP BY product_id, date_month, date_year) as r;
	RETURN min_qty;
	END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_logistic_min_qty_location_day(plocation_id int, report_interval int, pproduct_id int) RETURNS numeric AS $$
    DECLARE
	min_qty numeric;
        BEGIN
		SELECT coalesce(avg(product_qty), 0.0) as min_qty into min_qty
		FROM
		(
		SELECT product_id, sum(product_qty) as product_qty, date_month, date_year
		FROM poi_stock_customer_report r
		LEFT JOIN
			(
				SELECT id, cast(substring(tz_offset from 1 for 3)||':'||substring(tz_offset from 4 for 2) as interval) as c_interval FROM res_company
			) as company_tz
			ON company_tz.id = r.company_id
		WHERE date < cast(date_trunc('month', cast(cast(now() as timestamp) + c_interval as date)) as date)
			AND date >= cast(date_trunc('month', cast(cast(now() as timestamp) + c_interval as date)) as date) - cast(cast(report_interval as integer)||' days' as interval)
			AND product_id = pproduct_id
			AND location_id = plocation_id
		GROUP BY product_id, date_month, date_year) as r;
	RETURN min_qty;
	END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_logistic_min_qty_company_day(pcompany_id int, report_interval int, pproduct_id int) RETURNS numeric AS $$
    DECLARE
	min_qty numeric;
        BEGIN
		SELECT coalesce(avg(product_qty), 0.0) as min_qty into min_qty
		FROM
		(
		SELECT product_id, sum(product_qty) as product_qty, date_month, date_year
		FROM poi_stock_customer_report r
		LEFT JOIN
			(
				SELECT id, cast(substring(tz_offset from 1 for 3)||':'||substring(tz_offset from 4 for 2) as interval) as c_interval FROM res_company
			) as company_tz
			ON company_tz.id = r.company_id
		WHERE date < cast(date_trunc('month', cast(cast(now() as timestamp) + c_interval as date)) as date)
			AND date >= cast(date_trunc('month', cast(cast(now() as timestamp) + c_interval as date)) as date) - cast(cast(report_interval as integer)||' days' as interval)
			AND product_id = pproduct_id
			AND company_id = pcompany_id
		GROUP BY product_id, date_month, date_year) as r;
	RETURN min_qty;
	END;
$$ LANGUAGE plpgsql;
        """)


        cr.execute("""

            DROP MATERIALIZED VIEW IF EXISTS %s CASCADE;
            CREATE MATERIALIZED VIEW %s as ((
            SELECT row_number() over() as id, *
                FROM ((
                    %s
                )) as asd
            ))""" % (table, table, self._select(select)))


    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, uid, "poi_actual_stock_report")
        self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "poi_stock_customer_report")
        self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, uid, "poi_margin_stock_report")
        res = super(PoiMarginStockReport, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby, lazy=lazy)
        return res


    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: context = {}
        #Nos aseguramos que se actualice si o si al entrar, aunque alguno le mande algun valor por defecto al dominio
        if view_type=="tree":
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "poi_stock_customer_report")
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "poi_actual_stock_report")
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "poi_margin_stock_report")
        res = super(PoiMarginStockReport, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        return res


    @api.cr_uid_context
    def read_actual_stock(self, cr, uid, product_ids=[], location_id=None, context=None):
        if not product_ids:
            product_ids = []

        self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, uid, "poi_actual_stock_report")
        self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, uid, "poi_margin_stock_report")

        mod_obj = self.pool.get('ir.model.data')

        res = mod_obj.get_object_reference(cr, uid, 'poi_logistic', 'view_poi_margin_stock_report_tree')
        res_id = res and res[1] or False,

        return {
            'name': _('Margin Stock Report'),
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': [res_id],
            'res_model': 'poi.margin.stock.report',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': [('product_id','in',product_ids)],
        }