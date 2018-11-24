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


class ProductSaleInvoiceList(models.Model):
    _name = 'product.sale.invoice.list'
    _description = 'List Sale Invoices Report'
    _auto = False


    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    partner_id = fields.Many2one('res.partner', string='Client')
    user_id = fields.Many2one('res.users', string='Salesperson')
    shop_id = fields.Many2one('stock.warehouse', string='Shop')
    date_invoice = fields.Datetime('Date Order')
    product_id = fields.Many2one('product.product', string='Product')
    inv_qty_sold = fields.Float('Quantity Sold')
    amount_sold = fields.Float('Amount Sold')
    amount_discounted = fields.Float('Amount Discounted')
    price_unit = fields.Float('Average Price Unit')
    inv_qty_returned = fields.Float('Quantity Returned')
    amount_returned = fields.Float('Amount Returned')
    company_id = fields.Many2one('res.company', string='Company')

    def _select(self, select=False):
        if select:
            select_str= select
        else:
            select_str = """
  SELECT
		ail.invoice_id,
		ai.partner_id,
		ai.user_id,
		ai.warehouse_id as shop_id,
		ai.date_invoice,
		ail.product_id,
		sum(ail.quantity) as inv_qty_sold,
		sum((ail.price_unit*ail.quantity)*(1-(ail.discount/100))) as amount_sold,
		sum((ail.price_unit*ail.quantity)*(ail.discount/100)) as amount_discounted,
		avg(ail.price_unit) as price_unit,
		0.0 as inv_qty_returned,
		0.0 as amount_returned,
		ai.company_id
	FROM account_invoice_line ail
	LEFT JOIN account_invoice ai
	ON ail.invoice_id = ai.id
	WHERE ai.type='out_invoice'
	AND ai.state in ('open','paid')
	AND ail.product_id is not null
	GROUP BY ail.invoice_id, ai.date_invoice, ail.product_id, ai.company_id, ai.warehouse_id, ai.partner_id, ai.user_id

	UNION
	SELECT
		ail.invoice_id,
		ai.partner_id,
		ai.user_id,
		ai.warehouse_id as shop_id,
		ai.date_invoice,
		ail.product_id,
		0.0 as inv_qty_sold,
		0.0 as amount_sold,
		0.0 as amount_discounted,
		avg(ail.price_unit) as price_unit,
		sum(abs(ail.quantity)) as inv_qty_returned,
		sum(abs((ail.price_unit*ail.quantity)*(1-(ail.discount/100)))) as amount_returned,
		ai.company_id
	FROM account_invoice_line ail
	LEFT JOIN account_invoice ai
	ON ail.invoice_id = ai.id
	WHERE ai.type='out_refund'
	AND ai.state in ('open','paid')
	AND ail.product_id is not null
	GROUP BY ail.invoice_id, ai.date_invoice, ail.product_id, ai.company_id, ai.warehouse_id, ai.partner_id, ai.user_id
        """
        return select_str


    def init(self, cr, select=False, mlc=False, mlr=False):
        table = "product_sale_invoice_list"
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
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "product_sale_invoice_list")
        res = super(ProductSaleInvoiceList, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        return res