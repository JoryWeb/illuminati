from odoo import models, fields, api
from datetime import date, datetime
from odoo.exceptions import Warning, ValidationError

class BagVehiclesReport(models.Model):
    _name = 'bag.vehicles.report'
    _description = 'Reporte de Bolsa de Vehiculos Sin Cliente'
    _auto = False


    released = fields.Selection(
        string="Liberado",
        selection=[
            ('sin_warrant', 'Sin Warrant'),
            ('no_liberado', 'Con Warrant'),
            ('en_tramite', 'En Trámite'),
            ('liberado', 'Liberado'),
        ]
    )
    nationalized = fields.Selection(
        string="Nacionalizado",
        selection=[
            ('no_nacionalizado', 'No Nacionalizado'),
            ('en_tramite', 'En Tramite'),
            ('temporal', u'Internación Temporal'),
            ('nacionalizado', 'Nacionalizado'),
        ]

    )
    lot_id = fields.Many2one('stock.production.lot', u'N° de Chasis')
    product_id = fields.Many2one('product.product', 'Master')
    year_id = fields.Many2one('anio.toyosa', u'Año')
    colorexterno = fields.Many2one('color.externo', 'Color')
    #type = fields.Many2one('sale.order', 'Orden de Venta')
    price = fields.Float('Precio del Vehiculo', compute="_compute_price")

    @api.multi
    def _compute_price(self):
        config_id = self.env['bag.vehicles.config'].search([])
        if config_id:
            config_id = config_id[0]
        else:
            raise Warning('Necesitas Tener una Configuracion de Lista de Precios')


        for s in self:
            for l in config_id.list_ids:
                product_id = s.product_id
                product = product_id.with_context(
                    year_id=(s.year_id and s.year_id.id) or False,
                    lang='es_BO',
                    quantity=1.0,
                    pricelist=l.pricelist_id.id,
                    uom=False,
                    date=fields.Datetime.now(),
                )
                if product.price:
                    if not s.price or s.price == 0.00:
                        s.price = product.price
                else:
                    s.price = 0.00

    @api.model
    def _update_report(self):
        self.env.cr.execute("REFRESH MATERIALIZED VIEW bag_vehicles_report");


    def _select(self):
        select_str ="""
            select
            	state_importaciones as nationalized,
                state_finanzas as released,
                id as lot_id,
                product_id,
                anio_modelo as year_id,
                colorexterno,
                sale_line_id
                /*type*/
            from
            	stock_production_lot
            where
                sale_line_id is null
        """
        return select_str


    @api.model_cr
    def init(self):
        table = "bag_vehicles_report"
        self.env.cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = 'bag_vehicles_report';
            """)
        vista = self.env.cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                self.env.cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS bag_vehicles_report;
            CREATE MATERIALIZED VIEW bag_vehicles_report as (
            SELECT row_number() over() as id, *
                FROM(%s) as asd
            )""" % (self._select()))
