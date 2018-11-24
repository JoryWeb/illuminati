from odoo import tools
from odoo import api, fields, models

class InventorySpeedReport(models.Model):
    _name = "inventory.speed.report"
    _description = "Reporte Inventarios Veloz"
    _auto = False

    categ_id = fields.Many2one('product.category', string=u'Categoría', readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    reservation_id = fields.Many2one('stock.move', string='Reservado para', readonly=True)
    in_date = fields.Datetime(string='Fecha Entrada', readonly=True)
    lot_id = fields.Many2one("stock.production.lot", string="Chasis/Lote", readonly=True)
    location_id = fields.Many2one("stock.location", string=u"Ubicación", readonly=True)
    usage = fields.Char(u"Tipo Ubicación")
    qty = fields.Float(string='Cantidad', readonly=True)
    product_uom_id = fields.Many2one("product.uom", string='Unidad de Medida', readonly=True)
    total = fields.Float(string='Total', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'inventory_speed_report')
        self.env.cr.execute("""
        create or replace view inventory_speed_report as (
        select
          t0.id as id,
          t2.categ_id,
          t0.product_id,
          t0.reservation_id,
          t0.in_date,
          t0.lot_id,
          t0.location_id,
          t3.usage,
          t0.qty,
          t2.uom_id as product_uom_id,
          t0.qty*t0.cost as total
        from stock_quant t0
        inner join product_product t1 on t1.id = t0.product_id
        inner join product_template t2 on t2.id = t1.product_tmpl_id
        inner join stock_location t3 on t3.id = t0.location_id
        order by id
        )""")
