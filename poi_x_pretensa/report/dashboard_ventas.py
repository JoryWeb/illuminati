##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting
#    autor: Nicolas Bustillos
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


from openerp.osv import fields, osv
from openerp import tools
import openerp.addons.decimal_precision as dp
import unicodedata

from lxml import etree


def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

class pret_sales_report(osv.osv):
    _name = "pret.sales.report"
    _description = "Informe Ventas"
    _auto = False
    _columns = {
        'partner_id':fields.many2one('res.partner', 'Cliente', readonly=True),
        'date_order': fields.date('Fecha', readonly=True),
        'name': fields.char('Pedido de ventas', size=64, readonly=True),
        'shop_id': fields.many2one('stock.warehouse', 'Sucursal', readonly=True),
        'date_day': fields.char(u'Día', size=10, readonly=True),
        'date_week': fields.char(u'Semana', size=8, readonly=True),
        'date_month': fields.char(u'Mes', size=18, readonly=True),
        'estado': fields.selection([('vpe','VENDIDO X ENTREGAR'),('ve','VENDIDO ENTREGADO'),('pendiente','PENDIENTE'),('perdida','PERDIDA')], string="Estado"),
        'user_id': fields.many2one('res.users', 'Vendedor', readonly=True),
        'amount_total': fields.float('Precio de venta', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'pricelist_total': fields.float('Precio de lista', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'difference': fields.float('Diferencia', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_40': fields.float('Viguetas Pretensadas(m)', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_41': fields.float('Losas Huecas Pretensadas(m)', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_44': fields.float('Plastobloq(m3)', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_45': fields.float('Tiras', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_46': fields.float('Casetones', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_50': fields.float('Techos', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_47': fields.float(u'Tabiquería(pz)', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_1054': fields.float('Complementos(m3)', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_1056': fields.float('Cordones Pretensados(m)', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'field_1055': fields.float('Muros Pretensados(m)', digits_compute=dp.get_precision('Sale Price'),
                                   readonly=True),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='search', context=None, toolbar=False, submenu=False):
        if view_type == 'search' and 'params' in context:
            cr.execute("REFRESH MATERIALIZED VIEW pret_sales_report;")
        res = super(pret_sales_report, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
        return res

    def init(self, cr):
        #tools.sql.drop_view_if_exists(cr, 'pret_sales_report')
        query_to_exe = """DROP MATERIALIZED VIEW IF EXISTS pret_sales_report;
                    CREATE MATERIALIZED VIEW pret_sales_report as (
                    select row_number() over() as id, foo.* from (
                      SELECT
                        t0.partner_id,
                        t2.date_done as date_order,
                        t0.name,
                        t0.warehouse_id                                                           AS shop_id,
                        to_char(coalesce(t2.date_done,t2.date),
                                'DD/MM/YYYY')                                                     AS date_day,
                        cast(extract(YEAR FROM coalesce(t2.date_done,t2.date)) AS CHAR(4)) || '/' || cast(extract(WEEK FROM coalesce(t2.date_done,t2.date)) AS
                                                                                         CHAR(3)) AS date_week,
                        to_char(coalesce(t2.date_done,t2.date),
                                'YYYY-MM')                                                        AS date_month,
                        CASE
                         WHEN t0.state IN ('draft', 'send')
                           THEN 'pendiente'
                         WHEN
                           t0.state IN ('sale', 'confirmed', 'assigned') and t2.state IN ('waiting', 'confirmed', 'partially_available','assigned')
                           THEN 'vpe'
                         WHEN t0.state IN ('done', 'sale') and t2.state IN ('done')
                           THEN 've'

                         WHEN t0.state IN ('cancel') or t2.state IN ('cancel')
                           THEN 'perdida'
                         ELSE
                           'vpe'
                         END AS estado,
                        t0.user_id                                                                AS user_id,
                        t0.id                                                                     AS order_id,
                        ddd.*
                      FROM sale_order t0
                        INNER JOIN stock_picking t2 ON t2.group_id = t0.procurement_group_id
                        INNER JOIN (SELECT
                                      picking_id,
                                      sum(precio_venta) AS amount_total,
                                      sum(precio_lista) AS pricelist_total,
                                      sum(diferencia)   AS difference,
                                      sum(field_40)     AS field_40,
                                      sum(field_41)     AS field_41,
                                      sum(field_44)     AS field_44,
                                      sum(field_45)     AS field_45,
                                      sum(field_46)     AS field_46,
                                      sum(field_50)     AS field_50,
                                      sum(field_47)     AS field_47,
                                      sum(field_1054)   AS field_1054,
                                      sum(field_1056)   AS field_1056,
                                      sum(field_1055)   AS field_1055
                                    FROM (
                                           SELECT
                                             t0.picking_id,
                                             t3.order_id,
                                             t0.product_id,
                                             t3.product_id,
                                             t3.price_unit,
                                             t0.price_unit                                       AS price_move,
                                             t3.discount,
                                             t0.product_qty,
                                             CASE WHEN t5.categ_id = 40
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_40,
                                             CASE WHEN t5.categ_id = 41
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_41,
                                             CASE WHEN t5.categ_id = 44
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_44,
                                             CASE WHEN t5.categ_id = 45
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_45,
                                             CASE WHEN t5.categ_id = 46
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_46,
                                             CASE WHEN t5.categ_id = 50
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_50,
                                             CASE WHEN t5.categ_id = 47
                                               THEN
                                                 t0.product_uom_qty
                                             ELSE 0 END                                          AS field_47,
                                             CASE WHEN t5.categ_id = 1054
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_1054,
                                             CASE WHEN t5.categ_id = 1056
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_1056,
                                             CASE WHEN t5.categ_id = 1055
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_1055,
                                             CASE WHEN t3.product_uom_qty > 0 THEN
                                             (t3.price_total / COALESCE(t3.product_uom_qty,0.1)) *
                                             t0.product_qty
                                            ELSE
                                            0 END
                                            AS precio_venta,
                                             (t3.price_unit *
                                              t0.product_qty)                                    AS precio_lista,
                                              CASE WHEN t3.product_uom_qty > 0 THEN
                                             (t3.price_unit * t0.product_qty) - ((t3.price_total / COALESCE(t3.product_uom_qty,0.1)) *
                                                                                 t0.product_qty)
                                            ELSE
                                            0 END AS diferencia
                                           FROM stock_move t0
                                             INNER JOIN stock_picking t1 ON t1.id = t0.picking_id
                                             INNER JOIN sale_order t2 ON t2.procurement_group_id = t1.group_id
                                             INNER JOIN procurement_order t6 ON t6.id = t0.procurement_id
                                             INNER JOIN sale_order_line t3 ON t3.id = t6.sale_line_id
                                             INNER JOIN product_product t4 ON t4.id = t3.product_id
                                             INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                                             INNER JOIN stock_location t7 on t7.id = t0.location_id
                                             WHERE t7.usage != 'customer'
                                              --WHERE t0.origin_returned_move_id IS NULL
                                              --and t0.id not in (
                                              --SELECT origin_returned_move_id from stock_move
                                              --where origin_returned_move_id is not null and state in ('done')
                                              --group by origin_returned_move_id)
                                           UNION ALL

                                           SELECT
                                             t0.picking_id,
                                             t4.order_id,
                                             t0.product_id,
                                             t4.product_id,
                                             t4.price_unit,
                                             t0.price_unit                                       AS price_move,
                                             t4.discount,
                                             t0.product_qty,
                                             CASE WHEN t6.categ_id = 40
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_40,
                                             CASE WHEN t6.categ_id = 41
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_41,
                                             CASE WHEN t6.categ_id = 44
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_44,
                                             CASE WHEN t6.categ_id = 45
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_45,
                                             CASE WHEN t6.categ_id = 46
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_46,
                                             CASE WHEN t6.categ_id = 50
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_50,
                                             CASE WHEN t6.categ_id = 47
                                               THEN
                                                 t0.product_uom_qty
                                             ELSE 0 END                                          AS field_47,
                                             CASE WHEN t6.categ_id = 1054
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_1054,
                                             CASE WHEN t6.categ_id = 1056
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_1056,
                                             CASE WHEN t6.categ_id = 1055
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                          AS field_1055,
                                             CASE WHEN t4.product_uom_qty > 0 THEN
                                             (t4.price_subtotal / COALESCE(t4.product_uom_qty,0.1)) *
                                             t0.product_qty
                                             ELSE
                                             0 END AS precio_venta,
                                             (t4.price_unit *
                                              t0.product_qty)                                    AS precio_lista,
                                              CASE WHEN t4.product_uom_qty > 0 THEN
                                             (t4.price_unit * t0.product_qty) - ((t4.price_subtotal / COALESCE(t4.product_uom_qty,0.1)) *
                                                                                 t0.product_qty)
                                            ELSE
                                            0 END AS diferencia
                                           FROM stock_move t0
                                           INNER JOIN stock_picking t1 ON t1.id = t0.picking_id
                                           --INNER JOIN sale_order t2 ON t2.procurement_group_id = t1.group_id
                                           --INNER JOIN procurement_order t3 ON t3.id = t0.procurement_id
                                           INNER JOIN sale_order_line t4 ON t4.id = t0.sale_line_id
                                           INNER JOIN product_product t5 ON t5.id = t4.product_id
                                           INNER JOIN product_template t6 ON t6.id = t5.product_tmpl_id
                                           WHERE t0.procurement_id IS NULL
                                               --AND t0.picking_type_id IS NOT NULL
                                         ) AS foo
                                    GROUP BY picking_id) ddd ON ddd.picking_id = t2.id

                      UNION ALL
                      SELECT
                        t0.partner_id,
                        t0.date_order,
                        t0.name,
                        t0.warehouse_id                                                           AS shop_id,
                        to_char(t0.date_order,
                                'DD/MM/YYYY')                                                     AS date_day,
                        cast(extract(YEAR FROM t0.date_order) AS CHAR(4)) || '/' || cast(extract(WEEK FROM t0.date_order) AS
                                                                                         CHAR(3)) AS date_week,
                        to_char(t0.date_order,
                                'YYYY-MM')                                                        AS date_month,
                        CASE WHEN t0.state IN ('draft', 'sent')
                          THEN 'pendiente'
                        WHEN t0.state IN ('cancel')
                          THEN 'perdida' END                                                      AS estado,
                        t0.user_id                                                                AS user_id,
                        ddd.*
                      FROM sale_order t0
                        INNER JOIN (SELECT
                                      order_id,
                                      0                 AS picking_id,
                                      sum(precio_venta) AS amount_total,
                                      sum(precio_lista) AS pricelist_total,
                                      sum(diferencia)   AS difference,
                                      sum(field_40)     AS field_40,
                                      sum(field_41)     AS field_41,
                                      sum(field_44)     AS field_44,
                                      sum(field_45)     AS field_45,
                                      sum(field_46)     AS field_46,
                                      sum(field_50)     AS field_50,
                                      sum(field_47)     AS field_47,
                                      sum(field_1054)   AS field_1054,
                                      sum(field_1056)   AS field_1056,
                                      sum(field_1055)   AS field_1055
                                    FROM (
                                           SELECT
                                             t0.order_id,
                                             t0.product_id,
                                             t0.price_unit                                               AS price_move,
                                             t0.discount,
                                             t0.product_uom_qty,
                                             CASE WHEN t5.categ_id = 40
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                                  AS field_40,
                                             CASE WHEN t5.categ_id = 41
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                                  AS field_41,
                                             CASE WHEN t5.categ_id = 44
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                                  AS field_44,
                                             CASE WHEN t5.categ_id = 45
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                                  AS field_45,
                                             CASE WHEN t5.categ_id = 46
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                                  AS field_46,
                                             CASE WHEN t5.categ_id = 50
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                                  AS field_50,
                                             CASE WHEN t5.categ_id = 47
                                               THEN
                                                 t0.product_uom_qty
                                             ELSE 0 END                                                  AS field_47,
                                             CASE WHEN t5.categ_id = 1054
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                                  AS field_1054,
                                             CASE WHEN t5.categ_id = 1056
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                                  AS field_1056,
                                             CASE WHEN t5.categ_id = 1055
                                               THEN
                                                 t0.total_dimension
                                             ELSE 0 END                                                  AS field_1055,
                                             CASE WHEN t0.product_uom_qty > 0 THEN
                                             (t0.price_total / COALESCE(t0.product_uom_qty,0.1)) *
                                             t0.product_uom_qty
                                             ELSE
                                             0 END AS precio_venta,
                                             (t0.price_unit *
                                              t0.product_uom_qty)                                        AS precio_lista,
                                              CASE WHEN t0.product_uom_qty > 0 THEN
                                             (t0.price_unit * t0.product_uom_qty) - ((t0.price_total / COALESCE(t0.product_uom_qty,0.1)) *
                                                                                     t0.product_uom_qty)
                                            ELSE
                                            0 END AS diferencia
                                           FROM sale_order_line t0
                                             INNER JOIN product_product t4 ON t4.id = t0.product_id
                                             INNER JOIN product_template t5 ON t5.id = t4.product_tmpl_id
                                             INNER JOIN sale_order t6 ON t6.id = t0.order_id
                                           WHERE t0.product_uom_qty != 0 AND t6.state IN ('draft', 'sent', 'cancel')

                                         ) AS foo
                                    GROUP BY order_id) ddd ON ddd.order_id = t0.id
                      WHERE t0.state IN ('draft', 'sent', 'cancel') AND t0.procurement_group_id IS NULL
                    ) as foo
                    ORDER BY foo.date_order DESC
                    )"""
        cr.execute(query_to_exe)

    def launch_form(self, cr, uid, ids, context=None):

        line = self.browse(cr, uid, ids[0], context=context)
        line_id=self.pool.get('sale.order').search(cr, uid, [('name', '=', line.name)])
        line_id=line_id[0]
        action_form = {
            'name': "Orden de venta",
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
    
pret_sales_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: