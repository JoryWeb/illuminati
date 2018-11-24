from odoo import tools
from odoo import api, fields, models


class PoiChasisLandedCostReport(models.Model):
    _name = "poi.chasis.landed.cost.report"
    _description = "Reporte de Costos por chasis"
    _auto = False

    lot_id = fields.Many2one('stock.production.lot', string=u'Serie/Chasis', readonly=True)
    date = fields.Date(string="Fecha", readonly=True)
    move_id = fields.Many2one("stock.move", string=u"Movimiento", readonly=True)
    order_id = fields.Many2one("purchase.order", string=u"Orden de Importación", readonly=True)
    fecha_cr = fields.Datetime(string=u"Fecha creación", readonly=True)
    price_unit = fields.Float(string='Costo Bs.', readonly=True, help="Costo de compra Bs.")
    price_unit_usd = fields.Float(string='Costo USD.', readonly=True, help="Costo de compra o Dolares")
    origin = fields.Char(string='Origen', readonly=True)
    name = fields.Char(string=u"Descripción", readonly=True)
    metodo = fields.Char(string=u"Método Ditribución", readonly=True)
    valoracion = fields.Char(string=u"Valoración", readonly=True)
    bank_id = fields.Many2one('res.bank', string="Banco")
    n_prestamo = fields.Char("N° de Prestamo")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'poi_chasis_landed_cost_report')
        self.env.cr.execute("""
        create or replace view poi_chasis_landed_cost_report as (
        select row_number() over() as id, * from (
            SELECT *
                FROM (
                       SELECT DISTINCT ON (t0.lot_id)
                          t0.lot_id,
                          t1.date :: DATE           AS date,
                          t1.id                     AS move_id,
                          t3.order_id,
                          t0.create_date  AS fecha_cr,
                          t1.price_unit,
                          (select rate
                           from res_currency_rate
                           where currency_id = 3
                           order by name desc
                           limit 1) * t1.price_unit as price_unit_usd,
                          t1.origin,
                          t1.name,
                          'Inicial' :: VARCHAR      as metodo,
                          'Costo FOB' :: VARCHAR    as valoracion,
                          t4.bank_id,
                          t4.n_prestamo
                        FROM stock_move_line t0
                          INNER JOIN stock_move t1 ON t1.id = t0.move_id
                          LEFT JOIN purchase_order_line t3 on t3.id = t1.purchase_line_id
                          LEFT JOIN purchase_order t4 on t4.id = t3.order_id
                          where t1.state in ('done')
                        ORDER BY t0.lot_id, t1.date ASC
                     ) AS foo1
                UNION ALL
                SELECT *
                FROM (
                SELECT
                  t2.lot_id,
                  t5.date,
                  t0.move_id,
                  po.order_id,
                  t0.write_date                                         AS fecha_cr,
                  (t0.additional_landed_cost / t0.quantity)             AS price_unit,
                  (select rate
                   from res_currency_rate
                   where currency_id = 3
                   order by name desc
                   limit 1) * (t0.additional_landed_cost / t0.quantity) as price_unit_usd,
                  t5.name                                               AS origin,
                  t0.name,
                  CASE WHEN t1.split_method = 'by_quantity'
                    THEN
                      'Por cantidad' :: VARCHAR
                  WHEN t1.split_method = 'by_current_cost_price'
                    THEN
                      'Por costo actual' :: VARCHAR
                  WHEN t1.split_method = 'by_weight'
                    THEN
                      'Por Peso' :: VARCHAR
                  WHEN t1.split_method = 'by_volume'
                    THEN
                      'Por Volumen' :: VARCHAR
                  ELSE
                    'Igual' :: VARCHAR
                  END                                                   AS metodo,
                  'Gastos por transferencia' :: VARCHAR                 as valoracion,
                  po.bank_id,
                  po.n_prestamo
                FROM stock_valuation_adjustment_lines t0
                  INNER JOIN stock_landed_cost_lines t1 ON t1.id = t0.cost_line_id
                  INNER JOIN stock_move_line t2 ON t2.move_id = t0.move_id
                  INNER JOIN stock_production_lot t4 ON t4.id = t2.lot_id
                  INNER JOIN stock_landed_cost t5 ON t5.id = t0.cost_id
                  INNER JOIN (
                               SELECT DISTINCT ON (t0.lot_id)
                                 t0.lot_id,
                                 t1.date :: DATE        AS date,
                                 t1.id                  AS move_id,
                                 t3.order_id            as order_id,
                                 t0.create_date         AS fecha_cr,
                                 t1.price_unit,
                                 t1.origin,
                                 t1.name,
                                 'Inicial' :: VARCHAR   as metodo,
                                 'Costo FOB' :: VARCHAR as valoracion,
                                 t4.bank_id,
                                 t4.n_prestamo
                               FROM stock_move_line t0
                                 INNER JOIN stock_move t1 ON t1.id = t0.move_id
                                 LEFT JOIN purchase_order_line t3 on t3.id = t1.purchase_line_id
                                 LEFT JOIN purchase_order t4 on t4.id = t3.order_id
                                 WHERE t1.state in ('done')
                               ORDER BY t0.lot_id, t1.date ASC
                
                             ) as po on po.lot_id = t2.lot_id
                WHERE t5.state IN ('done')
                ORDER BY t2.lot_id, t5.date
                     ) AS foo2
                UNION ALL
                SELECT *
                FROM (
                       SELECT
                          t2.lot_id,
                          t5.date,
                          t0.move_id,
                          po.order_id,
                          t0.write_date                                         AS fecha_cr,
                          (t0.additional_landed_cost / t0.quantity)             AS price_unit,
                          (select rate
                           from res_currency_rate
                           where currency_id = 3
                           order by name desc
                           limit 1) * (t0.additional_landed_cost / t0.quantity) as price_unit_usd,
                          t5.name                                               AS origin,
                          t0.name,
                          CASE WHEN t1.split_method = 'by_quantity'
                            THEN
                              'Por cantidad' :: VARCHAR
                          WHEN t1.split_method = 'by_current_cost_price'
                            THEN
                              'Por costo actual' :: VARCHAR
                          WHEN t1.split_method = 'by_weight'
                            THEN
                              'Por Peso' :: VARCHAR
                          WHEN t1.split_method = 'by_volume'
                            THEN
                              'Por Volumen' :: VARCHAR
                          ELSE
                            'Igual' :: VARCHAR
                          END                                                   AS metodo,
                          'Gastos por chasis' :: VARCHAR                        as valoracion,
                          po.bank_id,
                          po.n_prestamo
                        FROM stock_valuation_adjustment_lines t0
                          INNER JOIN stock_landed_cost_lines t1 ON t1.id = t0.cost_line_id
                          INNER JOIN stock_move_line t2 ON t2.id = t0.move_line_id
                          INNER JOIN stock_production_lot t4 ON t4.id = t2.lot_id
                          INNER JOIN stock_landed_cost t5 ON t5.id = t0.cost_id
                          INNER JOIN (SELECT DISTINCT ON (t0.lot_id)
                                         t0.lot_id,
                                         t1.date :: DATE        AS date,
                                         t1.id                  AS move_id,
                                         t3.order_id            as order_id,
                                         t0.create_date         AS fecha_cr,
                                         t1.price_unit,
                                         t1.origin,
                                         t1.name,
                                         'Inicial' :: VARCHAR   as metodo,
                                         'Costo FOB' :: VARCHAR as valoracion,
                                         t4.bank_id,
                                         t4.n_prestamo
                                       FROM stock_move_line t0
                                         INNER JOIN stock_move t1 ON t1.id = t0.move_id
                                         LEFT JOIN purchase_order_line t3 on t3.id = t1.purchase_line_id
                                         LEFT JOIN purchase_order t4 on t4.id = t3.order_id
                                         WHERE t1.state in ('done')
                                       ORDER BY t0.lot_id, t1.date ASC
                                     ) as po on po.lot_id = t2.lot_id
                        WHERE t5.state IN ('done')
                        ORDER BY t2.lot_id, t5.date
                     ) AS foo3
                ORDER BY 1, 4

            ) as report
        )""")
