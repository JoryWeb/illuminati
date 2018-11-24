from odoo import tools
from odoo import api, fields, models


class PoiAssetAssetReport(models.Model):
    _name = "poi.asset.asset.report"
    _description = "Assets Analysis Depreciation"
    _auto = False

    activo = fields.Char(string='Activo', required=False, readonly=True)
    value = fields.Float(string='Valor de Compra', required=False, readonly=True)
    cat_activo = fields.Char(string='Categoría Activo', required=False, readonly=True)
    asset_id = fields.Many2one('account.asset.asset', string='Activo Maestro', required=False, readonly=True)
    amount_dep_per = fields.Float(string=u'Depreciación Periodo', required=False, readonly=True)
    amount_inc_act = fields.Float(string=u'Incremento de Valor', required=False, readonly=True)
    amount_dep_act = fields.Float(string=u'Actualización Depreciación Acumulada', required=False, readonly=True)
    date_accounting = fields.Date(string=u'Fecha Contabilizada', required=False, readonly=True)
    date_trans = fields.Date(string=u'Fecha Transacción', required=False, readonly=True)
    periodo = fields.Char(string=u'Periodo', required=False, readonly=True)
    anio = fields.Char(string=u'Gestión', required=False, readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'poi_asset_asset_report')
        self.env.cr.execute("""
            create or replace view poi_asset_asset_report as (
                SELECT
                  row_number() over() as id,
                  t1.name as activo,
                  t1.value,
                  t2.name as cat_activo,
                  t0.asset_id,
                  t0.amount_dep_per,
                  t0.amount_inc_act,
                  t0.amount_dep_act,
                  t0.date_accounting,
                  t0.date_trans,
                  to_char(t0.date_accounting,'MM-YYYY') as periodo,
                  to_char(t0.date_accounting,'YYYY') as anio
                FROM account_asset_value t0
                  INNER JOIN account_asset_asset t1 ON t1.id = t0.asset_id
                  INNER JOIN account_asset_category t2 ON t2.id = t1.category_id
        )""")
