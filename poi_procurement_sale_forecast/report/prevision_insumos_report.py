from openerp import fields, models, tools

class PoiPrevisionInsumosReport(models.Model):
    _name = "poi.prevision.insumos.report"
    _description = "Reporte de origen de insumos"
    _auto = False

    product_id = fields.Many2one('product.product', string=u'Producto', readonly=True)
    location_id = fields.Many2one('stock.location', string=u'Ubicación', readonly=True, help=u"")
    date = fields.Date(string=u"Fecha", help=u"")
    uom_id = fields.Many2one("product.uom", string=u"UdM")
    cant_max = fields.Char(string=u"Mínimo Requerido", readonly=True, help=u"Cantida máxima configurada en un regla de abastecimiento")
    cant_min = fields.Char(string=u"Máximo Requerido", readonly=True, help=u"Cantida mínima configurada en un regla de abastecimiento")
    stock_actual = fields.Char(string=u"Stock Actual", readonly=True, help=u"Cantidad actual en la ubicación")
    cant_planificada = fields.Float(string=u"Planificado", readonly=True, help=u"Cantidad definida en las previsiones de venta o producción")
    cant_prevista = fields.Float(string=u"Previsto", readonly=True, help=u"Compras + previsiones + ajustes inventario + entradas por producción")
    cant_solicitada = fields.Float(string=u"Solicitado", readonly=True, help=u"Solicitudes de stock + solicitudes de insumos + salidas de almacén")
    stock_futuro = fields.Char(string=u"Stock a Futuro", readonly=True, help=u"Stock que se prevee tener al ejecutar la cantidad solicitada contra la cantidad prevista")
    ultimo_stock = fields.Float(string=u"Último Stock", readonly=True, help=u"Stock total para agrupar")
    _order = 'date asc'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'poi_prevision_insumos_report')
        cr.execute("""
        create or replace view poi_prevision_insumos_report as (
            SELECT
  row_number()
  OVER ()                                                               AS id,
  plan2.product_id,
  plan2.date,
  coalesce(swo.product_max_qty, 0)                                      AS cant_max,
  coalesce(swo.product_min_qty, 0)                                      AS cant_min,
  plan2.location_id,
  plan2.cant_planificada,
  plan2.cant_prevista,
  plan2.cant_solicitada,
  plan2.stock_actual,
  plan2.uom_id,
  round((coalesce(plan2.stock_actual, 0.0) + coalesce(stock_previsto,0.0) - coalesce(stock_solicitado,0.0))::NUMERIC, 2) AS stock_futuro,
  CASE WHEN plan2.lead2 is null THEN
    (coalesce(plan2.stock_actual, 0) + stock_previsto - stock_solicitado)
    ELSE
    0 END AS ultimo_stock
FROM (
SELECT
  *,
  (sum(COALESCE(plan.cant_solicitada, 0))
  OVER w)  AS stock_solicitado,
  (sum(COALESCE(plan.cant_prevista, 0))
  OVER w)  AS stock_previsto,
  LEAD(plan.cant_planificada)
  OVER w   AS lead2
FROM (
       SELECT
         coalesce(foo3.product_id, foo2.product_id)     AS product_id,
         coalesce(foo3.date, foo2.date)                 AS date,
         coalesce(foo3.qty, 0)                          AS cant_planificada,
         coalesce(foo3.lot_stock_id, foo2.location_id)  AS location_id,
         coalesce(foo3.uom_id, foo2.product_uom)        AS uom_id,
         coalesce(foo3.stock_actual, foo2.stock_actual) AS stock_actual,
         coalesce(foo2.cant_entrada, 0)                 AS cant_prevista,
         coalesce(foo2.cant_salida * (-1), 0)           AS cant_solicitada
       FROM (
              SELECT
                foo.product_id,
                foo.product_uom,
                foo.location_id,
                foo.date,
                sum(foo.cant_entrada)              AS cant_entrada,
                sum(foo.cant_salida)               AS cant_salida,
                (SELECT sum(qty)
                 FROM stock_quant
                 WHERE product_id = foo.product_id
                       AND location_id = foo.location_id
                       AND reservation_id IS NULL) AS stock_actual
              FROM (
                     SELECT
                       f0.state,
                       f0.product_id,
                       f0.product_qty                                  AS cant_entrada,
                       0                                               AS cant_salida,
                       f0.product_uom,
                       f0.location_dest_id                             AS location_id,
                       (f0.date_expected - INTERVAL '4 HOURS') :: DATE AS date
                     FROM stock_move f0
                       INNER JOIN stock_location f1 ON f1.id = f0.location_dest_id
                     WHERE f0.state NOT IN ('cancel', 'done')
                           AND f1.usage IN ('internal')
                     UNION ALL
                     SELECT
                       f0.state,
                       f0.product_id,
                       0                                               AS cant_entrada,
                       f0.product_qty * (-1)                           AS cant_salda,
                       f0.product_uom,
                       f0.location_id                                  AS location_id,
                       (f0.date_expected - INTERVAL '4 HOURS') :: DATE AS date
                     FROM stock_move f0
                       INNER JOIN stock_location f1 ON f1.id = f0.location_id
                     WHERE f0.state NOT IN ('cancel', 'done')
                           AND f1.usage IN ('internal')
                   ) AS foo
              GROUP BY product_id,
                product_uom,
                location_id,
                date
              ORDER BY date
            ) AS foo2
         LEFT JOIN (SELECT
                      t0.product_id,
                      t0.qty,
                      t0.date,
                      t2.lot_stock_id,
                      t4.uom_id,
                      (SELECT sum(qty)
                       FROM stock_quant
                       WHERE product_id = t0.product_id
                             AND location_id = t2.lot_stock_id
                             AND reservation_id IS NULL) AS stock_actual
                    FROM procurement_sale_forecast_line t0
                      INNER JOIN procurement_sale_forecast t1 ON t1.id = t0.forecast_id
                      INNER JOIN stock_warehouse t2 ON t2.id = t1.warehouse_id
                      INNER JOIN product_product t3 ON t3.id = t0.product_id
                      INNER JOIN product_template t4 ON t4.id = t3.product_tmpl_id
                    ORDER BY t0.date) AS foo3
           ON foo3.product_id = foo2.product_id AND foo3.date = foo2.date AND
              foo3.lot_stock_id = foo2.location_id

       UNION

       SELECT
         coalesce(foo2.product_id, foo3.product_id)     AS product_id,
         coalesce(foo2.date, foo3.date)                 AS date,
         coalesce(foo2.qty, 0)                          AS cant_planificada,
         coalesce(foo2.lot_stock_id, foo3.location_id)  AS location_id,
         coalesce(foo2.uom_id, foo3.product_uom)        AS uom_id,
         coalesce(foo2.stock_actual, foo3.stock_actual) AS stock_actual,
         coalesce(foo3.cant_entrada, 0)                 AS cant_prevista,
         coalesce(foo3.cant_salida, 0)                  AS cant_solicitada

       FROM (
              SELECT
                t0.product_id,
                t0.qty,
                t0.date,
                t2.lot_stock_id,
                t4.uom_id,
                (SELECT sum(qty)
                 FROM stock_quant
                 WHERE product_id = t0.product_id
                       AND location_id = t2.lot_stock_id
                       AND reservation_id IS NULL) AS stock_actual
              FROM procurement_sale_forecast_line t0
                INNER JOIN procurement_sale_forecast t1 ON t1.id = t0.forecast_id
                INNER JOIN stock_warehouse t2 ON t2.id = t1.warehouse_id
                INNER JOIN product_product t3 ON t3.id = t0.product_id
                INNER JOIN product_template t4 ON t4.id = t3.product_tmpl_id
              ORDER BY t0.date) AS foo2
         LEFT JOIN (
                     SELECT
                       foo.product_id,
                       foo.product_uom,
                       foo.location_id,
                       foo.date,
                       sum(foo.cant_entrada)              AS cant_entrada,
                       sum(foo.cant_salida)               AS cant_salida,
                       (SELECT sum(qty)
                        FROM stock_quant
                        WHERE product_id = foo.product_id
                              AND location_id = foo.location_id
                              AND reservation_id IS NULL) AS stock_actual
                     FROM (
                            SELECT
                              f0.state,
                              f0.product_id,
                              f0.product_qty                                  AS cant_entrada,
                              0                                               AS cant_salida,
                              f0.product_uom,
                              f0.location_dest_id                             AS location_id,
                              (f0.date_expected - INTERVAL '4 HOURS') :: DATE AS date
                            FROM stock_move f0
                              INNER JOIN stock_location f1 ON f1.id = f0.location_dest_id
                            WHERE f0.state NOT IN ('cancel', 'done')
                                  AND f1.usage IN ('internal')
                            UNION ALL
                            SELECT
                              f0.state,
                              f0.product_id,
                              0                                               AS cant_entrada,
                              f0.product_qty * (-1)                           AS cant_salda,
                              f0.product_uom,
                              f0.location_id                                  AS location_id,
                              (f0.date_expected - INTERVAL '4 HOURS') :: DATE AS date
                            FROM stock_move f0
                              INNER JOIN stock_location f1 ON f1.id = f0.location_id
                            WHERE f0.state NOT IN ('cancel', 'done')
                                  AND f1.usage IN ('internal')

                          ) AS foo
                     GROUP BY product_id,
                       product_uom,
                       location_id,
                       date
                     ORDER BY date
                   ) AS foo3
           ON foo3.product_id = foo2.product_id AND foo3.date = foo2.date AND
              foo3.location_id = foo2.lot_stock_id
     ) AS plan
--WHERE plan.product_id = 331
WINDOW w AS (
  PARTITION BY plan.product_id, plan.location_id
  ORDER BY plan.date ASC )
ORDER BY plan.product_id, plan.location_id, plan.date
       ) AS plan2
  LEFT JOIN stock_warehouse_orderpoint swo ON swo.product_id = plan2.product_id AND swo.location_id = plan2.location_id
--where plan2.product_id = 331
ORDER BY plan2.date ASC

        )""")
