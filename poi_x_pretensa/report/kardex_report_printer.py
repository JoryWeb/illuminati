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
from openerp.osv import osv
from openerp.report import report_sxw

class kardex_report_printer(report_sxw.rml_parse):
    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        obj_move = self.pool.get('account.move.line')
        ctx = self.context.copy()
        #ctx['period_init_id'] = data['form']['period_init_id']
        #ctx['period_end_id'] = data['form']['period_end_id']
        self.product_id = data['form'].get('product_id', False)
        self.location_id = data['form'].get('location_id', False)
        self.lot_id = data['form'].get('lot_id', False)
        #self.asset_ids = data['ids']
        self.date_from = data['form'].get('date_from', False)
        self.date_to = data['form'].get('date_to', False)
        self.total_entrada = 0.0
        self.total_salida = 0.0
        self.diferencia = 0.0
        self.total_monto_entrada = 0.0
        self.total_monto_salida = 0.0
        self.diferencia_monto = 0.0

        self.context.update(ctx)
        #if (data['model'] == 'ir.ui.menu'):
        #    objects = self.pool.get('poi.report.kardex.valorado.dos').browse(self.cr, self.uid, new_ids)
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
            'default_code': self._get_default_code,
            'lote': self._get_lot,
            'get_user': self._get_user,
            'total_entrada': self._get_total_entrada,
            'total_salida': self._get_total_salida,
            'diferencia': self._get_diferencia,
            'total_monto_entrada': self._get_total_monto_entrada,
            'total_monto_salida': self._get_total_monto_salida,
            'diferencia_monto': self._get_diferencia_monto,
        })
        self.context = context

    def _get_location(self):
        return self.location_id[1]
    def _get_product(self):
        return self.product_id[1]

    def _get_default_code(self):
        code = self.pool.get('product.product').browse(self.cr, self.uid, self.product_id[0]).default_code
        return code

    def _get_lot(self):
        return self.lot_id[1]

    def _get_total_entrada(self):
        return self.total_entrada
    def _get_total_salida(self):
        return self.total_salida
    def _get_diferencia(self):
        return self.diferencia

    def _get_total_monto_entrada(self):
        return self.total_monto_entrada
    def _get_total_monto_salida(self):
        return self.total_monto_salida
    def _get_diferencia_monto(self):
        return self.diferencia_monto

    def _get_user(self):
        return self.pool.get('res.users').browse(self.cr, self.uid, self.uid).name

    def lines(self):
        #period_obj = self.pool.get('account.period')
        if self.location_id:
            location_id = self.location_id[0] or ''
        else:
            location_id = 0
        if self.product_id:
            product_id = self.product_id[0] or ''
        else:
            product_id = 0
        if self.lot_id:
            lot_id = self.lot_id[0] or ''
            lot_data = self.pool.get('stock.production.lot').browse(self.cr,self.uid,lot_id,{})
            price_unit = lot_data.product_id.standard_price*lot_data.dimension_id.total_computed
        else:
            lot_id = 0
        date_from = self.date_from or ''
        date_to = self.date_to or ''
        #date_start = period_obj.browse(self.cr, self.uid, self.period_init_id, context=self.context).date_start
        #date_stop = period_obj.browse(self.cr, self.uid, self.period_end_id, context=self.context).date_stop

        sql = """
        select kardex.* from (
          SELECT foo5.*
          FROM (
                 SELECT
                   *,
                   (cantidad_entrada * precio) AS monto_entrada,
                   (cantidad_salida * precio)  AS monto_salida
                 FROM (
                        SELECT
                          pp.name_template AS producto,
                          pp.default_code  AS codigo,
                          spl.name         AS lote,
                          date,
                          --product_id,
                          picking,
                          CASE
                          WHEN picking LIKE '%OUT%'
                            THEN 'VENTA'
                          WHEN picking LIKE ''
                            THEN 'AJUSTE'
                          WHEN picking LIKE '%IN/%'
                            THEN 'DEVOLUCIÓN'
                          WHEN picking LIKE '%-TR%'
                            THEN 'MOV. INTERNO'
                          WHEN picking LIKE 'REC%' or picking LIKE '%-REC%'
                            THEN 'RECUPERADO'
                          ELSE 'SALDO'
                          END              AS tipo,
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
                          END              AS cantidad_entrada,
                          --10
                          CASE WHEN cantidad < 0
                            THEN
                              cantidad * (-1)
                          ELSE
                            0.0
                          END              AS cantidad_salida,
                          --11
                          CASE WHEN valor_anterior != 0 AND price_unit != 0
                              THEN
                                price_unit
                            ELSE
                              (""" + str(price_unit) + """)
                            END              AS precio,
                            CASE WHEN valor_anterior != 0 AND price_unit != 0
                              THEN
                                valor_anterior
                            ELSE
                              total_en_fecha + cantidad
                            END              AS cantidad_en_fecha,
                            CASE WHEN valor_anterior != 0 AND price_unit != 0
                              THEN valor_anterior * price_unit
                            ELSE
                              (total_en_fecha + cantidad) * (""" + str(price_unit) + """)
                            END              AS valor_inventario_fecha --14
                        FROM (
                               SELECT
                                 *,
                                 lag(total_en_fecha)
                                 OVER (
                                   ORDER BY date DESC) AS valor_anterior
                               FROM (
                                      SELECT
                                        *,
                                        SUM(cantidad)
                                        OVER (PARTITION BY product_id
                                          ORDER BY date) - cantidad AS total_en_fecha
                                      FROM (
                                             SELECT
                                               (t0.date - '4 hr' :: INTERVAL) AS date,
                                               t0.product_id,
                                               t4.product_tmpl_id,
                                               t3.name                        AS picking,
                                               t0.origin                      AS origin,
                                               t0.name                        AS name_mov,
                                               t5.lot_id,
                                               t1.complete_name               AS origen,
                                               t2.complete_name               AS destino,
                                               CASE
                                               WHEN t0.location_id != """ + str(location_id) + """ and t0.location_dest_id = """ + str(location_id) + """
                                           THEN t5.qty
                                         WHEN t0.location_id = """ + str(location_id) + """ and t0.location_dest_id != """ + str(location_id) + """
                                                 THEN t5.qty * (-1)
                                               END                            AS cantidad,
                                               """ + str(price_unit) + """  AS price_unit
                                             FROM stock_move t0
                                               INNER JOIN stock_location t1 ON t1.id = t0.location_id
                                               INNER JOIN stock_location t2 ON t2.id = t0.location_dest_id
                                               LEFT JOIN stock_picking t3 ON t3.id = t0.picking_id
                                               INNER JOIN product_product t4 ON t4.id = t0.product_id
                                               INNER JOIN (SELECT
                                                             sm.id    AS move_id,
                                                             sl.id    AS lot_id,
                                                             sum(CASE WHEN sq.qty > 0
                                                               THEN
                                                                 sq.qty
                                                                 ELSE
                                                                   0
                                                                 END) AS qty
                                                           FROM stock_move sm
                                                             INNER JOIN stock_quant_move_rel smr ON smr.move_id = sm.id
                                                             INNER JOIN stock_quant sq ON sq.id = smr.quant_id
                                                             INNER JOIN stock_production_lot sl ON sl.id = sq.lot_id
                                                           WHERE sl.id = """ + str(lot_id) + """
                                                           GROUP BY sm.id, sl.id
                                                          ) t5 ON t5.move_id = t0.id
                                             where t0.product_id=""" + str(product_id) + """
                                             and t5.lot_id =""" + str(lot_id) + """
                                             and (t0.location_id=""" + str(location_id) + """ or t0.location_dest_id = """ + str(location_id) + """)
                                                   AND t0.location_id != t0.location_dest_id
                                                   AND t0.state IN ('done')
                                             ORDER BY date
                                           ) AS foo
                                    ) AS foo2
                               ORDER BY date
                             ) AS foo3
                          INNER JOIN product_product pp ON pp.id = foo3.product_id
                          INNER JOIN stock_production_lot spl ON spl.id = foo3.lot_id
                        ORDER BY foo3.date
                      ) AS foo
                 WHERE foo.date >= '""" + date_from + """' AND foo.date <= '""" + date_to + """'
               ) AS foo5

          UNION ALL
          SELECT foo3.* from (
          SELECT foo2.*
          FROM (
                 SELECT
                   *,
                   (cantidad_entrada * precio) AS monto_entrada,
                   (cantidad_salida * precio)  AS monto_salida
                 FROM (
                        SELECT
                          pp.name_template                    AS producto,
                          pp.default_code                     AS codigo,
                          spl.name                            AS lote,
                          date,
                          --product_id,
                          --product_id,
                          picking,
                          CASE
                          WHEN picking LIKE 'OUT%'
                            THEN 'VENTA'
                          WHEN picking LIKE ''
                            THEN 'AJUSTE'
                          WHEN picking LIKE 'IN%' OR picking LIKE 'REC%'
                            THEN 'RECUPERADO'
                          ELSE 'SALDO'
                          END                                 AS tipo,
                          origin,
                          --lot_id,
                          ('SALDO Hasta:' || date) :: VARCHAR AS name_mov,
                          origen,
                          destino,
                          cantidad,
                          CASE WHEN cantidad > 0
                            THEN
                              cantidad
                          ELSE
                            0.0
                          END                                 AS cantidad_entrada,
                          --10
                          CASE WHEN cantidad < 0
                            THEN
                              cantidad * (-1)
                          ELSE
                            0.0
                          END                                 AS cantidad_salida,
                          --11
                          CASE WHEN valor_anterior != 0 AND price_unit != 0
                              THEN
                                price_unit
                            ELSE
                              (""" + str(price_unit) + """)
                            END              AS precio,
                            CASE WHEN valor_anterior != 0 AND price_unit != 0
                              THEN
                                valor_anterior
                            ELSE
                              total_en_fecha + cantidad
                            END              AS cantidad_en_fecha,
                            CASE WHEN valor_anterior != 0 AND price_unit != 0
                              THEN valor_anterior * price_unit
                            ELSE
                              (total_en_fecha + cantidad) * (""" + str(price_unit) + """)
                            END              AS valor_inventario_fecha --14
                        FROM (
                               SELECT
                                 *,
                                 lag(total_en_fecha)
                                 OVER (
                                   ORDER BY date DESC) AS valor_anterior
                               FROM (
                                      SELECT
                                        *,
                                        SUM(cantidad)
                                        OVER (PARTITION BY product_id
                                          ORDER BY date) - cantidad AS total_en_fecha
                                      FROM (
                                             SELECT
                                               (t0.date - '4 hr' :: INTERVAL) AS date,
                                               t0.product_id,
                                               t4.product_tmpl_id,
                                               t3.name                        AS picking,
                                               t0.origin                      AS origin,
                                               t0.name                        AS name_mov,
                                               t5.lot_id,
                                               t1.complete_name               AS origen,
                                               t2.complete_name               AS destino,
                                               CASE
                                               WHEN t0.location_id != """ + str(
            location_id) + """ and t0.location_dest_id = """ + str(location_id) + """
                                           THEN t5.qty
                                         WHEN t0.location_id = """ + str(
            location_id) + """ and t0.location_dest_id != """ + str(location_id) + """
                                                 THEN t5.qty * (-1)
                                               END                            AS cantidad,
                                               """ + str(price_unit) + """  AS price_unit
                                             FROM stock_move t0
                                               INNER JOIN stock_location t1 ON t1.id = t0.location_id
                                               INNER JOIN stock_location t2 ON t2.id = t0.location_dest_id
                                               LEFT JOIN stock_picking t3 ON t3.id = t0.picking_id
                                               INNER JOIN product_product t4 ON t4.id = t0.product_id
                                               INNER JOIN (SELECT
                                                             sm.id    AS move_id,
                                                             sl.id    AS lot_id,
                                                             sum(CASE WHEN sq.qty > 0
                                                               THEN
                                                                 sq.qty
                                                                 ELSE
                                                                   0
                                                                 END) AS qty
                                                           FROM stock_move sm
                                                             INNER JOIN stock_quant_move_rel smr ON smr.move_id = sm.id
                                                             INNER JOIN stock_quant sq ON sq.id = smr.quant_id
                                                             INNER JOIN stock_production_lot sl ON sl.id = sq.lot_id
                                                           WHERE sl.id = """ + str(lot_id) + """
                                                           GROUP BY sm.id, sl.id
                                                          ) t5 ON t5.move_id = t0.id
                                             where t0.product_id=""" + str(product_id) + """
                                             and t5.lot_id =""" + str(lot_id) + """
                                             and (t0.location_id=""" + str(
            location_id) + """ or t0.location_dest_id = """ + str(location_id) + """)
                                                   AND t0.location_id != t0.location_dest_id
                                                   AND t0.state IN ('done')
                                             ORDER BY date
                                           ) AS foo
                                    ) AS foo2
                               ORDER BY date
                             ) AS foo3
                          INNER JOIN product_product pp ON pp.id = foo3.product_id
                          INNER JOIN stock_production_lot spl ON spl.id = foo3.lot_id
                      ) AS foor
                 ORDER BY foor.date DESC
               ) AS foo2
               WHERE foo2.date <= '""" + date_from + """'
               LIMIT 1
               ) as foo3
        ) as kardex order by date
        """

        sql_totales = """SELECT foo5.*
          FROM (
                 SELECT
                   *,
                   (cantidad_entrada * precio) AS monto_entrada,
                   (cantidad_salida * precio)  AS monto_salida
                 FROM (
                        SELECT
                          pp.name_template AS producto,
                          pp.default_code  AS codigo,
                          spl.name         AS lote,
                          date,
                          --product_id,
                          picking,
                          CASE
                          WHEN picking LIKE '%OUT%'
                            THEN 'VENTA'
                          WHEN picking LIKE ''
                            THEN 'AJUSTE'
                          WHEN picking LIKE '%IN/%'
                            THEN 'DEVOLUCIÓN'
                          WHEN picking LIKE '%-TR%'
                            THEN 'MOV. INTERNO'
                          WHEN picking LIKE 'REC%' or picking LIKE '%-REC%'
                            THEN 'RECUPERADO'
                          ELSE 'SALDO'
                          END              AS tipo,
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
                          END              AS cantidad_entrada,
                          --10
                          CASE WHEN cantidad < 0
                            THEN
                              cantidad * (-1)
                          ELSE
                            0.0
                          END              AS cantidad_salida,
                          --11
                          CASE WHEN valor_anterior != 0 AND price_unit != 0
                              THEN
                                price_unit
                            ELSE
                              (""" + str(price_unit) + """)
                            END              AS precio,
                            CASE WHEN valor_anterior != 0 AND price_unit != 0
                              THEN
                                valor_anterior
                            ELSE
                              total_en_fecha + cantidad
                            END              AS cantidad_en_fecha,
                            CASE WHEN valor_anterior != 0 AND price_unit != 0
                              THEN valor_anterior * price_unit
                            ELSE
                              (total_en_fecha + cantidad) * (""" + str(price_unit) + """)
                            END              AS valor_inventario_fecha --14
                        FROM (
                               SELECT
                                 *,
                                 lag(total_en_fecha)
                                 OVER (
                                   ORDER BY date DESC) AS valor_anterior
                               FROM (
                                      SELECT
                                        *,
                                        SUM(cantidad)
                                        OVER (PARTITION BY product_id
                                          ORDER BY date) - cantidad AS total_en_fecha
                                      FROM (
                                             SELECT
                                               (t0.date - '4 hr' :: INTERVAL) AS date,
                                               t0.product_id,
                                               t4.product_tmpl_id,
                                               t3.name                        AS picking,
                                               t0.origin                      AS origin,
                                               t0.name                        AS name_mov,
                                               t5.lot_id,
                                               t1.complete_name               AS origen,
                                               t2.complete_name               AS destino,
                                               CASE
                                               WHEN t0.location_id != """ + str(location_id) + """ and t0.location_dest_id = """ + str(location_id) + """
                                           THEN t5.qty
                                         WHEN t0.location_id = """ + str(location_id) + """ and t0.location_dest_id != """ + str(location_id) + """
                                                 THEN t5.qty * (-1)
                                               END                            AS cantidad,
                                               """ + str(price_unit) + """  AS price_unit
                                             FROM stock_move t0
                                               INNER JOIN stock_location t1 ON t1.id = t0.location_id
                                               INNER JOIN stock_location t2 ON t2.id = t0.location_dest_id
                                               LEFT JOIN stock_picking t3 ON t3.id = t0.picking_id
                                               INNER JOIN product_product t4 ON t4.id = t0.product_id
                                               INNER JOIN (SELECT
                                                             sm.id    AS move_id,
                                                             sl.id    AS lot_id,
                                                             sum(CASE WHEN sq.qty > 0
                                                               THEN
                                                                 sq.qty
                                                                 ELSE
                                                                   0
                                                                 END) AS qty
                                                           FROM stock_move sm
                                                             INNER JOIN stock_quant_move_rel smr ON smr.move_id = sm.id
                                                             INNER JOIN stock_quant sq ON sq.id = smr.quant_id
                                                             INNER JOIN stock_production_lot sl ON sl.id = sq.lot_id
                                                           WHERE sl.id = """ + str(lot_id) + """
                                                           GROUP BY sm.id, sl.id
                                                          ) t5 ON t5.move_id = t0.id
                                             where t0.product_id=""" + str(product_id) + """
                                             and t5.lot_id =""" + str(lot_id) + """
                                             and (t0.location_id=""" + str(location_id) + """ or t0.location_dest_id = """ + str(location_id) + """)
                                                   AND t0.location_id != t0.location_dest_id
                                                   AND t0.state IN ('done')
                                             ORDER BY date
                                           ) AS foo
                                    ) AS foo2
                               ORDER BY date
                             ) AS foo3
                          INNER JOIN product_product pp ON pp.id = foo3.product_id
                          INNER JOIN stock_production_lot spl ON spl.id = foo3.lot_id
                        ORDER BY foo3.date
                      ) AS foo
                      WHERE foo.date <= '""" + date_to + """'
               ) AS foo5"""
        #self.cr.execute(sql, (asset.id, str(date_from), str(date_to),))
        self.cr.execute(sql)
        res_lines = self.cr.dictfetchall()
        self.cr.execute(sql_totales)
        res_total = self.cr.fetchall()
        for totales in res_total:
            self.total_entrada = self.total_entrada + float(totales[11])
            self.total_salida = self.total_salida + float(totales[12])
            self.diferencia = float(totales[14])
            self.total_monto_entrada = self.total_monto_entrada + float(totales[16])
            self.total_monto_salida = self.total_monto_salida + float(totales[17])
            self.diferencia_monto = float(totales[15])
        #self.diferencia = self.total_entrada - self.total_salida
        res = res_lines
        return res

class report_kardex_printer(osv.AbstractModel):
    _name = 'report.poi_x_pretensa.report_kardex_pre'
    _inherit = 'report.abstract_report'
    _template = 'poi_x_pretensa.report_kardex_pre'
    _wrapped_report_class = kardex_report_printer


class report_kardex_valorado_printer(osv.AbstractModel):
    _name = 'report.poi_x_pretensa.report_kardex_valorado_pre'
    _inherit = 'report.abstract_report'
    _template = 'poi_x_pretensa.report_kardex_valorado_pre'
    _wrapped_report_class = kardex_report_printer

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
