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


class PoiReportKardexLot(models.Model):
    _name = 'poi.report.kardex.lot'
    _description = "Reporte Kardex Lote"
    _auto = False

    date = fields.Date(string='Fecha', readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string='Lote', readonly=True)
    picking = fields.Char(string='Albarán')
    origin = fields.Char(string='Doc. Origen')
    name_mov = fields.Char(string='Movimiento')
    origen = fields.Char(string='Origen')
    destino = fields.Char(string='Destino')
    cantidad = fields.Float(string='Cant. Producto')
    precio = fields.Float(string='Precio Unitario', groups="base.group_sale_manager")
    cantidad_en_fecha = fields.Float(string='Stock a la Fecha')
    valor_inventario_fecha = fields.Float(string='Valor Inventario Fecha', groups="base.group_sale_manager")

    def _select(self, date_from='', date_to='', product_id='', location_id='', lot_id=''):
        sql_kardexvalorado = """
            select
                date, product_id,
                picking,
                origin,
                lot_id,
                name_mov, origen, destino, cantidad,
                CASE WHEN valor_anterior != 0 and price_unit != 0
                THEN
                price_unit
                ELSE
                (select s0.cost
                 from product_price_history s0
                 where s0.product_id = product_id
                 and  (s0.datetime - '4 hr'::interval) <= date order by s0.datetime desc limit 1)
                END as precio,

                CASE WHEN valor_anterior != 0 and price_unit != 0
                THEN
                valor_anterior
                ELSE
                total_en_fecha + cantidad
                END as cantidad_en_fecha,

                CASE WHEN valor_anterior != 0 and price_unit != 0
                THEN valor_anterior * price_unit
                ELSE
                (total_en_fecha + cantidad) * (select s0.cost
                 from product_price_history s0
                 where s0.product_id = product_id
                 and  (s0.datetime - '4 hr'::interval) <= date order by s0.datetime desc limit 1)
                END as valor_inventario_fecha
                FROM (
                select *, lag(total_en_fecha) OVER (ORDER BY date DESC) as valor_anterior from (
                    select *, SUM(cantidad)
                          OVER (PARTITION BY product_id
                                  ORDER BY date) - cantidad AS total_en_fecha
                        from (
                            select (t0.date - '4 hr'::interval) as date,
                            t0.product_id,
                            t4.product_tmpl_id,
                            t3.name as picking,
                            t0.origin as origin,
                            t0.name as name_mov,
                            t5.lot_id,
                            t1.complete_name as origen,
                            t2.complete_name as destino,
                            CASE
                            WHEN t0.location_id != """ + str(location_id) + """ and t0.location_dest_id = """ + str(
            location_id) + """
                              --THEN t0.product_uom_qty
                                THEN t5.qty
                            WHEN t0.location_id = """ + str(location_id) + """ and t0.location_dest_id != """ + str(
            location_id) + """
                              --THEN t0.product_uom_qty * (-1)
                                THEN t5.qty * (-1)
                            END AS cantidad,
                            t0.price_unit
                            from stock_move t0
                            inner join stock_location t1 on t1.id = t0.location_id
                            inner join stock_location t2 on t2.id = t0.location_dest_id
                            left join stock_picking t3 on t3.id = t0.picking_id
                            inner join product_product t4 on t4.id = t0.product_id
                            inner join (
                                    SELECT
                                     sm.id       AS move_id,
                                     sml.lot_id,
                                     sml.date,
                                     sum(sml.qty_done) as qty
                                   FROM stock_move sm
                                     INNER JOIN stock_move_line sml ON sml.move_id = sm.id
                                     WHERE sml.lot_id = """ + str(lot_id) + """
                                   GROUP BY sm.id, sml.lot_id, sml.date
                                ) t5 ON t5.move_id = t0.id
                            where t0.product_id=""" + str(product_id) + """
                            and t5.lot_id =""" + str(lot_id) + """
                            and (t0.location_id=""" + str(location_id) + """ or t0.location_dest_id = """ + str(
            location_id) + """)
                            and t0.location_id != t0.location_dest_id
                            and t0.state in ('done')
                            order by date
                        ) as foo
                    ) as foo2
                    order by date
                ) as foo3
        """
        return sql_kardexvalorado

    @api.model_cr
    def init(self, date_from=time.strftime("%Y-%m-%d"), date_to=time.strftime("%Y-%m-%d"), product_id=0, location_id=0,
             lot_id=0):
        sql = """ DROP VIEW if exists poi_report_kardex_lot;
                  CREATE or REPLACE VIEW poi_report_kardex_lot as ((
                      SELECT row_number() over() as id, *
                        FROM ((
                            %s
                        )) as asd
              ))""" % (self._select(date_from, date_to, product_id, location_id, lot_id))
        self.env.cr.execute(sql)
