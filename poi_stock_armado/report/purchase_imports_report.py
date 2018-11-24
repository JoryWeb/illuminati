from openerp import fields, models, tools


class PoiPurchaseImportsReport(models.Model):
    _name = "poi.purchase.imports.report"
    _description = "Reporte de Importaciones"
    _auto = False

    orden = fields.Char(string=u'Orden de Impotación', required=False, readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    movimiento = fields.Char(string=u'Movimiento', required=False, readonly=True)
    product_qty = fields.Float(string='Cantidad', readonly=True)
    price_unit = fields.Float(string='Precio Unitario', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    costo = fields.Float(string='Costo Adicional', readonly=True)
    product_cost_id = fields.Many2one('product.product', string='Producto Costo', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'poi_purchase_imports_report')
        cr.execute("""
            create or replace view poi_purchase_imports_report as (
                select row_number() OVER () as id, importaciones.*,
                      (importaciones.product_qty*importaciones.price_unit) as total
                from (
                  SELECT
                    t2.origin                 AS orden,
                    t2.product_id,
                    t2.name                   AS movimiento,
                    t2.product_qty,
                    t2.price_unit,
                    t0.additional_landed_cost AS costo,
                    t1.product_id             AS product_cost_id
                  FROM stock_valuation_adjustment_lines t0
                    INNER JOIN stock_landed_cost_lines t1 ON t1.id = t0.cost_line_id
                    INNER JOIN stock_move t2 ON t2.id = t0.move_id
                    LEFT JOIN purchase_order_line t3 ON t3.id = t2.purchase_line_id
                    LEFT JOIN purchase_order t4 ON t4.id = t3.order_id

                  UNION ALL

                  SELECT
                    t5.name           AS orden,
                    t1.product_id,
                    t3.name           AS movimiento,
                    t3.product_qty,
                    t3.price_unit,
                    t0.expense_amount AS costo,
                    t2.product_id AS product_cost_id
                  FROM poi_purchase_imports_line_expense t0
                    INNER JOIN poi_purchase_imports_line t1 ON t1.id = t0.distribution_line
                    INNER JOIN poi_purchase_imports_expense t2 ON t2.id = t0.distribution_expense
                    INNER JOIN stock_move t3 ON t3.id = t1.move_id
                    INNER JOIN purchase_order_line t4 ON t4.id = t3.purchase_line_id
                    INNER JOIN purchase_order t5 ON t5.id = t4.order_id
                    INNER JOIN product_product t6 ON t6.id = t3.product_id
                    LEFT JOIN product_product t7 ON t7.id = t2.product_id
                    LEFT JOIN account_invoice t8 ON t8.id = t2.invoice_id
                ) as importaciones
        )""")
