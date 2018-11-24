from odoo import tools
from odoo import api, fields, models


class WorkshopOrderReport(models.Model):
    _name = "workshop.order.report"
    _description = "Reporte Analisis Ordenes de Trabajo"
    _auto = False

    maintenance_id = fields.Many2one('workshop.order', string=u'Orden de Mantenimiento', readonly=True)
    partner_id = fields.Many2one("res.partner", string="Cliente", readonly=True)
    n_chasis = fields.Char(u"N° Chasis")
    asset_id = fields.Many2one("poi.vehicle", string=u"Vehículos", readonly=True)
    lot_id = fields.Many2one("stock.production.lot", string='Serie', readonly=True)
    product_id = fields.Many2one("product.product", string=u"Producto", readonly=True)
    cost = fields.Float(string="Costo", readonly=True)
    date_scheduled = fields.Datetime(string="Fecha Recepción", readonly=True)
    date_planned = fields.Datetime(string="Fecha Prevista", readonly=True)
    date_execution = fields.Datetime(string="Entrega", readonly=True)
    estado = fields.Char(string="Estado", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'workshop_order_report')
        self.env.cr.execute("""
        create or replace view workshop_order_report as (
        select row_number() over() as id, * from (
              SELECT
                t0.id AS maintenance_id,
                t0.partner_id,
                t0.n_chasis,
                t0.asset_id,
                t2.id AS lot_id,
                t2.product_id,
                t3.cost,
                t0.date_scheduled,
                t0.date_planned,
                t0.date_execution,
                CASE WHEN t0.state = 'draft'
                  THEN
                    'BORRADOR'
                WHEN t0.state = 'released'
                  THEN
                    'PLANIFICADO'
                WHEN t0.state = 'ready'
                  THEN
                    'APROBADO'
                WHEN t0.state = 'stop'
                  THEN
                    'DETENIDA'
                WHEN t0.state = 'invoiced'
                  THEN
                    'FACTURADO'
                WHEN t0.state = 'done'
                  THEN
                    'REALIZADO'
                WHEN t0.state = 'cancel'
                  THEN
                    'CANCELADO'
                END AS estado
              FROM workshop_order t0
                INNER JOIN poi_vehicle t1 ON t1.id = t0.asset_id
                LEFT JOIN stock_production_lot t2 ON t2.id = t1.chasis_id
                LEFT JOIN stock_quant t3 ON t3.lot_id = t2.id AND t3.product_id = t2.product_id

              UNION ALL

              SELECT
                t1.id         AS maintenance_id,
                t1.partner_id,
                t1.n_chasis,
                t1.asset_id,
                t3.id         AS lot_id,
                t0.service_id AS product_id,
                t0.price_unit AS cost,
                t1.date_scheduled,
                t1.date_planned,
                t1.date_execution,
                CASE WHEN t1.state = 'draft'
                  THEN
                    'BORRADOR'
                WHEN t1.state = 'released'
                  THEN
                    'PLANIFICADO'
                WHEN t1.state = 'ready'
                  THEN
                    'APROBADO'
                WHEN t1.state = 'stop'
                  THEN
                    'DETENIDA'
                WHEN t1.state = 'invoiced'
                  THEN
                    'FACTURADO'
                WHEN t1.state = 'done'
                  THEN
                    'REALIZADO'
                WHEN t1.state = 'cancel'
                  THEN
                    'CANCELADO'
                END AS estado
              FROM workshop_order_service_line t0
                INNER JOIN workshop_order t1 ON t1.id = t0.maintenance_id
                INNER JOIN poi_vehicle t2 ON t2.id = t1.asset_id
                LEFT JOIN stock_production_lot t3 ON t3.id = t2.chasis_id

              UNION ALL

              SELECT
                t1.id         AS maintenance_id,
                t1.partner_id,
                t1.n_chasis,
                t1.asset_id,
                t3.id         AS lot_id,
                t0.parts_id   AS product_id,
                t0.price_unit AS cost,
                t1.date_scheduled,
                t1.date_planned,
                t1.date_execution,
                CASE WHEN t1.state = 'draft'
                  THEN
                    'BORRADOR'
                WHEN t1.state = 'released'
                  THEN
                    'PLANIFICADO'
                WHEN t1.state = 'ready'
                  THEN
                    'APROBADO'
                WHEN t1.state = 'stop'
                  THEN
                    'DETENIDA'
                WHEN t1.state = 'invoiced'
                  THEN
                    'FACTURADO'
                WHEN t1.state = 'done'
                  THEN
                    'REALIZADO'
                WHEN t1.state = 'cancel'
                  THEN
                    'CANCELADO'
                END AS estado
              FROM workshop_order_parts_line t0
                INNER JOIN workshop_order t1 ON t1.id = t0.maintenance_id
                INNER JOIN poi_vehicle t2 ON t2.id = t1.asset_id
                LEFT JOIN stock_production_lot t3 ON t3.id = t2.chasis_id
            ) as foo
            order by foo.n_chasis
        )""")
