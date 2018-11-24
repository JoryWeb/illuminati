from odoo import tools
from odoo import api, fields, models

class InventoryDuiReport(models.Model):
    _name = "inventory.dui.report"
    _description = "Reporte Inventarios Veloz"
    _auto = False

    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    reservation_id = fields.Many2one('stock.move', string='Reservado para', readonly=True)
    in_date = fields.Datetime(string='Fecha Importaciones', readonly=True)
    lot_id = fields.Many2one("stock.production.lot", string="Chasis/Lote", readonly=True)
    location_id = fields.Many2one("stock.location", string=u"Ubicación", readonly=True)
    usage = fields.Char(u"Tipo Ubicación")
    qty = fields.Float(string='Cantidad', readonly=True)
    product_uom_id = fields.Many2one("product.uom", string='Unidad de Medida', readonly=True)
    invoice_id = fields.Many2one("account.invoice", string=u"N° Fact. Importaciones")
    date_factura = fields.Datetime(string=u"Fecha Fact. Imp")
    ref_proveedor = fields.Char(string=u"Ref. Proveedor DUI")
    imp_pol = fields.Char(string=u"Nro. Póliza Importación")
    n_factura_dui = fields.Many2one("account.invoice", string=u"N° Fact. DUI")
    date_dui = fields.Datetime(string=u"Fecha Fact. DUI")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'inventory_dui_report')
        self.env.cr.execute("""
        create or replace view inventory_dui_report as (
            select
              t0.id as id,
              t0.product_id,
              t0.reservation_id,
              t0.in_date,
              t0.lot_id,
              t0.location_id,
              t3.usage,
              t0.qty,
              t2.uom_id as product_uom_id,
              t5.id as invoice_id,
              t5.date as date_factura,
              t6.reference as ref_proveedor,
              t6.imp_pol,
              t6.date as date_dui
            from stock_quant t0
            inner join product_product t1 on t1.id = t0.product_id
            inner join product_template t2 on t2.id = t1.product_tmpl_id
            inner join stock_location t3 on t3.id = t0.location_id
            inner join poi_purchase_imports t4 on t4.id = t0.imports
            left join account_invoice t5 on t5.id = t4.invoice_id
            left join account_invoice t6 on t6.imports = t4.id and t6.iva > 0
            order by id
        )""")
