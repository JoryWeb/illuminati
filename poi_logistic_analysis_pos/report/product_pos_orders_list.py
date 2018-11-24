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


class ProductPosOrdersList(models.Model):
    _name = 'product.pos.orders.list'
    _description = 'List Pos Orders Report'
    _auto = False


    pos_order_id = fields.Many2one('pos.order', string='POS Order')
    shop_id = fields.Many2one('stock.warehouse', string='Shop')
    date_order = fields.Datetime('Date Order')
    product_id = fields.Many2one('product.product', string='Product')
    pos_qty_sold = fields.Float('Quantity Sold')
    amount_sold = fields.Float('Amount Sold')
    amount_discounted = fields.Float('Amount Discounted')
    price_unit = fields.Float('Average Price Unit')
    pos_qty_returned = fields.Float('POS Qty Returned')
    amount_returned = fields.Float('Amount Returned')
    company_id = fields.Many2one('res.company', string='Company')

    def _select(self, select=False):
        if select:
            select_str= select
        else:
            select_str = """
        SELECT
	po.id as pos_order_id,
	po.warehouse_id as shop_id,
	po.date_order,
	pol.product_id,
	sum(pol.qty) as pos_qty_sold,
	sum((pol.price_unit*pol.qty)*(1-(pol.discount/100))) as amount_sold,
	sum((pol.price_unit*pol.qty)*(pol.discount/100)) as amount_discounted,
	avg(pol.price_unit) as price_unit,
	0.0 as pos_qty_returned,
	0.0 as amount_returned,
	po.company_id
FROM pos_order_line pol
LEFT JOIN pos_order po
ON pol.order_id = po.id
WHERE po.state not in ('draft','cancel')
AND pol.qty > 0
GROUP BY po.id, po.date_order, pol.product_id, po.company_id, po.warehouse_id

UNION

SELECT
	po.id as pos_order_id,
	po.warehouse_id as shop_id,
	po.date_order,
	pol.product_id,
	0.0 as pos_qty_sold,
	0.0 as amount_sold,
	0.0 as amount_discounted,
	avg(pol.price_unit) as price_unit,
	sum(abs(pol.qty)) as pos_qty_returned,
	sum(abs((pol.price_unit*pol.qty)*(1-(pol.discount/100)))) as amount_returned,
	po.company_id
FROM pos_order_line pol
LEFT JOIN pos_order po
ON pol.order_id = po.id
WHERE po.state not in ('draft','cancel')
AND pol.qty < 0
GROUP BY po.id, po.date_order, pol.product_id, po.company_id, po.warehouse_id
        """
        return select_str


    def init(self, cr, select=False, mlc=False, mlr=False):
        table = "product_pos_orders_list"
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
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "product_pos_orders_list")
        res = super(ProductPosOrdersList, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        return res