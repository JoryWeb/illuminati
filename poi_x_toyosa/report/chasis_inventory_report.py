from odoo import tools
from odoo import api, fields, models

class PoiChasisInventoryReport(models.Model):
    _name = "poi.chasis.inventory.report"
    _description = "Chasis Inventario Reporte"
    _auto = False

    categ_id = fields.Many2one('product.category', string=u'Categoría', readonly=True)
    modelo = fields.Many2one("modelo.toyosa", string="Modelo", readonly=True)
    katashiki = fields.Many2one("katashiki.toyosa", string=u"Código modelo", readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    colorinterno = fields.Many2one("color.interno", string="Color Interno", readonly=True)
    colorexterno = fields.Many2one("color.externo", string="Color Externo", readonly=True)
    lot_id = fields.Many2one("stock.production.lot", string="Chasis/Lote", readonly=True)
    location_id = fields.Many2one("stock.location", string=u"Ubicación", readonly=True)
    qty = fields.Float(string='Cantidad', readonly=True)
    total = fields.Float(string='Total', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'poi_chasis_inventory_report')
        self.env.cr.execute("""
        create or replace view poi_chasis_inventory_report as (
        select
          t0.id,
          t3.categ_id,
          t3.modelo,
          t3.katashiki,
          t1.product_id,
          t4.colorinterno,
          t4.colorexterno,
          t0.lot_id,
          t0.location_dest_id as location_id,
          t1.remaining_qty as qty,
          t1.remaining_value as total
        from stock_move_line t0
          inner join stock_move t1 on t1.id = t0.move_id
          inner join product_product t2 on t2.id = t1.product_id
          inner join product_template t3 on t2.product_tmpl_id = t3.id
          left join stock_production_lot t4 on t0.lot_id = t4.id
        where t1.remaining_qty > 0 and t1.state in ('done')
        )""")
