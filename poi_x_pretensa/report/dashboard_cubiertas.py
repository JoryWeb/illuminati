from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import tools
import unicodedata

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')


class pret_cubiertas_report(osv.osv):
    """docstring for pret_cubiertas_report"""
    _name = "pret.cubiertas.report"
    _description = 'informe facturas e ingresos (cubiertas)'
    _auto = False

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Obra/Cliente', readonly=True),
        'order_id': fields.many2one('sale.order', 'Orden de Venta', readonly=True),
        #'date': fields.date('Fecha de Entrega(OUT)'),
        'picking_id': fields.many2one('stock.picking', 'Guia', readonly=True),
        'amount_total': fields.float('Monto total', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_metric': fields.float('Total M.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_metric_m2': fields.float('Total M2.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_metric_m3': fields.float('Total M3.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'shop_id':fields.many2one('stock.warehouse', 'Sucursal', readonly=True),
        #'estado': fields.selection([('vpe','VENDIDO X ENTREGAR'),('ve','VENDIDO ENTREGADO'),('pendiente','PENDIENTE'),('perdida','PERDIDA')], string="ESTADO", readonly=True),
        'day': fields.char(u'Día', size=10, readonly=True),
        'week': fields.char(u'Semana', size=8, readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
        'date': fields.date('Fecha', readonly=True),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='search', context=None, toolbar=False, submenu=False):
        if view_type == 'search' and 'params' in context:
            cr.execute("REFRESH MATERIALIZED VIEW pret_cubiertas_report;")
        res = super(pret_cubiertas_report, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
        return res

    def init(self, cr):
        #tools.sql.drop_view_if_exists(cr, 'pret_cubiertas_report')
        sql = """DROP MATERIALIZED VIEW IF EXISTS pret_cubiertas_report;
                    CREATE MATERIALIZED VIEW pret_cubiertas_report as (
          SELECT
  row_number()
  OVER ()                                                       AS id,
  sales.invoice_id,
  sales.partner_id,
  sales.order_id,
  sales.picking_id,
  sales.amount_total,
  sales.total_metric,
  sales.total_metric_m2,
  sales.total_metric_m3,
  sales.date,
  sales.estado,
  sales.shop_id,
  dim.idd,
  dim.ptype_col_49,
  dim.ptype_col_50,
  dim.ptype_col_51,
  (date_part('year' :: TEXT, sales.date) :: CHARACTER(4) :: TEXT || '/' :: TEXT) ||
  date_part('week' :: TEXT, sales.date) :: CHARACTER(3) :: TEXT AS week,
  to_char(sales.date, 'DD/MM/YYYY' :: TEXT)                     AS day,
  to_char(sales.date, 'YYYY' :: TEXT)                           AS year,
  to_char(sales.date, 'MM' :: TEXT)                             AS month
FROM (SELECT
        max(ai.id)                                                           AS invoice_id,
        max(ai.partner_id)                                                   AS partner_id,
        max(so.id)                                                           AS order_id,
        max(sp.id)                                                           AS picking_id,
        max(ai.amount_total)                                                 AS amount_total,
        to_number(max(so.total_metric :: TEXT), '999999999999.999' :: TEXT)  AS total_metric,
        to_number(max(so.total_metric_m2 :: TEXT), '9999999999.999' :: TEXT) AS total_metric_m2,
        to_number(max(so.total_metric_m3 :: TEXT), '999999999.999' :: TEXT)  AS total_metric_m3,
        max(sp.date_done)                                                    AS date,
        max(ai.state :: TEXT)                                                AS estado,
        max(ai.shop_id)                                                      AS shop_id
      FROM account_invoice ai
        LEFT JOIN (select t1.order_id, t2.invoice_id from sale_order_line_invoice_rel t0
inner join sale_order_line t1 on t1.id = t0.order_line_id
inner join account_invoice_line t2 on t2.id = t0.invoice_line_id
group by t1.order_id, t2.invoice_id
order by t1.order_id) as soir ON soir.invoice_id = ai.id
        LEFT JOIN sale_order so ON so.id = soir.order_id
        INNER JOIN (SELECT
                      t3.order_id,
                      s1.picking_id
                    FROM sale_order_line t3
                      INNER JOIN procurement_order s0 ON s0.sale_line_id = t3.id
                      INNER JOIN stock_move s1 ON s1.procurement_id = s0.id
                    GROUP BY t3.order_id, s1.picking_id
                    ORDER BY t3.order_id) ddd ON ddd.order_id = so.id
        LEFT JOIN stock_picking sp ON sp.id = ddd.picking_id
      WHERE sp.state :: TEXT = 'done' :: TEXT
      GROUP BY ddd.order_id) sales
  JOIN (SELECT
          di.idd,
          sum(di.ptype_col_49) AS ptype_col_49,
          sum(di.ptype_col_50) AS ptype_col_50,
          sum(di.ptype_col_51) AS ptype_col_51
        FROM (SELECT
                so.id AS idd,
                pt.categ_id,
                CASE
                WHEN pt.categ_id = 49
                  THEN sum(sol.total_dimension)
                ELSE 0.0
                END   AS ptype_col_49,
                CASE
                WHEN pt.categ_id = 50
                  THEN sum(sol.total_dimension)
                ELSE 0.0
                END   AS ptype_col_50,
                CASE
                WHEN pt.categ_id = 51
                  THEN sum(sol.total_dimension)
                ELSE 0.0
                END   AS ptype_col_51
              FROM sale_order_line sol
                JOIN sale_order so ON sol.order_id = so.id
                JOIN product_product pp ON sol.product_id = pp.id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
              WHERE pt.categ_id = ANY (ARRAY [49, 50, 51])
              GROUP BY so.id, pt.categ_id
              ORDER BY so.id) di
        GROUP BY di.idd) dim ON dim.idd = sales.order_id
        )"""
        cr.execute(sql)

    def so_form(self, cr, uid, ids, context=None):

        line = self.browse(cr, uid, ids[0], context=context)
        line_id=self.pool.get('sale.order').search(cr,uid,[('id','=',line.order_id.id)])
        line_id=line_id[0]
        action_form = {
            'name': "Pedido de Venta",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sale.order',
            'res_id': line_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': context,
        }
        return action_form

pret_cubiertas_report()


class pret_cubiertas_report2(osv.osv):
    """docstring for pret_cubiertas_report"""
    _name = "pret.cubiertas.report2"
    _description = 'Informe Material Entregado con Guias'
    _auto = False

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Cliente', readonly=True),
        'order_id': fields.many2one('sale.order', 'Orden de Venta', readonly=True),
        'picking_id': fields.many2one('stock.picking', 'Guia', readonly=True),
        'direccion': fields.char('Direccion de Entrega', readonly=True),
        'city': fields.char('Ciudad de Entrega', readonly=True),
        'user_id': fields.many2one('res.users', 'Vendedor', readonly=True),
        'date_done': fields.date('Fecha de entrega', readonly=True),
        'total_metric': fields.float('Total M.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_metric_m2': fields.float('Total M2.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_metric_m3': fields.float('Total M3.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_weight': fields.float('Total Quintales', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'date_day': fields.char(u'Día', size=10, readonly=True),
        'date_month': fields.char(u'Mes', size=18, readonly=True),
        'date_week': fields.char(u'Semana', size=8, readonly=True),
        'date2': fields.date('Fecha', readonly=True),
    }
    def fields_view_get(self, cr, uid, view_id=None, view_type='search', context=None, toolbar=False, submenu=False):
        if view_type == 'search' and 'params' in context:
            cr.execute("REFRESH MATERIALIZED VIEW pret_cubiertas_report2;")
        res = super(pret_cubiertas_report2, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
        return res
    def init(self, cr):
        #tools.sql.drop_view_if_exists(cr, 'pret_cubiertas_report2')

        sql = """DROP MATERIALIZED VIEW IF EXISTS pret_cubiertas_report2;
                    CREATE MATERIALIZED VIEW pret_cubiertas_report2 as (
            SELECT row_number() OVER () AS id,
            sales.partner_id,
            sales.order_id,
            sales.picking_id,
            sales.direccion,
            sales.city,
            sales.user_id,
            sales.date_done,
            sales.total_metric,
            sales.total_metric_m2,
            sales.total_metric_m3,
            sales.total_weight,
            sales.note,
            sales.date,
            dim.idd,
            dim.ptype_col_49,
            dim.ptype_col_50,
            dim.ptype_col_51,
            ((date_part('year'::text, sales.date)::character(4)::text || '-'::text) ||
                CASE
                    WHEN date_part('month'::text, sales.date) < 10::double precision THEN '0'::text
                    ELSE ''::text
                END) || date_part('month'::text, sales.date)::character varying::text AS date_month,
            (date_part('year'::text, sales.date)::character(4)::text || '/'::text) || date_part('week'::text, sales.date)::character(3)::text AS date_week,
            to_char(sales.date, 'DD/MM/YYYY'::text) AS date_day,
            to_date(to_char(sales.date, 'YYYY/MM/DD'::text), 'YYYY/MM/DD'::text) AS date2
           FROM ( SELECT max(so.partner_id) AS partner_id,
                    max(so.id) AS order_id,
                    max(sp.id) AS picking_id,
                    max(lower(rp.street::text)) AS direccion,
                    max(lower(rp.city::text)) AS city,
                    max(so.user_id) AS user_id,
                    max(sp.date_done) AS date_done,
                    to_number(max(so.total_metric::text), '999999999999.999'::text) AS total_metric,
                    to_number(max(so.total_metric_m2::text), '9999999999.999'::text) AS total_metric_m2,
                    to_number(max(so.total_metric_m3::text), '999999999.999'::text) AS total_metric_m3,
                    max(so.total_weight) AS total_weight,
                    max(so.note) AS note,
                    max(sp.date_done) AS date
                   FROM sale_order so
                     INNER JOIN (SELECT t3.order_id, s1.picking_id
                                            FROM sale_order_line t3
                                              INNER JOIN procurement_order s0 ON s0.sale_line_id = t3.id
                                              INNER JOIN stock_move s1 ON s1.procurement_id = s0.id
                                             group by t3.order_id, s1.picking_id
                                             order by t3.order_id) ddd on ddd.order_id = so.id
                                 LEFT JOIN stock_picking sp ON sp.id = ddd.picking_id
                     JOIN res_partner rp ON rp.id = sp.partner_id
                  WHERE sp.state::text = 'done'::text
                  GROUP BY ddd.order_id) sales
             JOIN ( SELECT di.idd,
                    sum(di.ptype_col_49) AS ptype_col_49,
                    sum(di.ptype_col_50) AS ptype_col_50,
                    sum(di.ptype_col_51) AS ptype_col_51
                   FROM ( SELECT so.id AS idd,
                            pt.categ_id,
                                CASE
                                    WHEN pt.categ_id = 49 THEN sum(sol.total_dimension)
                                    ELSE 0.0
                                END AS ptype_col_49,
                                CASE
                                    WHEN pt.categ_id = 50 THEN sum(sol.total_dimension)
                                    ELSE 0.0
                                END AS ptype_col_50,
                                CASE
                                    WHEN pt.categ_id = 51 THEN sum(sol.total_dimension)
                                    ELSE 0.0
                                END AS ptype_col_51
                           FROM sale_order_line sol
                             JOIN sale_order so ON sol.order_id = so.id
                             JOIN product_product pp ON sol.product_id = pp.id
                             JOIN product_template pt ON pt.id = pp.product_tmpl_id
                          WHERE pt.categ_id = ANY (ARRAY[49, 50, 51])
                          GROUP BY so.id, pt.categ_id
                          ORDER BY so.id) di
                  GROUP BY di.idd) dim ON dim.idd = sales.order_id
        )"""
        cr.execute(sql)
    def despacho_form(self, cr, uid, ids, context=None):

        line = self.browse(cr, uid, ids[0], context=context)
        a = line.picking_id
        line_id=self.pool.get('stock.picking').search(cr,uid,[('id','=',line.picking_id.id)])
        line_id=line_id[0]
        action_form = {
            'name': "Albaran de Salida",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'stock.picking',
            'res_id': line_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': context,
        }
        return action_form
        


class pret_cubiertas_report3(osv.osv):
    """docstring for pret_cubiertas_report"""
    _name = "pret.cubiertas.report3"
    _description = 'Informe de Ventas por Producto'
    _auto = False

    _columns = {
        'product_id': fields.many2one('product.product', 'Product'),
        'name': fields.char(u'Producto', readonly=True),
        'quantity': fields.float('Total M.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'price': fields.float('Precio Unit.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_bruto': fields.float('Total Bruto', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'taxes': fields.float('Impuesto 13% Iva y 3% Ite', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_neto': fields.float('Total Neto', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'date': fields.date(u'Fecha', readonly=True),
        'date_day': fields.char(u'Día', size=10, readonly=True),
        'date_month': fields.char(u'Mes', readonly=True),
        'date_week': fields.char(u'Semana', readonly=True),
       
        'date2': fields.date('Fecha', readonly=True),

    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='search', context=None, toolbar=False, submenu=False):
        if view_type == 'search' and 'params' in context:
            cr.execute("REFRESH MATERIALIZED VIEW pret_cubiertas_report3;")
        res = super(pret_cubiertas_report3, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
        return res

    def init(self, cr):
        #tools.sql.drop_view_if_exists(cr, 'pret_cubiertas_report3')
        sql = """DROP MATERIALIZED VIEW IF EXISTS pret_cubiertas_report3;
                    CREATE MATERIALIZED VIEW pret_cubiertas_report3 as (
                select 
                    row_number() over() as id,
                    *,
                    cast
                        (extract(year from a.date) as char(4)) || 
                        '-' || 
                        case 
                            when extract(month from a.date) <10 Then '0' 
                            Else '' 
                    End || 
                    cast(extract(month from a.date) as varchar)   as date_month,
                    cast(extract(year from a.date) as char(4)) || '/' || cast(extract(week from a.date) as char(3)) as date_week,
                    to_char(a.date,'DD/MM/YYYY') as date_day,
                    to_date(to_char(a.date,'YYYY/MM/DD'), 'YYYY/MM/DD') as date2

                from
                (
            select 
                so.id as sale,
                pp.name_template as name,
                sol.product_id,
                sol.total_dimension as quantity,
                sp.date_done as date,
                sol.discount,
                (sol.price_unit * product_uom_qty) - ((sol.price_unit * product_uom_qty )* (sol.discount/100) )  as total_bruto ,
                ((sol.price_unit * product_uom_qty) - ((sol.price_unit * product_uom_qty )* (sol.discount/100) ) )* 0.16 as taxes,
                 ((sol.price_unit * product_uom_qty) - ((sol.price_unit * product_uom_qty )* (sol.discount/100) )) - ( ((sol.price_unit * product_uom_qty) - ((sol.price_unit * product_uom_qty )* (sol.discount/100) ) ) * 0.16) as total_neto,
                sol.price_unit as price
            from 
                sale_order_line sol
                left join sale_order so on so.id = sol.order_id
                inner join (select t1.picking_id, t2.order_id
                from procurement_order t0
                inner join stock_move t1 on t1.procurement_id = t0.id
                inner join sale_order_line t2 on t2.id = t0.sale_line_id
                group by t1.picking_id, t2.order_id) sa on sa.order_id=so.id
                inner join stock_picking sp on sp.id = sa.picking_id
                left join product_product pp on pp.id = sol.product_id

                where sp.state = 'done' and sol.product_id in (select
                        p.id
                    from
                        product_product p

                        left join product_template pt on pt.id=p.product_tmpl_id
                        left join product_category pc on pc.id=pt.categ_id
                    where
                        pc.in_rep_cubiertas = True
                    group by
                        p.id
                   )
            order by so.id) as a)
            """
        cr.execute(sql)


class pret_cubiertas_report4(osv.osv):
    """docstring for pret_cubiertas_report"""
    _name = "pret.cubiertas.report4"
    _description = 'Informe de Ventas por Vendedor'
    _auto = False

    _columns = {
        'shop_id': fields.many2one('stock.warehouse', 'Sucursal', readonly=True),
        'user_id': fields.many2one('res.users', 'Vendedor', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Cliente', readonly=True),
        'date': fields.date('Fecha de Entrega', readonly=True),
        'order_id': fields.many2one('sale.order', 'Orden de Venta', readonly=True),
        'picking_id': fields.many2one('stock.picking', 'Albaran de Salida', readonly=True),
        'amount_total': fields.float('Monto Total', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'discount': fields.float('Descuento Total', readonly=True),
        'estado': fields.selection([('vpe','VENDIDO X ENTREGAR'),('ve','VENDIDO ENTREGADO'),('pendiente','PENDIENTE'),('perdida','PERDIDA')], string="ESTADO"),
        'city': fields.char('Dirc. Envio', readonly=True),
        'total_metric': fields.float('Total M.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_metric_m2': fields.float('Total M2.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'total_metric_m3': fields.float('Total M3.', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'date_day': fields.char(u'Día', size=10, readonly=True),
        'date_month': fields.char(u'Mes', readonly=True),
        'date_week': fields.char(u'Semana', readonly=True),
        'date2': fields.date(u'Fecha', readonly=True),

    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='search', context=None, toolbar=False, submenu=False):
        if view_type == 'search' and 'params' in context:
            cr.execute("REFRESH MATERIALIZED VIEW pret_cubiertas_report4;")
        res = super(pret_cubiertas_report4, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
        return res

    def init(self, cr):
        #tools.sql.drop_view_if_exists(cr, 'pret_cubiertas_report4')
        sql = """DROP MATERIALIZED VIEW IF EXISTS pret_cubiertas_report4;
                    CREATE MATERIALIZED VIEW pret_cubiertas_report4 as (
             SELECT row_number() OVER () AS id,
                sales.shop_id,
                sales.user_id,
                sales.partner_id,
                sales.order_id,
                sales.picking_id,
                sales.amount_total,
                sales.discount,
                sales.estado,
                sales.city,
                sales.total_metric,
                sales.total_metric_m2,
                sales.total_metric_m3,
                sales.date,
                dim.idd,
                dim.ptype_col_49,
                dim.ptype_col_50,
                dim.ptype_col_51,
                ((date_part('year'::text, sales.date)::character(4)::text || '-'::text) ||
                    CASE
                        WHEN date_part('month'::text, sales.date) < 10::double precision THEN '0'::text
                        ELSE ''::text
                    END) || date_part('month'::text, sales.date)::character varying::text AS date_month,
                (date_part('year'::text, sales.date)::character(4)::text || '/'::text) || date_part('week'::text, sales.date)::character(3)::text AS date_week,
                to_char(sales.date, 'DD/MM/YYYY'::text) AS date_day,
                to_date(to_char(sales.date, 'YYYY/MM/DD'::text), 'YYYY/MM/DD'::text) AS date2
               FROM ( SELECT so.shop_id,
                        so.user_id,
                        so.partner_id,
                        so.id AS order_id,
                        max(sp.id) AS picking_id,
                        so.amount_total,
                        so.discount_global AS discount,
                            CASE
                                WHEN max(sp.state::text) = ANY (ARRAY['draft'::text, 'auto'::text, 'confirmed'::text, 'assigned'::text]) THEN 'vpe'::text
                                WHEN max(sp.state::text) = 'done'::text THEN 've'::text
                                WHEN max(sp.state::text) = 'cancel'::text THEN 'perdida'::text
                                ELSE
                                CASE
                                    WHEN so.state::text = 'cancel'::text THEN 'perdida'::text
                                    WHEN so.state::text = ANY (ARRAY['draft'::character varying, 'sent'::character varying]::text[]) THEN 'pendiente'::text
                                    ELSE NULL::text
                                END
                            END AS estado,
                        max(lower(rp.city::text)) AS city,
                        to_number(max(so.total_metric::text), '999999999999.999'::text) AS total_metric,
                        to_number(max(so.total_metric_m2::text), '9999999999.999'::text) AS total_metric_m2,
                        to_number(max(so.total_metric_m3::text), '999999999.999'::text) AS total_metric_m3,
                        max(sp.date_done) AS date
                       FROM sale_order so
                         INNER JOIN (SELECT t3.order_id, s1.picking_id
                                    FROM sale_order_line t3
                                      INNER JOIN procurement_order s0 ON s0.sale_line_id = t3.id
                                      INNER JOIN stock_move s1 ON s1.procurement_id = s0.id
                                     group by t3.order_id, s1.picking_id
                                     order by t3.order_id) ddd on ddd.order_id = so.id
                         LEFT JOIN stock_picking sp ON sp.id = ddd.picking_id
                         LEFT JOIN res_partner rp ON rp.id = so.partner_shipping_id
                      WHERE sp.state::text = 'done'::text
                      GROUP BY so.id) sales
                 JOIN ( SELECT di.idd,
                        sum(di.ptype_col_49) AS ptype_col_49,
                        sum(di.ptype_col_50) AS ptype_col_50,
                        sum(di.ptype_col_51) AS ptype_col_51
                       FROM ( SELECT so.id AS idd,
                                pt.categ_id,
                                    CASE
                                        WHEN pt.categ_id = 49 THEN sum(sol.total_dimension)
                                        ELSE 0.0
                                    END AS ptype_col_49,
                                    CASE
                                        WHEN pt.categ_id = 50 THEN sum(sol.total_dimension)
                                        ELSE 0.0
                                    END AS ptype_col_50,
                                    CASE
                                        WHEN pt.categ_id = 51 THEN sum(sol.total_dimension)
                                        ELSE 0.0
                                    END AS ptype_col_51
                               FROM sale_order_line sol
                                 JOIN sale_order so ON sol.order_id = so.id
                                 JOIN product_product pp ON sol.product_id = pp.id
                                 JOIN product_template pt ON pt.id = pp.product_tmpl_id
                              WHERE pt.categ_id = ANY (ARRAY[49, 50, 51])
                              GROUP BY so.id, pt.categ_id
                              ORDER BY so.id) di
                      GROUP BY di.idd) dim ON dim.idd = sales.order_id
            --where sales.picking_id in (1505,1068)
            )
            """
        cr.execute(sql)

    def so2_form(self, cr, uid, ids, context=None):

        line = self.browse(cr, uid, ids[0], context=context)
        line_id=self.pool.get('sale.order').search(cr, uid, [('id','=',line.order_id.id)])
        line_id=line_id[0]
        action_form = {
            'name': "Pedido de Ventas",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sale.order',
            'res_id': line_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': context,
        }
        return action_form