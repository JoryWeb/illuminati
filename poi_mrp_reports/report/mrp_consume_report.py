from openerp import fields, models, tools


class PoiMrpConsumeReport(models.Model):
    _name = "poi.mrp.consume.report"
    _description = "Reporte de origen de insumos"
    _auto = False

    production_id = fields.Many2one('mrp.production', string=u'Orden de Fabricación', readonly=True)
    product_id = fields.Many2one('product.product', string=u'Producto', readonly=True)
    product_qty = fields.Char(string="Cantidad", readonly=True)
    location_dest_id = fields.Many2one("stock.location", string=u"Ubicación", readonly=True)
    product_insumo_id = fields.Many2one('product.product', string=u'Producto Insumo', readonly=True)
    quant_id = fields.Many2one('stock.quant', string='Registro de Stock', readonly=True)
    qty = fields.Float("Cantidad Consumida")
    cost = fields.Float("Costo")
    lot_id = fields.Many2one('stock.production.lot', string='Lote', readonly=True)
    location_id = fields.Many2one('stock.location', string=u'Ubicacion Lote')
    in_date = fields.Datetime(string="Fecha Ingreso", readonly=True)
    consumed_for = fields.Many2one("stock.move", string="Movimiento Destino", readonly=True)
    origen = fields.Char(string="Origen", readonly=True)
    partner_id = fields.Many2one("res.partner", string=u"Proveedor de Insumo", readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'poi_mrp_consume_report')
        cr.execute("""
        create or replace view poi_mrp_consume_report as (
            select
              row_number() over() as id,
              t1.raw_material_production_id as production_id,
              t4.product_id,
              t4.product_qty,
              t4.location_dest_id,
              t1.product_id as product_insumo_id,
              t3.id as quant_id,
              t3.qty,
              t3.cost,
              t3.lot_id,
              t3.location_id,
              t3.in_date,
              t1.consumed_for,
              (SELECT s1.origin
            FROM stock_quant_move_rel s0
              INNER JOIN stock_move s1 ON s1.id = s0.move_id
              LEFT JOIN stock_picking s2 ON s2.id = s1.picking_id
            WHERE s0.quant_id = t3.id
            ORDER BY s1.date asc
            LIMIT 1) as origen,
              (SELECT s2.partner_id
            FROM stock_quant_move_rel s0
              INNER JOIN stock_move s1 ON s1.id = s0.move_id
              LEFT JOIN stock_picking s2 ON s2.id = s1.picking_id
            WHERE s0.quant_id = t3.id
            ORDER BY s1.date asc
            LIMIT 1) as partner_id
            from stock_quant_move_rel t0
            inner join stock_move t1 on t1.id = t0.move_id
              inner join product_product t2 on t2.id = t1.product_id
              inner join stock_quant t3 on t3.id = t0.quant_id
              inner join stock_move t4 on t4.id = t1.consumed_for
            order by t4.origin
        )""")
