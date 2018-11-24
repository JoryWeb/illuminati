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

class PoiReportKardexInv(models.Model):
    _name = 'poi.report.kardex.inv'
    _description = "Reporte Kardex Lote"
    _auto = False

    date = fields.Date(string='Fecha', readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    picking = fields.Char(string='Albarán')
    origin = fields.Char(string='Doc. Origen')
    name_mov = fields.Char(string='Movimiento')
    origen = fields.Char(string='Origen')
    destino = fields.Char(string='Destino')
    lote = fields.Char(string='Destino')
    product_uom_qty = fields.Float(string='Cantidad')
    valor = fields.Float(string='Valor')
    cantidad_fecha = fields.Float(string='Stock a la Fecha')
    valor_fecha = fields.Float(string='Valor Inventario Fecha')

    def _select(self, date_from='', date_to='', product_id='', location_id=''):
        sql_kardexvalorado = """
            with data as (
               select
                 sm.id                                  as move_id,
                 sml.date,
                 pt.default_code                        as codigo,
                 pt.name                                as producto,
                 sm.origin,
                 pp.id                                  as product_id,
                 sm.name                                as name_mov,
                 sml.lot_id,
                 spl.name as lote,
                 coalesce(sml.qty_done * (-1), 0) as product_uom_qty,
                 sm.product_uom,
                 pu.name as udm,
                 coalesce(sm.price_unit * (-1), 0)      AS precio,
                 coalesce(sm.price_unit*sml.qty_done * (-1), 0)           as valor,
                 0                                      AS cantidad_en_fecha,
                 0                                      AS total_inventario,
                 0                                      AS valor_inventario_fecha,
                 lo.complete_name                       as origen,
                 ld.complete_name                       as destino,
                 sp.name as picking,
                 CASE
                 WHEN spt.code = 'incoming'
                   THEN 'Proveedores'
                 WHEN spt.code = 'outgoing'
                   THEN 'Clientes'
                 WHEN spt.code = 'internal'
                   THEN 'Interno o Ajuste'
                 ELSE 'Otros'
                 END                                    AS tipo
               from stock_move_line sml
                 inner join stock_move sm on sm.id = sml.move_id
                 inner join product_product pp on pp.id = sm.product_id
                 inner join product_template pt on pp.product_tmpl_id = pt.id
                 inner join stock_picking_type spt on sm.picking_type_id = spt.id
                 inner join stock_location lo on sm.location_id = lo.id
                 inner join stock_location ld on sm.location_dest_id = ld.id
                 inner join stock_picking sp on sp.id = sm.picking_id
                 inner join product_uom pu on pu.id = sm.product_uom
                 left join stock_production_lot spl on spl.id = sml.lot_id
               where sml.state = 'done'
              and sm.date between '""" + date_from + """' and '""" + date_to + """'
                     and sm.product_id = """ + str(product_id) + """ and sm.location_id = """ + str(location_id) + """
               UNION ALL
               select
                 sm.id                      as move_id,
                 sml.date,
                 pt.default_code            as codigo,
                 pt.name                    as producto,
                 sm.origin,
                 pp.id                      as product_id,
                 sm.name                    as name_mov,
                 sml.lot_id,
                 spl.name as lote,
                 sml.qty_done as product_uom_qty,
                 sm.product_uom,
                 pu.name as udm,
                 coalesce(sm.price_unit, 0) as precio,
                 coalesce(sm.price_unit*sml.qty_done, 0)      as valor,
                 0                          AS cantidad_en_fecha,
                 0                          AS total_inventario,
                 0                          AS valor_inventario_fecha,
                 lo.complete_name           as origen,
                 ld.complete_name           as destino,
                 sp.name as picking,
                 CASE
                 WHEN spt.code = 'incoming'
                   THEN 'Proveedores'
                 WHEN spt.code = 'outgoing'
                   THEN 'Clientes'
                 WHEN spt.code = 'internal'
                   THEN 'Interno o Ajuste'
                 ELSE 'Otros'
                 END                        AS tipo
               from stock_move_line sml
                 inner join stock_move sm on sm.id = sml.move_id
                 inner join product_product pp on pp.id = sm.product_id
                 inner join product_template pt on pp.product_tmpl_id = pt.id
                 inner join stock_picking_type spt on sm.picking_type_id = spt.id
                 inner join stock_location lo on sm.location_id = lo.id
                 inner join stock_location ld on sm.location_dest_id = ld.id
                 inner join stock_picking sp on sp.id = sm.picking_id
                 inner join product_uom pu on pu.id = sm.product_uom
                 left join stock_production_lot spl on spl.id = sml.lot_id
               where sml.state = 'done'
               and sm.date between '""" + date_from + """' and '""" + date_to + """'
                  and sm.product_id = """ + str(product_id) + """ and sm.location_dest_id = """ + str(location_id) + """
               order by 4,1
        
        )
        select
          *,
          sum(product_uom_qty) over (order by product_id, date asc rows between unbounded preceding and current row) as cantidad_fecha,
          sum(valor) over (order by product_id, date asc rows between unbounded preceding and current row) as valor_fecha
        from data
        """
        return sql_kardexvalorado

    @api.model_cr
    def init(self, date_from=time.strftime("%Y-%m-%d"), date_to=time.strftime("%Y-%m-%d"), product_id=0, location_id=0):
        sql = """ DROP VIEW IF EXISTS poi_report_kardex_inv;
                  CREATE or REPLACE VIEW poi_report_kardex_inv as ((
                      SELECT row_number() over() as id, *
                        FROM ((
                            %s
                        )) as asd
              ))""" % (self._select(date_from, date_to, product_id, location_id))
        self.env.cr.execute(sql)
