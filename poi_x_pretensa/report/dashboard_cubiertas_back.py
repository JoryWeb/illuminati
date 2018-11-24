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

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'pret_cubiertas_report')
        sql = """
        CREATE or replace view pret_cubiertas_report as (
        select ROW_NUMBER() OVER(ORDER BY order_id) AS id, foo2.* from (
              select shop_id, date_order as date, day, year, month, week, partner_id, order_id, picking_id, amount_total,
                 sum(total_m) as total_metric,
                  sum(total_m2) as total_metric_m2,
                  sum(total_m3) as total_metric_m3 from
                  (
                    SELECT
                      u0.shop_id,
                      u0.date_order,
                      to_char(u0.date_order,'DD/MM/YYYY') as day,
                      to_char(u0.date_order, 'YYYY') as year,
                      to_char(u0.date_order, 'MM') as month,
                      extract(week from u0.date_order::date) as week,
                      t1.partner_id,
                      t3.order_id,
                      s1.picking_id,
                      u0.amount_total,
                      0                                                AS total_m,
                      0                                                AS total_m2,
                      0                                                AS total_m3
                    FROM account_invoice_line t0
                      INNER JOIN account_invoice t1 ON t1.id = t0.invoice_id
                      INNER JOIN sale_order_line_invoice_rel t2 ON t2.invoice_line_id = t0.id
                      INNER JOIN sale_order_line t3 ON t3.id = t2.order_line_id
                      INNER JOIN sale_order u0 on u0.id = t3.order_id
                      INNER JOIN procurement_order s0 on s0.sale_line_id = t3.id
                      INNER JOIN stock_move s1 on s1.procurement_id = s0.id
                      INNER JOIN stock_picking s2 on s2.id = s1.picking_id
                      INNER JOIN product_product t4 ON t4.id = t3.product_id
                      INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                      INNER JOIN product_category t6 ON t6.id = t5.categ_id
                    where s2.state in ('done')
                    UNION ALL
                    SELECT
                      u0.shop_id,
                      u0.date_order,
                      to_char(u0.date_order,'DD/MM/YYYY') as day,
                      to_char(u0.date_order, 'YYYY') as year,
                      to_char(u0.date_order, 'MM') as month,
                      extract(week from u0.date_order::date) as week,
                      t1.partner_id,
                      t3.order_id,
                      s1.picking_id,
                      u0.amount_total,
                      CASE WHEN t6.udm_rep_ventas = 'm'
                        THEN t3.total_dimension
                      ELSE 0 END                                       AS total_m,
                      0                                                AS total_m2,
                      0                                                AS total_m3
                    FROM account_invoice_line t0
                      INNER JOIN account_invoice t1 ON t1.id = t0.invoice_id
                      INNER JOIN sale_order_line_invoice_rel t2 ON t2.invoice_line_id = t0.id
                      INNER JOIN sale_order_line t3 ON t3.id = t2.order_line_id
                      INNER JOIN sale_order u0 on u0.id = t3.order_id
                      INNER JOIN procurement_order s0 on s0.sale_line_id = t3.id
                      INNER JOIN stock_move s1 on s1.procurement_id = s0.id
                      INNER JOIN stock_picking s2 on s2.id = s1.picking_id
                      INNER JOIN product_product t4 ON t4.id = t3.product_id
                      INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                      INNER JOIN product_category t6 ON t6.id = t5.categ_id
                    where s2.state in ('done')

                    UNION ALL
                      select u0.shop_id,
                      u0.date_order,
                      to_char(u0.date_order,'DD/MM/YYYY') as day,
                      to_char(u0.date_order, 'YYYY') as year,
                      to_char(u0.date_order, 'MM') as month,
                      extract(week from u0.date_order::date) as week,
                      t1.partner_id,
                      t3.order_id,
                      s1.picking_id,
                      u0.amount_total,
                  0 as total_m,
                  CASE WHEN t6.udm_rep_ventas = 'm2' THEN
                    t3.total_dimension
                    ELSE 0 END as total_m2,
                  0 as total_m3
                FROM account_invoice_line t0
                      INNER JOIN account_invoice t1 ON t1.id = t0.invoice_id
                      INNER JOIN sale_order_line_invoice_rel t2 ON t2.invoice_line_id = t0.id
                      INNER JOIN sale_order_line t3 ON t3.id = t2.order_line_id
                      INNER JOIN sale_order u0 on u0.id = t3.order_id
                      INNER JOIN procurement_order s0 on s0.sale_line_id = t3.id
                      INNER JOIN stock_move s1 on s1.procurement_id = s0.id
                      INNER JOIN stock_picking s2 on s2.id = s1.picking_id
                      INNER JOIN product_product t4 ON t4.id = t3.product_id
                      INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                      INNER JOIN product_category t6 ON t6.id = t5.categ_id
                    where s2.state in ('done')
                    UNION ALL
                  select u0.shop_id,
                      u0.date_order,
                      to_char(u0.date_order,'DD/MM/YYYY') as day,
                      to_char(u0.date_order, 'YYYY') as year,
                      to_char(u0.date_order, 'MM') as month,
                      extract(week from u0.date_order::date) as week,
                      t1.partner_id,
                      t3.order_id,
                      s1.picking_id,
                      u0.amount_total,
                  0 as total_m,
                  0 as total_m2,
                  CASE WHEN t6.udm_rep_ventas = 'm3' THEN
                    t3.total_dimension
                    ELSE 0 END as total_m3

                FROM account_invoice_line t0
                      INNER JOIN account_invoice t1 ON t1.id = t0.invoice_id
                      INNER JOIN sale_order_line_invoice_rel t2 ON t2.invoice_line_id = t0.id
                      INNER JOIN sale_order_line t3 ON t3.id = t2.order_line_id
                      INNER JOIN sale_order u0 on u0.id = t3.order_id
                      INNER JOIN procurement_order s0 on s0.sale_line_id = t3.id
                      INNER JOIN stock_move s1 on s1.procurement_id = s0.id
                      INNER JOIN stock_picking s2 on s2.id = s1.picking_id
                      INNER JOIN product_product t4 ON t4.id = t3.product_id
                      INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                      INNER JOIN product_category t6 ON t6.id = t5.categ_id
                    where s2.state in ('done')
                  )
                  as foo group by shop_id, date_order, day, year, month, week, partner_id, order_id, picking_id, amount_total
                  order by date_order
                  ) as foo2
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
    
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'pret_cubiertas_report2')
        sql = """
        CREATE or replace view pret_cubiertas_report2 as (
            select ROW_NUMBER() OVER(ORDER BY order_id) AS id, foo2.* from (
              SELECT
                shop_id,
                to_date(to_char(date_order,'YYYY/MM/DD'), 'YYYY/MM/DD') as date2,
                day as date_day,
                year as date_year,
                month as date_month,
                week as date_week,
                partner_id,
                order_id,
                picking_id,
                direccion,
                city,
                user_id,
                date_done,
                total_weight,
                sum(total_m) as total_metric,
                sum(total_m2) as total_metric_m2,
                sum(total_m3) as total_metric_m3
              FROM
                (
                  SELECT
                    u0.shop_id,
                    u0.date_order,
                    to_char(u0.date_order, 'DD/MM/YYYY')     AS day,
                    to_char(u0.date_order, 'YYYY')           AS year,
                    to_char(u0.date_order, 'YYYY-MM')             AS month,
                    extract(WEEK FROM u0.date_order :: DATE) AS week,
                    t1.partner_id,
                    t3.order_id,
                    s1.picking_id,
                    u1.street                                AS direccion,
                    u1.city                                  AS city,
                    u0.user_id,
                    s2.date_done,
                    CASE WHEN t6.udm_rep_ventas = 'm'
                      THEN t3.total_dimension
                    ELSE 0 END                               AS total_m,
                    0                                        AS total_m2,
                    0                                        AS total_m3,
                    u0.total_weight
                  FROM account_invoice_line t0
                    INNER JOIN account_invoice t1 ON t1.id = t0.invoice_id
                    INNER JOIN sale_order_line_invoice_rel t2 ON t2.invoice_line_id = t0.id
                    INNER JOIN sale_order_line t3 ON t3.id = t2.order_line_id
                    INNER JOIN sale_order u0 ON u0.id = t3.order_id
                    INNER JOIN res_partner u1 ON u1.id = u0.partner_id
                    INNER JOIN procurement_order s0 ON s0.sale_line_id = t3.id
                    INNER JOIN stock_move s1 ON s1.procurement_id = s0.id
                    INNER JOIN stock_picking s2 ON s2.id = s1.picking_id
                    INNER JOIN product_product t4 ON t4.id = t3.product_id
                    INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                    INNER JOIN product_category t6 ON t6.id = t5.categ_id
                  WHERE s2.state IN ('done')

                  UNION ALL
                  SELECT
                    u0.shop_id,
                    u0.date_order,
                    to_char(u0.date_order, 'DD/MM/YYYY')     AS day,
                    to_char(u0.date_order, 'YYYY')           AS year,
                    to_char(u0.date_order, 'YYYY-MM')             AS month,
                    extract(WEEK FROM u0.date_order :: DATE) AS week,
                    t1.partner_id,
                    t3.order_id,
                    s1.picking_id,
                    u1.street                                AS direccion,
                    u1.city                                  AS city,
                    u0.user_id,
                    s2.date_done,
                    0                                        AS total_m,
                    CASE WHEN t6.udm_rep_ventas = 'm2'
                      THEN t3.total_dimension
                    ELSE 0 END                               AS total_m2,
                    0                                        AS total_m3,
                    u0.total_weight
                  FROM account_invoice_line t0
                    INNER JOIN account_invoice t1 ON t1.id = t0.invoice_id
                    INNER JOIN sale_order_line_invoice_rel t2 ON t2.invoice_line_id = t0.id
                    INNER JOIN sale_order_line t3 ON t3.id = t2.order_line_id
                    INNER JOIN sale_order u0 ON u0.id = t3.order_id
                    INNER JOIN res_partner u1 ON u1.id = u0.partner_id
                    INNER JOIN procurement_order s0 ON s0.sale_line_id = t3.id
                    INNER JOIN stock_move s1 ON s1.procurement_id = s0.id
                    INNER JOIN stock_picking s2 ON s2.id = s1.picking_id
                    INNER JOIN product_product t4 ON t4.id = t3.product_id
                    INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                    INNER JOIN product_category t6 ON t6.id = t5.categ_id
                  WHERE s2.state IN ('done')
                  UNION ALL
                  SELECT
                    u0.shop_id,
                    u0.date_order,
                    to_char(u0.date_order, 'DD/MM/YYYY')     AS day,
                    to_char(u0.date_order, 'YYYY')           AS year,
                    to_char(u0.date_order, 'YYYY-MM')             AS month,
                    extract(WEEK FROM u0.date_order :: DATE) AS week,
                    t1.partner_id,
                    t3.order_id,
                    s1.picking_id,
                    u1.street                                AS direccion,
                    u1.city                                  AS city,
                    u0.user_id,
                    s2.date_done,
                    0                                        AS total_m,
                    0                                        AS total_m2,
                    CASE WHEN t6.udm_rep_ventas = 'm3'
                      THEN t3.total_dimension
                    ELSE 0 END                               AS total_m3,
                    u0.total_weight
                  FROM account_invoice_line t0
                    INNER JOIN account_invoice t1 ON t1.id = t0.invoice_id
                    INNER JOIN sale_order_line_invoice_rel t2 ON t2.invoice_line_id = t0.id
                    INNER JOIN sale_order_line t3 ON t3.id = t2.order_line_id
                    INNER JOIN sale_order u0 ON u0.id = t3.order_id
                    INNER JOIN res_partner u1 ON u1.id = u0.partner_id
                    INNER JOIN procurement_order s0 ON s0.sale_line_id = t3.id
                    INNER JOIN stock_move s1 ON s1.procurement_id = s0.id
                    INNER JOIN stock_picking s2 ON s2.id = s1.picking_id
                    INNER JOIN product_product t4 ON t4.id = t3.product_id
                    INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                    INNER JOIN product_category t6 ON t6.id = t5.categ_id
                  WHERE s2.state IN ('done')

                )
                  AS foo
              GROUP BY shop_id, date_order, day, year, month, week, partner_id, order_id, picking_id, direccion, city, user_id,
                date_done, total_weight
              ORDER BY date_order
            ) as foo2
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
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'pret_cubiertas_report3')
        sql = """
             CREATE or replace view pret_cubiertas_report3 as (
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

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'pret_cubiertas_report4')
        sql = """
            CREATE or replace view pret_cubiertas_report4 as (
            select ROW_NUMBER() OVER(ORDER BY order_id) AS id, foo2.* from (
              SELECT
                shop_id,
                date2,
                date_done as date,
                day as date_day,
                year as date_year,
                month as date_month,
                week as date_week,
                partner_id,
                order_id,
                picking_id,
                direccion,
                estado,
                city,
                user_id,
                amount_total,
                discount_global as discount,
                sum(total_m)  AS total_metric,
                sum(total_m2) AS total_metric_m2,
                sum(total_m3) AS total_metric_m3
              FROM
                (
                  SELECT
                    u0.shop_id,
                    u0.date_order                            AS date2,
                    to_char(s2.date_done, 'DD/MM/YYYY')     AS day,
                    to_char(s2.date_done, 'YYYY')           AS year,
                    to_char(s2.date_done, 'YYYY-MM')        AS month,
                    extract(WEEK FROM u0.date_order :: DATE) AS week,
                    u0.partner_id,
                    t3.order_id,
                    s1.picking_id,
                    CASE
                    WHEN s2.state IN ('draft', 'auto', 'confirmed', 'assigned')
                      THEN 'vpe'
                    WHEN s2.state IN ('done')
                      THEN 've'
                    WHEN s2.state IN ('cancel')
                      THEN 'perdida'
                    ELSE
                      CASE
                      WHEN u0.state IN ('cancel')
                        THEN 'perdida'
                      WHEN u0.state IN ('draft', 'sent')
                        THEN 'pendiente'
                      END
                    END                                      AS estado,
                    u1.street                                AS direccion,
                    u1.city                                  AS city,
                    u0.user_id,
                    s2.date_done,
                    u0.amount_total,
                    u0.discount_global,
                    CASE WHEN t6.udm_rep_cubiertas = 'm'
                      THEN t3.total_dimension
                    ELSE 0 END                               AS total_m,
                    0                                        AS total_m2,
                    0                                        AS total_m3,
                    u0.total_weight
                  FROM sale_order_line t3
                    INNER JOIN sale_order u0 ON u0.id = t3.order_id
                    INNER JOIN res_partner u1 ON u1.id = u0.partner_id
                    INNER JOIN procurement_order s0 ON s0.sale_line_id = t3.id
                    INNER JOIN stock_move s1 ON s1.procurement_id = s0.id
                    INNER JOIN stock_picking s2 ON s2.id = s1.picking_id
                    INNER JOIN product_product t4 ON t4.id = t3.product_id
                    INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                    INNER JOIN product_category t6 ON t6.id = t5.categ_id
                    WHERE s2.state in ('done') and t6.id in (49, 50, 51)
                  UNION ALL
                    SELECT
                    u0.shop_id,
                    u0.date_order                            AS date2,
                    to_char(s2.date_done, 'DD/MM/YYYY')     AS day,
                    to_char(s2.date_done, 'YYYY')           AS year,
                    to_char(s2.date_done, 'YYYY-MM')        AS month,
                    extract(WEEK FROM u0.date_order :: DATE) AS week,
                    u0.partner_id,
                    t3.order_id,
                    s1.picking_id,
                    CASE
                    WHEN s2.state IN ('draft', 'auto', 'confirmed', 'assigned')
                      THEN 'vpe'
                    WHEN s2.state IN ('done')
                      THEN 've'
                    WHEN s2.state IN ('cancel')
                      THEN 'perdida'
                    ELSE
                      CASE
                      WHEN u0.state IN ('cancel')
                        THEN 'perdida'
                      WHEN u0.state IN ('draft', 'sent')
                        THEN 'pendiente'
                      END
                    END                                      AS estado,
                    u1.street                                AS direccion,
                    u1.city                                  AS city,
                    u0.user_id,
                    s2.date_done,
                    u0.amount_total,
                    u0.discount_global,
                    0                              AS total_m,
                    CASE WHEN t6.udm_rep_cubiertas = 'm2'
                      THEN t3.total_dimension
                    ELSE 0 END  AS total_m2,
                    0                                        AS total_m3,
                    u0.total_weight
                  FROM sale_order_line t3
                    INNER JOIN sale_order u0 ON u0.id = t3.order_id
                    INNER JOIN res_partner u1 ON u1.id = u0.partner_id
                    INNER JOIN procurement_order s0 ON s0.sale_line_id = t3.id
                    INNER JOIN stock_move s1 ON s1.procurement_id = s0.id
                    INNER JOIN stock_picking s2 ON s2.id = s1.picking_id
                    INNER JOIN product_product t4 ON t4.id = t3.product_id
                    INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                    INNER JOIN product_category t6 ON t6.id = t5.categ_id
                    WHERE s2.state in ('done') and t6.id in (49,50,51)
                  UNION ALL
                    SELECT
                    u0.shop_id,
                    u0.date_order                            AS date2,
                    to_char(s2.date_done, 'DD/MM/YYYY')     AS day,
                    to_char(s2.date_done, 'YYYY')           AS year,
                    to_char(s2.date_done, 'YYYY-MM')        AS month,
                    extract(WEEK FROM u0.date_order :: DATE) AS week,
                    u0.partner_id,
                    t3.order_id,
                    s1.picking_id,
                    CASE
                    WHEN s2.state IN ('draft', 'auto', 'confirmed', 'assigned')
                      THEN 'vpe'
                    WHEN s2.state IN ('done')
                      THEN 've'
                    WHEN s2.state IN ('cancel')
                      THEN 'perdida'
                    ELSE
                      CASE
                      WHEN u0.state IN ('cancel')
                        THEN 'perdida'
                      WHEN u0.state IN ('draft', 'sent')
                        THEN 'pendiente'
                      END
                    END                                      AS estado,
                    u1.street                                AS direccion,
                    u1.city                                  AS city,
                    u0.user_id,
                    s2.date_done,
                    u0.amount_total,
                    u0.discount_global,
                    0                              AS total_m,
                    0  AS total_m2,
                    CASE WHEN t6.udm_rep_cubiertas = 'm3'
                      THEN t3.total_dimension
                    ELSE 0 END AS total_m3,
                    u0.total_weight
                  FROM sale_order_line t3
                    INNER JOIN sale_order u0 ON u0.id = t3.order_id
                    INNER JOIN res_partner u1 ON u1.id = u0.partner_id
                    INNER JOIN procurement_order s0 ON s0.sale_line_id = t3.id
                    INNER JOIN stock_move s1 ON s1.procurement_id = s0.id
                    INNER JOIN stock_picking s2 ON s2.id = s1.picking_id
                    INNER JOIN product_product t4 ON t4.id = t3.product_id
                    INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                    INNER JOIN product_category t6 ON t6.id = t5.categ_id
                    WHERE s2.state in ('done') and t6.id in (49,50,51)
                ) AS foo
              group by shop_id, date_done, date2, day, year, month, week, partner_id,
                order_id, picking_id, direccion, estado, city, user_id, amount_total,
                discount_global
            ) as foo2
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