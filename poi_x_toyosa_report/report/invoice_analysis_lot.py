from odoo import models, fields, api, _, tools
from datetime import datetime
import time
import odoo.addons.decimal_precision as dp
from odoo.osv import expression

ESTADO_VENTA = [
    ('draft', 'Disponible'),
    ('reserve', 'Reservado'),
    ('invoiced', 'Facturado'),
    ('done', 'Entregado'),
]

ESTADO_FINANZAS = [
    ('sin_warrant', 'Sin Warrant'),
    ('no_liberado', 'Con Warrant'),
    ('en_tramite', 'En Trámite'),
    ('liberado', 'Liberado'),
]

ESTADO_IMPORTACION = [
    ('no_nacionalizado', 'No Nacionalizado'),
    ('en_tramite', 'En Tramite'),
    ('temporal', u'Internación Temporal'),
    ('nacionalizado', 'Nacionalizado'),
]

class AccountInvoiceAnalysisLot(models.Model):
    _name = 'account.invoice.analysis.lot'
    _inherit = "account.invoice.report"

    @api.multi
    @api.depends('product_id')
    def _compute_brand_id(self):
        if self.product_id:
            self.brand_id = self.product_id.modelo.marca

    invoice_id = fields.Many2one('account.invoice', 'Factura')
    # date_invoice = fields.Date('Fecha de Facturacion')
    lot_id = fields.Many2one('stock.production.lot', 'Lote/Chasis')
    # amount_total = fields.Float('Total')
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen')
    agency_id = fields.Many2one('res.agency', 'Regional')
    model_id = fields.Many2one('modelo.toyosa', 'Modelo')
    year_model_id = fields.Many2one('anio.toyosa', 'Año Modelo')
    year_fabrication_id = fields.Many2one('anio.toyosa', 'Año de Fabricacion')
    edition = fields.Char('Edicion')
    color_int_id = fields.Many2one('color.interno', 'Color Interno')
    color_ext_id = fields.Many2one('color.externo', 'Color Externo')
    # current_location_id = fields.Many2one('stock.location', 'Ubicacion Actual')
    brand_id = fields.Many2one('marca.toyosa', 'Marca', compute="_compute_brand_id")
    state_l = fields.Selection(ESTADO_VENTA, string="Estado Venta")
    state_f = fields.Selection(ESTADO_FINANZAS, string="Estado Finanzas")
    state_i = fields.Selection(ESTADO_IMPORTACION, string="Estado Importaciones")
    category_root_id = fields.Many2one('product.category', string='Categoria Raiz')


    def _select(self):
        select_str = super(AccountInvoiceAnalysisLot, self)._select()
        select_str += """,
                sub.invoice_id,
                sub.lot_id,
                sub.warehouse_id,
                sub.agency_id,
                sub.model_id,
                sub.year_model_id,
                sub.year_fabrication_id,
                sub.edition,
                sub.color_ext_id,
                sub.colorinterno,
                sub.state_l,
                sub.state_f,
                sub.state_i,
                sub.category_root_id
        """
        return select_str

    def _sub_select(self):
        select_str = super(AccountInvoiceAnalysisLot, self)._sub_select()
        select_str += """,
                ai.id as invoice_id,
                ail.lot_id,
                ai.warehouse_id,
                sw.agency_id,
                lot.modelo as model_id,
                lot.anio_modelo as year_model_id,
                lot.anio_fabricacion as year_fabrication_id,
                lot.edicion as edition,
                lot.colorexterno as color_ext_id,
                lot.colorinterno as colorinterno,
                lot.state as state_l,
                lot.state_finanzas as state_f,
                lot.state_importaciones as state_i,
                pt.category_root as category_root_id
        """
        return select_str

    def _from(self):
        from_str = super(AccountInvoiceAnalysisLot, self)._from()
        from_str += """
                LEFT JOIN stock_warehouse sw on sw.id = ai.warehouse_id
                LEFT JOIN stock_production_lot lot ON lot.id = ail.lot_id

                WHERE ai.type = 'out_invoice' and ail.lot_id is not null
        """
        return from_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceAnalysisLot, self)._group_by()
        group_by_str += """, sw.agency_id, lot.modelo, lot.anio_modelo, lot.anio_fabricacion, lot.edicion, lot.colorexterno, lot.colorinterno,  lot.state, lot.state_finanzas, lot.state_importaciones, pt.category_root"""
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """CREATE or REPLACE VIEW %s as (
            WITH currency_rate AS (%s)
            %s
            FROM (
                %s %s %s
            ) AS sub
            LEFT JOIN currency_rate cr ON
                (cr.currency_id = sub.currency_id AND
                 cr.company_id = sub.company_id AND
                 cr.date_start <= COALESCE(sub.date, NOW()) AND
                 (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date, NOW())))
        )""" % (
                    self._table, self.env['res.currency']._select_companies_rates(),
                    self._select(), self._sub_select(), self._from(), self._group_by())
        self.env.cr.execute(query)
