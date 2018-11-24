from odoo import tools
from odoo import api, fields, models


class except_osv(Exception):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.args = (name, value)

service = None

class PoiReportKardexChasis(models.Model):
    _name = 'poi.report.kardex.chasis'
    _description = "Reporte Kardex Lote/Chasis"
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
    subtotal = fields.Float(string='Venta total', readonly=True)
    incremento_ufv = fields.Float(string='Valor Ufv', readonly=True)
    costo_fin = fields.Float(string='Costo fin', readonly=True)
    rentabilidad = fields.Float(string='Rentabilidad', readonly=True)

    def _select(self, cr, date_to='', lot_id = 0):

        sql_kardexvalorado = """
        select *, (foo.total+foo.incremento_ufv) as costo_fin, (foo.total+foo.incremento_ufv - foo.subtotal) as rentabilidad from (
            select
              t2.categ_id,
              t2.modelo,
              t2.katashiki,
              t0.product_id,
              t3.colorinterno,
              t3.colorexterno,
              t0.lot_id,
              t0.location_id,
              t0.qty,
              t0.qty*t0.cost as total,
              coalesce((select
              sum(((total_price*ufv_final)/ufv_inicial - total_price)) as incremento_ufv
            from poi_ufv_inventory_line
              where product_id = t0.product_id
                and quant_id = t0.id
                and lot_id = t3.id
                and date <= '""" + str(date_to) + """'),0) as incremento_ufv,
              coalesce(t4.price_subtotal, 0) as subtotal,
              t3.sale_line_id
            from stock_quant t0
            inner join product_product t1 on t1.id = t0.product_id
            inner join product_template t2 on t2.id = t1.product_tmpl_id
            inner join stock_production_lot t3 on t3.id = t0.lot_id
            left join sale_order_line t4 on t4.id = t3.sale_line_id
            WHERE t0.lot_id = """ + str(lot_id) + """
            order by t0.product_id
            ) as foo
        """
        return sql_kardexvalorado

    def init(self, cr, date_to=time.strftime("%Y-%m-%d"), lot_id=0):
        sql = """ DROP VIEW if exists poi_report_kardex_chasis;
                  CREATE or REPLACE VIEW poi_report_kardex_chasis as ((
                      SELECT row_number() over() as id, *
                        FROM ((
                            %s
                        )) as asd
              ))""" % (self._select(cr, date_to, lot_id))
        cr.execute(sql)
