from odoo import tools
from odoo import api, fields, models


class PoiPurchaseImportsReport(models.Model):
    _name = "poi.purchase.imports.report"
    _description = "Reporte de Importaciones"
    _auto = False
    category = fields.Char(string=u"Concepto", readonly=True, help=u"Concepto del Gasto")
    proveedor = fields.Many2one("res.partner", string="Proveedor", readonly=True,
                                help=u"Proveedor de Gasto o Factura FOB")
    invoice_id = fields.Many2one("account.invoice", string="Doc.", readonly=True, help=u"Documento en sistema")
    order_id = fields.Many2one("purchase.order", string="Orden de compra", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Proveedor Compra", readonly=True)
    country_id = fields.Many2one("res.country", string="Procedencia", readonly=True)
    orden = fields.Char(string=u'Orden de Impotación', readonly=True, help=u"Orden de Compra o Importaciones")
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    movimiento = fields.Char(string=u'Movimiento', readonly=True, help=u"Nombre de gasto o item de compra")
    product_qty = fields.Char(string='Cantidad', readonly=True,
                              help=u"Cantidad de compra o cantidad utilizada para la compra")
    price_unit = fields.Char(string=u'Costo Bs.', readonly=True, help=u"Precio Unitario")
    price_unit_usd = fields.Char(string=u'Costo $us', readonly=True, help=u"Precio Unitario Dolares")
    total = fields.Char(string='Total', readonly=True, help=u"Total de compra")
    total_usd = fields.Char(string='Total $us', readonly=True, help=u"Total de compra en dolares")
    costo = fields.Float(string='Pago', readonly=True, help=u"Pago")
    costo_usd = fields.Float(string='Pago $us', readonly=True, help=u"Pago en Dolares")
    product_cost_id = fields.Many2one('product.product', string='Items', readonly=True,
                                      help=u"Item o concepto de importación")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'poi_purchase_imports_report')
        self.env.cr.execute("""
            create or replace view poi_purchase_imports_report as (
                SELECT
                  row_number()
                  OVER ()                                                              AS id,
                  importaciones.*,
                  (importaciones.product_qty * importaciones.price_unit)               AS total,
                  ((SELECT rate
                    FROM res_currency_rate
                    WHERE currency_id = 3
                    ORDER BY name DESC
                    LIMIT 1) * (importaciones.product_qty * importaciones.price_unit)) AS total_usd
                FROM (
                       SELECT
                          t8.name                                              AS category,
                          t9.partner_id                                        AS proveedor,
                          t9.invoice_id,
                          t4.order_id                                          AS order_id,
                          t4.partner_id,
                          t6.country_id,
                          t5.name                                              AS orden,
                          t2.product_id,
                          t0.name                                              AS movimiento,
                          COALESCE(t2.product_qty, 0)                          AS product_qty,
                          COALESCE(t2.price_unit, 0)                           AS price_unit,
                          ((SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = 3
                            ORDER BY name DESC
                            LIMIT 1) * COALESCE(t2.price_unit, 0))             AS price_unit_usd,
                          t0.additional_landed_cost                            AS costo,
                          ((SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = 3
                            ORDER BY name DESC
                            LIMIT 1) * COALESCE(t0.additional_landed_cost, 0)) AS costo_usd,
                          t1.product_id                                        AS product_cost_id
                        FROM stock_valuation_adjustment_lines t0
                          LEFT JOIN stock_landed_cost_lines t1 ON t1.id = t0.cost_line_id
                          LEFT JOIN stock_move t2 ON t2.id = t0.move_id
                          LEFT JOIN stock_picking t3 ON t3.id = t2.picking_id
                          INNER JOIN purchase_order_line t4 on t4.id = t2.purchase_line_id
                          LEFT JOIN purchase_order t5 ON t5.id = t4.order_id
                          LEFT JOIN res_partner t6 ON t6.id = t4.partner_id
                          LEFT JOIN product_product t7 ON t7.id = t1.product_id
                          LEFT JOIN product_template t8 ON t8.id = t7.product_tmpl_id
                          LEFT JOIN account_invoice_line t9 on t9.purchase_line_id = t4.id
                        
                        UNION ALL
                        select * from (
                        SELECT
                          t8.name                                              AS category,
                          foo.partner_id                                       AS proveedor,
                          foo.invoice_id                                       AS invoice_id,
                          foo.order_id                                         AS order_id,
                          foo.partner_id,
                          foo.country_id,
                          foo.name                                             AS orden,
                          t2.product_id,
                          t0.name                                              AS movimiento,
                          COALESCE(t2.product_qty, 0)                          AS product_qty,
                          COALESCE(t3.price_unit, 0)                           AS price_unit,
                          ((SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = 3
                            ORDER BY name DESC
                            LIMIT 1) * COALESCE(t3.price_unit, 0))             AS price_unit_usd,
                          t0.additional_landed_cost / t0.quantity              AS costo,
                          ((SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = 3
                            ORDER BY name DESC
                            LIMIT 1) * COALESCE(t0.additional_landed_cost / t0.quantity , 0)) AS costo_usd,
                          t1.product_id                                        AS product_cost_id
                        FROM stock_valuation_adjustment_lines t0
                          INNER JOIN stock_landed_cost_lines t1 ON t1.id = t0.cost_line_id
                          INNER JOIN stock_move_line t2 ON t2.move_id = t0.move_id
                          INNER JOIN stock_move t3 on t3.id = t2.move_id
                          INNER JOIN (select
                                       t0.lot_id,
                                       t0.lot_name,
                                       t2.order_id,
                                       t3.partner_id,
                                       t4.country_id,
                                       t3.name,
                                       t9.invoice_id
                                     from stock_move_line t0
                                       inner join stock_move t1 on t1.id = t0.move_id
                                       inner join purchase_order_line t2 on t2.id = t1.purchase_line_id
                                       inner join purchase_order t3 on t3.id = t2.order_id
                                       inner join res_partner t4 on t4.id = t3.partner_id
                                       LEFT JOIN account_invoice_line t9 on t9.purchase_line_id = t2.id
                                     where lot_name != '') as foo on foo.lot_id = t2.lot_id
                          LEFT JOIN product_product t7 ON t7.id = t1.product_id
                          LEFT JOIN product_template t8 ON t8.id = t7.product_tmpl_id
                          where t0.move_line_id is not null) as foore
                        UNION ALL 
                        
                        SELECT
                          t8.name                                              AS category,
                          foo.partner_id                                       AS proveedor,
                          foo.invoice_id                                       AS invoice_id,
                          foo.order_id                                         AS order_id,
                          foo.partner_id,
                          foo.country_id,
                          foo.name                                             AS orden,
                          t2.product_id,
                          t0.name                                              AS movimiento,
                          COALESCE(t2.product_qty, 0)                          AS product_qty,
                          COALESCE(t3.price_unit, 0)                           AS price_unit,
                          ((SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = 3
                            ORDER BY name DESC
                            LIMIT 1) * COALESCE(t3.price_unit, 0))             AS price_unit_usd,
                          t0.additional_landed_cost / t0.quantity              AS costo,
                          ((SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = 3
                            ORDER BY name DESC
                            LIMIT 1) * COALESCE(t0.additional_landed_cost / t0.quantity , 0)) AS costo_usd,
                          t1.product_id                                        AS product_cost_id
                        FROM stock_valuation_adjustment_lines t0
                          INNER JOIN stock_landed_cost_lines t1 ON t1.id = t0.cost_line_id
                          INNER JOIN stock_move_line t2 ON t2.id = t0.move_line_id
                          INNER JOIN stock_move t3 on t3.id = t2.move_id
                          INNER JOIN (select
                                       t0.lot_id,
                                       t0.lot_name,
                                       t2.order_id,
                                       t3.partner_id,
                                       t4.country_id,
                                       t3.name,
                                       t9.invoice_id
                                     from stock_move_line t0
                                       inner join stock_move t1 on t1.id = t0.move_id
                                       inner join purchase_order_line t2 on t2.id = t1.purchase_line_id
                                       inner join purchase_order t3 on t3.id = t2.order_id
                                       inner join res_partner t4 on t4.id = t3.partner_id
                                       LEFT JOIN account_invoice_line t9 on t9.purchase_line_id = t2.id
                                     where lot_name != '') as foo on foo.lot_id = t2.lot_id
                          LEFT JOIN product_product t7 ON t7.id = t1.product_id
                          LEFT JOIN product_template t8 ON t8.id = t7.product_tmpl_id
                          
                        UNION ALL

                        SELECT
                              'A. TOTAL FOB' as category,
                              t0.partner_id                             AS proveedor,
                              t3.invoice_id,
                              t0.order_id,
                              t0.partner_id,
                              t5.country_id,
                              t4.name                                   AS orden,
                              t0.product_id,
                              t0.name                                   AS movimiento,
                              t0.product_qty,
                              CASE WHEN t3.currency_id = 3 THEN
                              (COALESCE(t3.price_subtotal, 0) /(SELECT rate
                                  FROM res_currency_rate
                                  WHERE currency_id = 3
                                  ORDER BY name DESC
                                  LIMIT 1) )
                              ELSE
                                t3.price_subtotal
                              END AS price_unit,


                              CASE WHEN t3.currency_id = 63 THEN
                                ((SELECT rate
                                  FROM res_currency_rate
                                  WHERE currency_id = 3
                                  ORDER BY name DESC
                                  LIMIT 1)*COALESCE(t0.price_unit, 0))
                              ELSE
                                t3.price_subtotal
                              END  as price_unit_usd,

                              CASE WHEN t3.currency_id = 3 THEN
                                (COALESCE(t3.price_subtotal, 0) /(SELECT rate
                                  FROM res_currency_rate
                                  WHERE currency_id = 3
                                  ORDER BY name DESC
                                  LIMIT 1) )
                              ELSE
                                t3.price_subtotal
                              END AS costo,

                              CASE WHEN t3.currency_id = 63 THEN
                              ((SELECT rate
                                FROM res_currency_rate
                                WHERE currency_id = 3
                                ORDER BY name DESC
                                LIMIT 1) * COALESCE(t3.price_subtotal, 0))
                              ELSE
                                t3.price_subtotal
                              END AS costo_usd,
                              t0.product_id
                            FROM purchase_order_line t0
                              INNER JOIN product_product t1 ON t1.id = t0.product_id
                              INNER JOIN product_template t2 ON t2.id = t1.product_tmpl_id
                              INNER JOIN account_invoice_line t3 ON t3.purchase_line_id = t0.id
                              INNER JOIN purchase_order t4 ON t4.id = t0.order_id
                              INNER JOIN res_partner t5 ON t5.id = t4.partner_id
                            WHERE t4.tipo_fac = '3'

                        /* Todo: Ver para promedio ponderado
                        UNION ALL
                        SELECT
                          t12.name                                          AS category,
                          t2.partner_id as proveedor,
                          t2.invoice_id,
                          t5.id                                        AS order_id,
                          t5.partner_id,
                          t9.country_id,
                          t5.name                                      AS orden,
                          t1.product_id,
                          t3.name                                      AS movimiento,
                          COALESCE(t3.product_qty, 0)                  AS product_qty,
                          COALESCE(t3.price_unit, 0)                   AS price_unit,
                          ((SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = 3
                            ORDER BY name DESC
                            LIMIT 1) * COALESCE(t3.price_unit, 0))     AS price_unit_usd,
                          t0.expense_amount                            AS costo,
                          ((SELECT rate
                            FROM res_currency_rate
                            WHERE currency_id = 3
                            ORDER BY name DESC
                            LIMIT 1) * COALESCE(t0.expense_amount, 0)) AS costo_usd,
                          t2.product_id                                AS product_cost_id
                        FROM poi_purchase_imports_line_expense t0
                          LEFT JOIN poi_purchase_imports_line t1 ON t1.id = t0.distribution_line
                          LEFT JOIN poi_purchase_imports_expense t2 ON t2.id = t0.distribution_expense
                          LEFT JOIN stock_move t3 ON t3.id = t1.move_id
                          LEFT JOIN purchase_order_line t4 ON t4.id = t3.purchase_line_id
                          LEFT JOIN purchase_order t5 ON t5.id = t4.order_id
                          LEFT JOIN product_product t6 ON t6.id = t3.product_id
                          LEFT JOIN product_product t7 ON t7.id = t2.product_id
                          LEFT JOIN account_invoice t8 ON t8.id = t2.invoice_id
                          LEFT JOIN res_partner t9 ON t9.id = t5.partner_id
                          LEFT JOIN product_product t10 on t10.id = t2.product_id
                          LEFT JOIN product_template t11 on t11.id = t10.product_tmpl_id
                          LEFT JOIN product_category t12 on t12.id = t11.categ_id*/
          ) AS importaciones
        )""")
