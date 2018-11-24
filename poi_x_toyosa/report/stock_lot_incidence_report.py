from odoo import tools
from odoo import api, fields, models

class StockLotIncidenceReport(models.Model):
    _name = "stock.lot.incidence.report"
    _description = "Reporte de Incidencias"
    _auto = False

    stock_production_lot_id = fields.Many2one('stock.production.lot', string=u'Serie/Chasis', readonly=True)
    name = fields.Char(string="Nombre", readonly=True)
    observaciones = fields.Char(string="Observaciones", readonly=True)
    tipo = fields.Many2one("stock.lot.incidence.type", string=u"Tipo de Incidencia", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'stock_lot_incidence_report')
        self.env.cr.execute("""
        create or replace view stock_lot_incidence_report as (
        select t0.id,
          t1.stock_production_lot_id,
          t0.name,
          t0.observaciones,
          t0.tipo
        from stock_lot_incidence t0
        inner join stock_lot_incidence_stock_production_lot_rel t1 on t1.stock_lot_incidence_id = t0.id
        )""")
