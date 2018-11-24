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


class ReservasTren(models.Model):
    _name = 'reservas.tren'
    _description = "Reporte reserva de tren"
    _auto = False

    picking_id = fields.Many2one("stock.picking", string=u'Albarán', readonly=True)
    ubicacion_origen = fields.Char(string=u'Ubicación Origen', readonly=True)
    name = fields.Char(string=u'Nombre operacion', readonly=True)
    total = fields.Float(string=u'Cant. Prod. Despachado', readonly=True)

    def _select(self, picking_id=''):
        sql = """
            select
              sp.id as picking_id,
              l.complete_name as ubicacion_origen,
              sp.name,
              sm.total
            from stock_picking sp
            inner join (select picking_id, sum(product_uom_qty) total from stock_move
            group by picking_id
            order by picking_id) sm on sm.picking_id = sp.id
              inner join stock_location l on sp.location_id = l.id
              where sp.id = """ + str(picking_id) + """
            order by sp.id
        """
        return sql

    @api.model_cr
    def init(self, picking_id=0):
        sql = """ DROP VIEW IF EXISTS reservas_tren;
                  CREATE or REPLACE VIEW reservas_tren as ((
                      SELECT row_number() over() as id, *
                        FROM ((
                            %s
                        )) as asd
              ))""" % (self._select(picking_id))
        self.env.cr.execute(sql)
