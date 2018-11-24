##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Poiesis Consulting
#    autor: Grover Menacho
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

from odoo import tools
from odoo import api, fields, models

import time


class PoiReportKardexValuation(models.Model):
    _name = 'poi.report.kardex.valuation'
    _description = "Reporte Kardex Valorado"
    _auto = False

    date = fields.Datetime(string="Fecha", readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string=u"Almacén", readonly=True)
    documento = fields.Char(string=u"Documento", readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    cantidad = fields.Float(string='Cant. Producto')
    lot_id = fields.Many2one('stock.production.lot', string='Lote')
    price_unit = fields.Char(string='Precio Unitario')
    total_fecha = fields.Char(string='Total Fecha')
    monto_en_fecha = fields.Char(string='Monto en Fecha')
    price_unit_date = fields.Char(string='precio Unitario en fecha')

    def _select(self, date_from='', date_to='', warehouse_ids='', product_ids=''):
        sql_kardexvalorado = """
            SELECT
                  *,
                  CASE WHEN foo2.total_fecha != 0
                    THEN
                      (foo2.monto_en_fecha / foo2.total_fecha)
                  ELSE
                    0
                  END AS price_unit_date
                FROM (
                       SELECT
                         *,
                         (sum(foo.cantidad)
                         OVER w) AS total_fecha,
                         (sum(foo.cantidad * foo.price_unit + (monto_opcional))
                         OVER w) AS monto_en_fecha
                       FROM (
                              SELECT
                                t0.date AS date,
                                t2.id   AS warehouse_id,
                                t1.code AS tipo,
                                t5.name AS documento,
                                t0.product_id,
                                CASE
                                WHEN t1.code = 'incoming'
                                  THEN
                                    t6.qty
                                WHEN t1.code = 'outgoing'
                                  THEN
                                    t6.qty * (-1)
                                END     AS cantidad,
                                t6.lot_id,
                                t0.price_unit,
                                0       as monto_opcional
                              FROM stock_move t0
                                INNER JOIN stock_picking_type t1 ON t1.id = t0.picking_type_id
                                INNER JOIN stock_warehouse t2 ON t2.id = t1.warehouse_id
                                INNER JOIN stock_picking t5 ON t5.id = t0.picking_id
                                INNER JOIN (SELECT
                                               sm.id             AS move_id,
                                               sml.lot_id,
                                               sml.date,
                                               sum(sml.qty_done) as qty
                                             FROM stock_move sm
                                               INNER JOIN stock_move_line sml ON sml.move_id = sm.id
                                             GROUP BY sm.id, sml.lot_id, sml.date
                                           ) t6 ON t6.move_id = t0.id
                              WHERE t0.state = 'done'
                
                              UNION ALL
                
                              (SELECT
                                 CASE WHEN t6.qty = 0
                                   THEN
                                     t0.date + interval '2s'
                                 ELSE
                                   t0.date
                                 END                        AS date,
                                 t2.id                      AS warehouse_id,
                                 'production'               AS tipo,
                                 t0.origin                  AS documento,
                                 t0.product_id,
                                 t0.product_qty * (-1)      AS cantidad,
                                 t6.lot_id         AS lot_id,
                                 coalesce(t0.price_unit, 1) AS price_unit,
                                 0                          AS monto_opcional
                               FROM stock_move t0
                                 INNER JOIN stock_warehouse t2 ON t2.lot_stock_id = t0.location_id
                                 INNER JOIN (SELECT
                                               sm.id             AS move_id,
                                               sml.lot_id,
                                               sml.date,
                                               sum(sml.qty_done) as qty
                                             FROM stock_move sm
                                               INNER JOIN stock_move_line sml ON sml.move_id = sm.id
                                             GROUP BY sm.id, sml.lot_id, sml.date
                                            ) t6 ON t6.move_id = t0.id
                                 INNER JOIN stock_production_lot t3 ON t3.id = t6.lot_id
                
                               WHERE t0.state = 'done' AND t0.picking_id IS NULL
                               ORDER BY t3.create_date desc)
                
                              UNION ALL
                
                              (SELECT
                                 CASE WHEN t6.qty = 0
                                   THEN
                                     t0.date + interval '2s'
                                 ELSE
                                   t0.date
                                 END                        AS date,
                                 t2.id                      AS warehouse_id,
                                 'production'               AS tipo,
                                 t0.origin                  AS documento,
                                 t0.product_id,
                                 t0.product_qty             AS cantidad,
                                 t6.lot_id         AS lot_id,
                                 coalesce(t0.price_unit, 1) AS price_unit,
                                 0                          AS monto_opcional
                               FROM stock_move t0
                                 INNER JOIN stock_warehouse t2 ON t2.lot_stock_id = t0.location_dest_id
                                 INNER JOIN (SELECT
                                               sm.id             AS move_id,
                                               sml.lot_id,
                                               sml.date,
                                               sum(sml.qty_done) as qty
                                             FROM stock_move sm
                                               INNER JOIN stock_move_line sml ON sml.move_id = sm.id
                                             GROUP BY sm.id, sml.lot_id, sml.date
                                            ) t6 ON t6.move_id = t0.id
                                 INNER JOIN stock_production_lot t3 ON t3.id = t6.lot_id
                               WHERE t0.state = 'done' AND t0.picking_id IS NULL
                               ORDER BY t3.create_date desc)
                
                              /*UNION ALL
                
                              SELECT
                                t0.date_update_price                 AS date,
                                t3.id                                AS id_almacen,
                                t2.code                              AS tipo,
                                t6.name                              AS documento,
                                t0.product_id,
                                0                                    AS cantidad,
                                0                                    AS lot_id,
                                (t0.expense_amount / t0.product_qty) AS price_unit,
                                t0.expense_amount                    as monto_opcional
                              FROM poi_purchase_imports_line t0
                                INNER JOIN stock_move t1 ON t1.id = t0.move_id
                                INNER JOIN stock_picking_type t2 ON t2.id = t1.picking_type_id
                                INNER JOIN stock_warehouse t3 ON t3.id = t2.warehouse_id
                                INNER JOIN stock_picking t5 ON t5.id = t0.picking_id
                                INNER JOIN poi_purchase_imports t6 ON t6.id = t0.distribution
                              WHERE t6.state = 'done'*/
                            ) AS foo
                       WINDOW w AS (
                         PARTITION BY foo.product_id
                         ORDER BY foo.date ASC )
                     ) AS foo2
                ORDER BY foo2.product_id, foo2.date, foo2.lot_id
        """
        return sql_kardexvalorado

    @api.model_cr
    def init(self, date_from=time.strftime("%Y-%m-%d"), date_to=time.strftime("%Y-%m-%d"), product_id=0, location_id=0):
        sql = """DROP MATERIALIZED VIEW IF EXISTS poi_report_kardex_valuation;
                  CREATE MATERIALIZED VIEW poi_report_kardex_valuation AS (
                  (
                      SELECT row_number() over() as id, *
                        FROM ((
                            %s
                        )) as asd
              ))""" % (self._select(date_from, date_to, product_id, location_id))
        self.env.cr.execute(sql)
