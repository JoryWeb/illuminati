from odoo import tools
from odoo import api, fields, models

class InventorySpeedPrevistoReport(models.Model):
    _name = "inventory.speed.previsto.report"
    _description = "Reporte Inventarios Veloz"
    _auto = False

    categ_id = fields.Many2one('product.category', string=u'Categoría', readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    reservation_id = fields.Many2one('stock.move', string='Reservado para', readonly=True)
    in_date = fields.Datetime(string='Fecha Entrada', readonly=True)
    lot_id = fields.Many2one("stock.production.lot", string="Chasis/Lote", readonly=True)
    location_id = fields.Many2one("stock.location", string=u"Ubicación", readonly=True)
    usage = fields.Char(u"Tipo Ubicación")
    total = fields.Float(string='Cantidad', readonly=True)
    previsto = fields.Float(string='Cantidad Prevista', readonly=True)
    product_uom_id = fields.Many2one("product.uom", string='Unidad de Medida', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'inventory_speed_previsto_report')
        self.env.cr.execute("""
        create or replace view inventory_speed_previsto_report as (
        select row_number() over() as id,
          t2.categ_id,
          t0.product_id,
          t0.reservation_id,
          t0.lot_id,
          t0.location_id,
          t3.usage,
          sum(t0.qty) as total,
          sum(coalesce(pr.previsto,0)) as previsto,
          t2.uom_id as product_uom_id
        from stock_quant t0
        inner join product_product t1 on t1.id = t0.product_id
        inner join product_template t2 on t2.id = t1.product_tmpl_id
        inner join stock_location t3 on t3.id = t0.location_id
        LEFT JOIN (SELECT t0.product_id, t0.location_dest_id, sum(t0.product_uom_qty) as previsto
        FROM stock_move t0
        INNER JOIN stock_location t1 on t1.id = t0.location_id
        INNER JOIN stock_location t2 on t2.id = t0.location_dest_id
        WHERE t0.state in ('assigned','confirmed','waiting')
        AND t1.usage in ('supplier','customer','inventory','procurement','production','vehicle')
        AND t2.usage in ('internal','transit')
        group by t0.product_id, t0.location_dest_id) as pr on pr.product_id = t0.product_id and pr.location_dest_id = t0.location_id
        group by t2.categ_id,t0.product_id,t0.reservation_id,t0.lot_id,t0.location_id,t3.usage,t2.uom_id
        )""")
