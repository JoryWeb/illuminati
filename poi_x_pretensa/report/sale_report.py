# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import tools
from openerp.osv import fields, osv

class pret_sales_report(osv.osv):
    _name = "pret.sales.report"
    _description = "Reporte de ventas Pretensa"
    _auto = False
    #_rec_name = 'date'

    _columns = {
        'order_id': fields.many2one('sale.order', 'Pedido'),
        'partner_id': fields.many2one('res.partner', 'Cliente', readonly=True),
        'shop_id': fields.many2one('stock.warehouse', 'Sucursal', readonly=True),
        'date_order': fields.datetime('Fecha Pedido', readonly=True),
        'estado': fields.selection([('vpe','VENDIDO X ENTREGAR'),
                                    ('ve','VENDIDO ENTREGADO'),
                                    ('pendiente','PENDIENTE'),
                                    ('perdida','PERDIDA')], string="ESTADO"),
        'user_id': fields.many2one('res.users', 'Vendedor', readonly=True),
        'categoria': fields.char(u'Categoría'),
        'total_dimension': fields.float('Total', readonly=True),
        'precio_venta': fields.float('Precio de Venta', readonly=True),
        #'precio_lista': fields.float('Precio de Lista', readonly=True),
        #'diferencia': fields.float('Diferencia', readonly=True),
        # 'product_id': fields.many2one('product.product', 'Product', readonly=True),
        # 'product_uom': fields.many2one('product.uom', 'Unit of Measure', readonly=True),
        # 'product_uom_qty': fields.float('# of Qty', readonly=True),
        # 'qty_delivered': fields.float('Qty Delivered', readonly=True),
        # 'qty_to_invoice': fields.float('Qty To Invoice', readonly=True),
        # 'qty_invoiced': fields.float('Qty Invoiced', readonly=True),
        #
        # 'company_id': fields.many2one('res.company', 'Company', readonly=True),
        # 'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        #
        # 'price_subtotal': fields.float('Untaxed Total Price', readonly=True),
        # 'product_tmpl_id': fields.many2one('product.template', 'Product Template', readonly=True),
        # 'categ_id': fields.many2one('product.category','Product Category', readonly=True),
        # 'nbr': fields.integer('# of Lines', readonly=True),
        # 'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', readonly=True),
        # 'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', readonly=True),
        # 'team_id': fields.many2one('crm.team', 'Sales Team', readonly=True, oldname='section_id'),
        # 'country_id': fields.many2one('res.country', 'Partner Country', readonly=True),
        # 'commercial_partner_id': fields.many2one('res.partner', 'Commercial Entity', readonly=True),
        # 'state': fields.selection([
        #         ('draft', 'Draft Quotation'),
        #         ('sent', 'Quotation Sent'),
        #         ('sale', 'Sales Order'),
        #         ('done', 'Sales Done'),
        #         ('cancel', 'Cancelled'),
        #     ], string='Status', readonly=True),
    }
    _order = 'date_order desc'

    def _select(self):
        select_str = """
             select ROW_NUMBER() OVER(ORDER BY order_id) AS id, foo.* from (
              SELECT
                t0.order_id,
                t1.partner_id,
                t1.shop_id,
                t1.date_order,
                CASE WHEN t1.state IN ('draft', 'sale', 'confirmed', 'assigned')
                  THEN 'vpe'
                WHEN t1.state IN ('done')
                  THEN 've'
                WHEN t1.state IN ('cancel')
                  THEN 'perdida' END AS estado,
                t0.write_uid AS user_id,
                t4.name || '(' || t4.udm_rep_ventas || ')' AS categoria,
                sum(COALESCE(t0.total_dimension, 0)) AS total_dimension,
                sum(COALESCE(t0.product_uom_qty * t0.price_unit, 0)) AS precio_venta
              FROM sale_order_line t0
                INNER JOIN sale_order t1 ON t1.id = t0.order_id
                INNER JOIN product_product t2 ON t2.id = t0.product_id
                INNER JOIN product_template t3 ON t3.id = t2.product_tmpl_id
                INNER JOIN product_category t4 ON t4.id = t3.categ_id
              GROUP BY t0.order_id,
                t1.partner_id,
                t1.shop_id,
                t1.date_order,
                t1.state,
                t0.write_uid,
                t4.name,
                t4.udm_rep_ventas
              UNION ALL
              SELECT
                t0.order_id,
                t1.partner_id,
                t1.shop_id,
                t1.date_order,
                CASE WHEN t1.state IN ('draft', 'sale', 'confirmed', 'assigned')
                  THEN 'vpe'
                WHEN t1.state IN ('done')
                  THEN 've'
                WHEN t1.state IN ('cancel')
                  THEN 'perdida' END                AS estado,
                t0.write_uid                        AS user_id,
                'Z1 Precio de Venta'                   AS categoria,
                sum(COALESCE(t0.price_subtotal, 0)) AS total_dimension,
                0 AS precio_venta
              FROM sale_order_line t0
                INNER JOIN sale_order t1 ON t1.id = t0.order_id
                INNER JOIN product_product t2 ON t2.id = t0.product_id
                INNER JOIN product_template t3 ON t3.id = t2.product_tmpl_id
                INNER JOIN product_category t4 ON t4.id = t3.categ_id
              GROUP BY t0.order_id,
                t1.partner_id,
                t1.shop_id,
                t1.date_order,
                t1.state,
                t0.write_uid,
                t4.name
              UNION ALL
              SELECT
                t0.order_id,
                t1.partner_id,
                t1.shop_id,
                t1.date_order,
                CASE WHEN t1.state IN ('draft', 'sale', 'confirmed', 'assigned')
                  THEN 'vpe'
                WHEN t1.state IN ('done')
                  THEN 've'
                WHEN t1.state IN ('cancel')
                  THEN 'perdida' END                                 AS estado,
                t0.write_uid                                         AS user_id,
                'Z2 Precio Lista'                                       AS categoria,
                sum(COALESCE(t0.product_uom_qty * t0.price_unit, 0)) AS total_dimension,
                0 AS precio_venta
              FROM sale_order_line t0
                INNER JOIN sale_order t1 ON t1.id = t0.order_id
                INNER JOIN product_product t2 ON t2.id = t0.product_id
                INNER JOIN product_template t3 ON t3.id = t2.product_tmpl_id
                INNER JOIN product_category t4 ON t4.id = t3.categ_id
              GROUP BY t0.order_id,
                t1.partner_id,
                t1.shop_id,
                t1.date_order,
                t1.state,
                t0.write_uid,
                t4.name
              UNION ALL
              SELECT
                t0.order_id,
                t1.partner_id,
                t1.shop_id,
                t1.date_order,
                CASE WHEN t1.state IN ('draft', 'sale', 'confirmed', 'assigned')
                  THEN 'vpe'
                WHEN t1.state IN ('done')
                  THEN 've'
                WHEN t1.state IN ('cancel')
                  THEN 'perdida' END                                                         AS estado,
                t0.write_uid                                                                 AS user_id,
                'Z3 Diferencia'                                                                 AS categoria,
                sum(COALESCE((t0.price_subtotal - (t0.product_uom_qty * t0.price_unit)), 0)) AS total_dimension,
                0 AS precio_venta
              FROM sale_order_line t0
                INNER JOIN sale_order t1 ON t1.id = t0.order_id
                INNER JOIN product_product t2 ON t2.id = t0.product_id
                INNER JOIN product_template t3 ON t3.id = t2.product_tmpl_id
                INNER JOIN product_category t4 ON t4.id = t3.categ_id
              GROUP BY t0.order_id,
                t1.partner_id,
                t1.shop_id,
                t1.date_order,
                t1.state,
                t0.write_uid,
                t4.name
            ) as foo
        """
        return select_str

    def _from(self):
        from_str = """
        """
        return from_str

    def _group_by(self):
        group_by_str = """
        """
        return group_by_str

    def init(self, cr):
        # self._table = pret_sales_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
                    %s
                    )""" % (self._table, self._select()))
        # cr.execute("""CREATE or REPLACE VIEW %s as (
        #     %s
        #     FROM ( %s )
        #     %s
        #     )""" % (self._table, self._select(), self._from(), self._group_by()))
