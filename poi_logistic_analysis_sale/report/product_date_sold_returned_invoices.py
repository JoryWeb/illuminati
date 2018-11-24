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


class ProductDateSoldReturnedInvoices(models.Model):
    _name = 'product.date.sold.returned.invoices'
    _description = 'Sale Invoice Report'
    _auto = False

    shop_id = fields.Many2one('stock.warehouse','Shop')
    partner_id = fields.Many2one('res.partner', string='Client')
    user_id = fields.Many2one('res.users', string='Salesperson')
    date_invoice = fields.Date('Date Order')
    date_invoice_day = fields.Integer('Day')
    date_invoice_month = fields.Integer('Month')
    date_invoice_year = fields.Integer('Year')
    product_id = fields.Many2one('product.product', string='Product')
    categ_id = fields.Many2one('product.category', string='Product Category')
    inv_qty_sold = fields.Float('Quantity Sold')
    amount_sold = fields.Float('Amount Sold')
    amount_discounted = fields.Float('Amount Discounted')
    price_unit = fields.Float('Average Price Unit', group_operator="avg")
    inv_qty_returned = fields.Float('Quantity Returned')
    amount_returned = fields.Float('Amount Returned')
    num_invoices_sold = fields.Integer('Num Orders Sold')
    num_invoices_returned = fields.Integer('Num Orders Returned')

    def _select(self, select=False):
        if select:
            select_str= select
        else:
            select_str = """
SELECT
		shop_id,
		partner_id,
		user_id,
		date_invoice,
		extract(day from cast(date_invoice as timestamp)) as date_invoice_day,
		extract(month from cast(date_invoice as timestamp)) as date_invoice_month,
		extract(year from cast(date_invoice as timestamp)) as date_invoice_year,
		product_id,
		categ_id,
		sum(inv_qty_sold) as inv_qty_sold,
		sum(amount_sold) as amount_sold,
		sum(amount_discounted) as amount_discounted,
		avg(price_unit) as price_unit,
		sum(inv_qty_returned) as inv_qty_returned,
		sum(amount_returned) as amount_returned,
		sum(num_invoices_sold) as num_invoices_sold,
		sum(num_invoices_returned) as num_invoices_returned
	FROM
	(
		SELECT
			date_invoice,
			partner_id,
			user_id,
			shop_id,
			product_id,
			sum(inv_qty_sold) as inv_qty_sold,
			sum(amount_sold) as amount_sold,
			sum(amount_discounted) as amount_discounted,
			avg(price_unit) as price_unit,
			sum(inv_qty_returned) as inv_qty_returned,
			sum(amount_returned) as amount_returned,
			count(invoice_id) as num_invoices_sold,
			0.0 as num_invoices_returned
		FROM product_sale_invoice_list
		WHERE inv_qty_sold > 0 AND inv_qty_returned = 0
		GROUP BY date_invoice, product_id, shop_id, partner_id, user_id

		UNION

		SELECT
			date_invoice,
			partner_id,
			user_id,
			shop_id,
			product_id,
			sum(inv_qty_sold) as inv_qty_sold,
			sum(amount_sold) as amount_sold,
			sum(amount_discounted) as amount_discounted,
			avg(price_unit) as price_unit,
			sum(inv_qty_returned) as inv_qty_returned,
			sum(amount_returned) as amount_returned,
			0.0 as num_invoices_sold,
			count(invoice_id) as num_invoices_returned
		FROM product_sale_invoice_list
		WHERE inv_qty_sold = 0 AND inv_qty_returned > 0
		GROUP BY date_invoice, product_id, shop_id, partner_id, user_id
	) as total_sale_invoices
	LEFT JOIN product_product pp
	ON pp.id = product_id
	LEFT JOIN product_template pt
	ON pt.id = pp.product_tmpl_id
	GROUP BY date_invoice, product_id, categ_id, shop_id, partner_id, user_id
	ORDER BY date_invoice, product_id
        """
        return select_str


    def init(self, cr, select=False, mlc=False, mlr=False):
        table = "product_date_sold_returned_invoices"
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

            DROP MATERIALIZED VIEW IF EXISTS %s;
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
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "product_sale_invoice_list")
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "product_date_sold_returned_invoices")
        res = super(ProductDateSoldReturnedInvoices, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        return res
