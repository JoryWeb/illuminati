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




class PoiActualStockReport(models.Model):
    _name = 'poi.actual.stock.report'
    _description = 'Actual Stock Report'
    _auto = False

    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Location')
    qty = fields.Float(string='Quantity')
    reserved_qty = fields.Float(string='Reserved Quantity')
    categ_id = fields.Many2one('product.category', string='Product Category')

    def _select(self, select=False):
        if select:
            select_str= select
        else:
            select_str = """
        SELECT product_location.product_id, product_location.location_id, cast(coalesce(actual_stock.qty,'0.0') as float) as qty, cast(coalesce(reserved_stock.qty,'0.0') as float) as reserved_qty, pt.categ_id FROM
(
	SELECT pp.id as product_id, sl.id as location_id, pp.product_tmpl_id
	FROM product_product pp, stock_location sl
	WHERE usage='internal' and  pp.active
) as product_location
LEFT JOIN product_template as pt
ON product_location.product_tmpl_id = pt.id
LEFT JOIN
(
	SELECT product_id, location_id, sum(qty) as qty
		FROM stock_quant
		GROUP BY product_id, location_id
) as actual_stock
ON actual_stock.location_id=product_location.location_id and actual_stock.product_id = product_location.product_id
LEFT JOIN
(
	SELECT product_id, location_id, sum(qty) as qty
		FROM stock_quant
		WHERE reservation_id is not null
		GROUP BY product_id, location_id
) as reserved_stock
ON reserved_stock.location_id=product_location.location_id and reserved_stock.product_id = product_location.product_id
WHERE pt.type!='service'
ORDER BY product_id, location_id
        """
        return select_str


    def init(self, cr, select=False, mlc=False, mlr=False):
        table = "poi_actual_stock_report"
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


        cr.execute("SELECT indexname FROM pg_indexes WHERE indexname = %s and tablename = %s", ('poi_actual_stock_report_index', 'poi_actual_stock_report'))
        res2 = cr.dictfetchall()
        if not res2:
            cr.execute("""
            CREATE UNIQUE INDEX poi_actual_stock_report_index
              ON poi_actual_stock_report (product_id, location_id);
            """)
            cr.commit()

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        if ['id','<',0] in domain and len(domain)>1: domain.remove(['id','<',0])
        if ['id','<',0] in domain and len(domain)<=1:
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, uid, "poi_actual_stock_report")
            return True
        location_ids = self.pool.get('res.users').get_allowed_locations(cr, uid, context=context)
        def check_if_location_id(arg):
            for argument in arg:
                if isinstance(domain[0], (list, tuple)):
                    if argument[0] == 'location_id':
                        return True
            else:
                return False
        loc_domain = [('location_id','in',location_ids)]
        if loc_domain and not check_if_location_id(domain):
            domain = expression.AND([domain] + [loc_domain])
            #fields = ['product_id','location_id','qty']
            #groupby= ['product_id','location_id']
        res = super(PoiActualStockReport, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby, lazy=lazy)
        return res


    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if ['id','<',0] in args and len(args)>1: args.remove(['id','<',0])
        res=super(PoiActualStockReport, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
        return res


    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: context = {}
        #Nos aseguramos que se actualice si o si al entrar, aunque alguno le mande algun valor por defecto al dominio
        if view_type=="tree":
            self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, user, "poi_actual_stock_report")
        res = super(PoiActualStockReport, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        return res

    @api.cr_uid_context
    def get_actual_stock(self, cr, uid, product_ids=[], location_id=None, context=None):
        if not product_ids:
            product_ids = []

        prods = ",".join(str(x) for x in product_ids)

        self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, uid, "poi_actual_stock_report")
        query = """
        SELECT product_id, qty - reserved_qty as available_qty
        FROM poi_actual_stock_report
        WHERE product_id in ("""+prods+""")
        AND location_id = """+str(location_id)+"""
        """

        cr.execute(query)
        res = cr.dictfetchall()
        res_dict = {x.get('product_id'):x.get('available_qty') for x in res}
        return res_dict


    @api.cr_uid_context
    def read_actual_stock(self, cr, uid, product_ids=[], location_id=None, context=None):
        if not product_ids:
            product_ids = []

        self.pool.get('m.report.view').check_and_refresh_materialized_view(cr, uid, "poi_actual_stock_report")

        mod_obj = self.pool.get('ir.model.data')

        res = mod_obj.get_object_reference(cr, uid, 'poi_essential_reports', 'view_poi_actual_stock_report_tree')
        res_id = res and res[1] or False,

        return {
            'name': _('Actual Stock Report'),
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': [res_id],
            'res_model': 'poi.actual.stock.report',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': [('product_id','in',product_ids)],
            'context': {'group_by':['product_id','location_id'], 'group_by_no_leaf':1}
        }