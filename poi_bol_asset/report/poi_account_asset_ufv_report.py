from odoo import tools
from odoo import api, fields, models


class PoiAccountAssetUfvReport(models.Model):
    _name = "poi.account.asset.ufv.report"
    _description = "Análisis depreciacion UFV"
    _auto = False
    category_id = fields.Many2one('account.asset.category', string=u'Categoría de activo', required=False, readonly=True)
    code = fields.Char(string='Codigo', required=False, readonly=True)
    name = fields.Char(string='Detalle', required=False, readonly=True)
    asset_id = fields.Many2one('account.asset.asset', string='Activo', required=False, readonly=True)
    fecha_compra = fields.Date(string='Fecha de adquisición', required=False, readonly=True)
    valor_compra = fields.Float(string='Valor de Compra', required=False, readonly=True)
    date_accounting = fields.Date(string='Fecha Contabilizado', required=False, readonly=True)
    month = fields.Char(string='Mes', required=False, readonly=True)
    valor_fecha = fields.Float(string='Valor a la fecha', required=False, readonly=True)
    ufv_final = fields.Char(string=u'UFV Final', required=False, readonly=True)
    ufv_inicial = fields.Char(string=u'UFV Inicial', required=False, readonly=True)
    amount_inc_act = fields.Float(string=u'UFV actualización', required=False, readonly=True)
    valor_actualizado = fields.Float(string=u'Valor Actualizado', required=False, readonly=True)
    amount_dep_per = fields.Float(string=u'Deprecición Gestión', required=False, readonly=True)
    dep_acum_mes_anterior = fields.Float(string='Dep. Acum. Mes Anterior', required=False, readonly=True)
    amount_dep_act = fields.Float(string='Actualización Dep. Acum.', required=False, readonly=True)
    dep_acum_actualizado = fields.Float(string='Depreciación Acumulada Actualizado', required=False, readonly=True)
    total_dep = fields.Float(string='Total Depreciación', required=False, readonly=True)
    valor_neto = fields.Float(string='Valor Neto', required=False, readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'poi_account_asset_ufv_report')
        self.env.cr.execute("""
            create or replace view poi_account_asset_ufv_report as (
                SELECT row_number() over() as id, *, (foo.amount_dep_per + foo.dep_acum_actualizado) as total_dep,
                  foo.valor_actualizado - (foo.amount_dep_per + foo.dep_acum_actualizado)  as valor_neto
                FROM (SELECT
                        t1.category_id,
                        t1.code,
                        t1.name,
                        t1.id as asset_id,
                        t1.date as fecha_compra,
                        t1.value as valor_compra,
                        t0.date_accounting,
                        to_char(t0.date_accounting,'MM') as month,
                        (ahist.sum_inc_act - t0.amount_inc_act) + t1.value                                                    AS valor_fecha,
                        (SELECT r0.rate
                         FROM res_currency_rate r0
                           INNER JOIN res_currency r1 ON r1.id = r0.currency_id
                         WHERE r1.name = 'UFV' AND to_char(r0.name, 'YYYY-MM-dd') =
                                                   t0.date_accounting :: TEXT)                                                AS ufv_final,
                        CASE WHEN t1.date BETWEEN TO_DATE(t0.date_accounting :: TEXT, 'YYYY-MM-01') :: DATE AND t0.date_accounting
                          THEN
                            (SELECT r0.rate
                             FROM res_currency_rate r0
                               INNER JOIN res_currency r1 ON r1.id = r0.currency_id
                             WHERE r1.name = 'UFV' AND to_char(r0.name, 'YYYY-MM-dd') = t1.date :: TEXT)
                        ELSE
                          (SELECT r0.rate
                           FROM res_currency_rate r0
                             INNER JOIN res_currency r1 ON r1.id = r0.currency_id
                           WHERE r1.name = 'UFV' AND
                                 to_char(r0.name, 'YYYY-MM-dd') = TO_DATE(t0.date_accounting :: TEXT, 'YYYY-MM-01') :: TEXT)
                        END                                                                                                   AS ufv_inicial,
                        t0.amount_inc_act,
                        ((ahist.sum_inc_act - t0.amount_inc_act) + t1.value) +
                        t0.amount_inc_act                                                                                     AS valor_actualizado,
                        t0.amount_dep_per,
                        (ahist.sum_dep_per - t0.amount_dep_per) + (ahist.sum_dep_act -
                                                                   t0.amount_dep_act)                                         AS dep_acum_mes_anterior,
                        t0.amount_dep_act,
                        (ahist.sum_dep_per - t0.amount_dep_per) + (ahist.sum_dep_act - t0.amount_dep_act) +
                        t0.amount_dep_act                                                                                     AS dep_acum_actualizado
                      FROM account_asset_value t0
                        INNER JOIN account_asset_asset t1 ON t1.id = t0.asset_id
                        LEFT OUTER JOIN (SELECT
                                           av.asset_id,
                                           SUM(av.amount_inc_act)    sum_inc_act,
                                           SUM(av.amount_dep_per) AS sum_dep_per,
                                           SUM(av.amount_dep_act) AS sum_dep_act
                                         FROM account_asset_value av
                                         GROUP BY av.asset_id
                                        ) ahist ON ahist.asset_id = t0.asset_id
                        ) AS foo

        )""")
