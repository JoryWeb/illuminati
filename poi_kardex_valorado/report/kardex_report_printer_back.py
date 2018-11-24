##############################################################################
#
# Copyright (c) 2005-2006 CamptoCamp
# Copyright (c) 2006-2010 OpenERP S.A
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
##############################################################################

import time
from odoo.osv import osv
from odoo.report import report_sxw


class kardex_report_printer(report_sxw.rml_parse):
    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        ctx = self.context.copy()
        self.product_id = data['form'].get('product_id', False)
        self.location_id = data['form'].get('location_id', False)
        self.date_from = data['form'].get('date_from', False)
        self.date_to = data['form'].get('date_to', False)
        self.total_entrada = 0.0
        self.total_salida = 0.0
        self.diferencia = 0.0
        self.total_monto_entrada = 0.0
        self.total_monto_salida = 0.0
        self.diferencia_monto = 0.0
        self.monto = 0.0
        self.context.update(ctx)
        return super(kardex_report_printer, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(kardex_report_printer, self).__init__(cr, uid, name, context=context)
        self.tot_currency = 0.0
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'location': self._get_location,
            'producto': self._get_product,
            'lote': self._get_lot,
            'get_user': self._get_user,
            'total_entrada': self._get_total_entrada,
            'total_salida': self._get_total_salida,
            'diferencia': self._get_diferencia,
            'total_monto': self._get_monto,
        })
        self.context = context

    def _get_location(self):
        return self.location_id[1]

    def _get_product(self):
        return self.product_id[1]

    def _get_lot(self):
        return self.lot_id[1]

    def _get_total_entrada(self):
        return self.total_entrada

    def _get_total_salida(self):
        return self.total_salida

    def _get_diferencia(self):
        return self.diferencia

    def _get_monto(self):
        return self.monto

    def _get_user(self):
        return self.pool.get('res.users').browse(self.cr, self.uid, self.uid).name

    def lines(self):
        # period_obj = self.pool.get('account.period')
        if self.location_id:
            location_id = self.location_id[0] or ''
        else:
            location_id = 0
        if self.product_id:
            product_id = self.product_id[0] or ''
        else:
            product_id = 0

        date_from = self.date_from or ''
        date_to = self.date_to or ''
        # date_start = period_obj.browse(self.cr, self.uid, self.period_init_id, context=self.context).date_start
        # date_stop = period_obj.browse(self.cr, self.uid, self.period_end_id, context=self.context).date_stop

        sql = """
        select
          pp.name_template                           as producto,
          pp.default_code                            as codigo,
          date,
          --product_id,
          picking,
          CASE
          WHEN tipo_picking = 'incoming'
            THEN 'Proveedores'
          WHEN tipo_picking = 'outgoing'
            THEN 'Clientes'
          WHEN tipo_picking = 'internal'
            THEN 'Interno o Ajuste'
          ELSE 'Otros'
          END                                        AS tipo,
          lote,
          origin,
          --lot_id,
          name_mov,
          origen,
          destino,
          cantidad,
          CASE WHEN cantidad > 0
            THEN
              cantidad
          ELSE
            0.0
          END                                        AS cantidad_entrada,
          --10
          CASE WHEN cantidad < 0
            THEN
              cantidad * (-1)
          ELSE
            0.0
          END                                        AS cantidad_salida,
          price_unit                                 AS precio,
          (total_en_fecha + cantidad)                AS cantidad_en_fecha,
          (cantidad * price_unit)                    AS total_inventario,
          (total_en_fecha_valor + costo_total) AS valor_inventario_fecha
        FROM (
               select
                 *,
                 lag(total_en_fecha)
                 OVER (
                   ORDER BY move_id, date, in_date) as valor_anterior,
                 lag(total_en_fecha_valor)
                 OVER (
                   ORDER BY move_id, date, in_date) as valor_anterior_valor
               from (
                      select
                        *,
                        SUM(cantidad)
                        OVER (
                          PARTITION BY product_id
                          ORDER BY move_id, date, in_date) - cantidad AS total_en_fecha,
                        SUM(costo_total)
                        OVER (
                          PARTITION BY product_id
                          ORDER BY move_id, date, in_date) - (costo_total) AS total_en_fecha_valor
                      from (
                             select
                               (t0.date - '4 hr' :: interval) as date,
                               t5.in_date,
                               t0.id                          as move_id,
                               t0.product_id,
                               t4.product_tmpl_id,
                               spt.code                       as tipo_picking,
                               coalesce(spl.name, '')         as lote,
                               coalesce(t3.name, '')          as picking,
                               coalesce(t0.origin, '')        as origin,
                               t0.name                        as name_mov,
                               t1.complete_name               as origen,
                               t2.complete_name               as destino,
                               CASE
                               WHEN t0.location_id != """ + str(location_id) + """ and t0.location_dest_id = """ + str(location_id) + """
                                 THEN t5.qty
                               WHEN t0.location_id = """ + str(location_id) + """ and t0.location_dest_id != """ + str(location_id) + """
                                 THEN t5.qty * (-1)
                               END                            AS cantidad,
                               CASE
                               WHEN t0.location_id != """ + str(location_id) + """ and t0.location_dest_id = """ + str(location_id) + """
                                 THEN t5.qty * t0.price_unit
                               WHEN t0.location_id = """ + str(location_id) + """ and t0.location_dest_id != """ + str(location_id) + """
                                 THEN t5.qty * t0.price_unit * (-1)
                               END                            AS costo_total,
                               t0.price_unit
                             from stock_move t0
                               inner join stock_location t1 on t1.id = t0.location_id
                               inner join stock_location t2 on t2.id = t0.location_dest_id
                               left join stock_picking t3 on t3.id = t0.picking_id
                               inner join product_product t4 on t4.id = t0.product_id
                               inner join (SELECT
                                             sm.id       AS move_id,
                                             sq.lot_id,
                                             sq.in_date,
                                             sum(sq.qty) as qty
                                           FROM stock_move sm
                                             INNER JOIN stock_quant_move_rel smr ON smr.move_id = sm.id
                                             INNER JOIN stock_quant sq ON sq.id = smr.quant_id
                                           GROUP BY sm.id, sq.lot_id, sq.in_date
                                          ) t5 ON t5.move_id = t0.id
                               LEFT JOIN stock_production_lot spl on spl.id = t5.lot_id
                               LEFT JOIN stock_picking_type spt on spt.id = t0.picking_type_id
                             where t0.product_id=""" + str(product_id) + """
                                    and (t0.location_id=""" + str(location_id) + """ or t0.location_dest_id = """ + str(location_id) + """)
                                   and t0.location_id != t0.location_dest_id
                                   and t0.state in ('done')
                                   and (t0.date - '4 hr'::interval)::DATE >= %s and (t0.date - '4 hr'::interval)::DATE <= %s
                             order by t0.id, t0.date
                           ) as foo
                    ) as foo2
             ) as foo3
          inner join product_product pp on pp.id = foo3.product_id
        order by foo3.move_id, foo3.date, foo3.in_date
        """
        # self.cr.execute(sql, (asset.id, str(date_from), str(date_to),))
        self.cr.execute(sql, (str(date_from), str(date_to),))
        res_lines = self.cr.dictfetchall()
        self.cr.execute(sql, (str(date_from), str(date_to),))
        res_total = self.cr.fetchall()
        for totales in res_total:
            self.total_entrada = self.total_entrada + float(totales[11])
            self.total_salida = self.total_salida + float(totales[12])
            self.monto = self.monto + float(totales[15])
        self.diferencia = self.total_entrada - self.total_salida
        res = res_lines
        return res


class report_kardex_printer(osv.AbstractModel):
    _name = 'report.poi_kardex_valorado.report_kardex'
    _inherit = 'report.abstract_report'
    _template = 'poi_kardex_valorado.report_kardex'
    _wrapped_report_class = kardex_report_printer


class report_kardex_valorado_printer(osv.AbstractModel):
    _name = 'report.poi_kardex_valorado.report_kardex_valorado'
    _inherit = 'report.abstract_report'
    _template = 'poi_kardex_valorado.report_kardex_valorado'
    _wrapped_report_class = kardex_report_printer
