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


class PoiReportKardexValuationReal(models.Model):
    _name = 'poi.report.kardex.valuation.real'
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

    # price_unit_date = fields.Float(string='precio Unitario en fecha')

    def _select(self, date_from='', date_to='', warehouse_ids='', product_ids=''):
        sql_kardexvalorado = """
            SELECT
              *,
              (sum(foo.cantidad)
              OVER win) AS total_fecha,
              (sum(foo.cantidad * foo.price_unit + (monto_opcional))
              OVER win) AS monto_en_fecha
            FROM (
                   SELECT
                     t0.date AS date,
                     CASE
                     WHEN t2.id IS NOT NULL
                       THEN
                         t2.id
                     WHEN t10.id IS NOT NULL
                       THEN
                         t10.id
                     WHEN t11.id IS NOT NULL
                       THEN
                         t11.id
                     ELSE
                       t7.id
                     END     AS warehouse_id,
            
                     t1.code AS tipo,
                     CASE
                     WHEN t5.name IS NULL
                       THEN
                         t0.name
                     ELSE
                       t5.name
                     END     AS documento,
                     t0.product_id,
            
                     CASE
                     WHEN t8.usage IN ('internal', 'transit')
                       THEN
                         t6.qty * (-1)
                     ELSE
                       t6.qty
                     END     AS cantidad,
                     t6.lot_id,
                     t0.price_unit AS price_unit,
                     0       AS monto_opcional
                   FROM stock_move t0
                     LEFT JOIN stock_picking_type t1 ON t1.id = t0.picking_type_id
                     LEFT JOIN stock_warehouse t2 ON t2.id = t1.warehouse_id
                     LEFT JOIN stock_picking t5 ON t5.id = t0.picking_id
                     INNER JOIN (SELECT
                                   sm.id             AS move_id,
                                   sml.lot_id,
                                   sml.date,
                                   sum(sml.qty_done) as qty
                                 FROM stock_move sm
                                   INNER JOIN stock_move_line sml ON sml.move_id = sm.id
                                 GROUP BY sm.id, sml.lot_id, sml.date
                                ) t6 ON t6.move_id = t0.id
                     LEFT JOIN stock_warehouse t7 ON t7.lot_stock_id = t0.location_id
                     INNER JOIN stock_location t8 ON t8.id = t0.location_id
                     INNER JOIN stock_location t9 ON t9.id = t0.location_dest_id
                     LEFT JOIN stock_warehouse t10 ON t10.lot_stock_id = t0.location_id
                     LEFT JOIN stock_warehouse t11 ON t11.lot_stock_id = t0.location_dest_id
                   WHERE t0.state = 'done'
                 ) AS foo
            WINDOW win AS (
              PARTITION BY foo.product_id
              ORDER BY foo.date )
        """
        return sql_kardexvalorado

    @api.model_cr
    def init(self, date_from=time.strftime("%Y-%m-%d"), date_to=time.strftime("%Y-%m-%d"), product_id=0, location_id=0):
        sql = """ DROP MATERIALIZED VIEW IF EXISTS poi_report_kardex_valuation_real;
                  CREATE MATERIALIZED VIEW poi_report_kardex_valuation_real AS (
                  (
                      SELECT row_number() over() as id, *
                        FROM ((
                            %s
                        )) as asd
              ))""" % (self._select(date_from, date_to, product_id, location_id))
        self.env.cr.execute(sql)
