from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

class SaleOrderBookingNeu(models.Model):
    _name = 'sale.order.booking.neu'
    _description = 'Analisis de Reserva de Neumaticos'
    _auto = False

    order_id = fields.Many2one('sale.order', 'Cotizacion')
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen')
    user_id = fields.Many2one('res.users', 'Vendedor')
    product_id = fields.Many2one('product.product', 'Producto')
    product_uom_qty = fields.Float('Cantidad')
    order_date = fields.Date('Fecha')
    picking_id = fields.Many2one('stock.picking', 'Albaran')
    state = fields.Char('Estado')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):

        self.env.cr.execute("REFRESH MATERIALIZED VIEW sale_order_booking_neu");

        res = super(SaleOrderBookingNeu, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        return res


    def _select(self):

        select_str ="""
            select
            	so.id as order_id,
            	so.warehouse_id,
            	so.user_id,
            	sol.product_id,
            	sol.product_uom_qty,
            	so.order_date,
            	sp.id as picking_id,
            	sp.state
            from
            	sale_order so
            	left join sale_order_line sol on sol.order_id = so.id
            	left join product_product pp on pp.id = sol.product_id
            	left join product_template pt on pt.id = pp.product_tmpl_id
            	left join product_category pc on pc.id = pt.categ_id
            	left join stock_picking sp on sp.group_id = so.procurement_group_id
            where
            	pc.type_product = 'neu'
        """
        return select_str

    @api.model_cr
    def init(self):
        table = "sale_order_booking_neu"
        self.env.cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = 'sale_order_booking_neu';
            """)
        vista = self.env.cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                self.env.cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS sale_order_booking_neu;
            CREATE MATERIALIZED VIEW sale_order_booking_neu as (
            SELECT row_number() over() as id, *
                FROM(%s) as asd
            )""" % (self._select()))
