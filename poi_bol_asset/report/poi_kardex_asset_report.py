from odoo import tools
from odoo import api, fields, models

class PoiKardexAssetReport(models.Model):
    _name = "poi.kardex.asset.report"
    _description = "Assets Analysis Depreciation"
    _auto = False

    category_id = fields.Many2one('account.asset.category', string=u'Categoría', required=False, readonly=True)
    date = fields.Date(string=u'Fecha', required=False, readonly=True)
    monto = fields.Float(string=u'Monto', required=False, readonly=True)
    concepto = fields.Char(string=u'Concepto', required=False, readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'poi_kardex_asset_report')
        self.env.cr.execute("""
            create or replace view poi_kardex_asset_report as (
                SELECT
                  row_number() over() as id, * from (
                  SELECT
                      t0.id as val_id,
                      t1.category_id,
                      t0.date_accounting             AS date,
                      CASE WHEN t0.amount_dep_act = 0 THEN
                            0
                      ELSE
                       (t1.value - (SELECT
                         SUM(av.amount_dep_per)+SUM(av.amount_dep_act)- SUM(av.amount_inc_act) AS sum_inc_act
                       FROM account_asset_value av
                         WHERE av.asset_id = t0.asset_id
                         and av.date_accounting < t0.date_accounting
                       GROUP BY av.asset_id))
                      END AS monto,
                      'A. VALOR ANTERIOR GESTIÓN'    AS concepto
                    FROM account_asset_value t0
                      INNER JOIN account_asset_asset t1 ON t1.id = t0.asset_id
                    UNION ALL
                    SELECT
                      t0.id as val_id,
                      t0.category_id             AS category_id,
                      t0.date,
                      t0.value                   AS monto,
                      'B. COMPRAS DE LA GESTIÓN' AS concepto
                    FROM account_asset_asset t0
                      INNER JOIN account_invoice t3 ON t3.id = t0.invoice_id
                    WHERE t3.type = 'in_invoice'
                    UNION ALL
                    SELECT
                      t0.id as val_id,
                      t1.category_id,
                      t0.date_accounting          AS date,
                      t0.amount_inc_act           AS monto,
                      'C. ACTUALIZACION AITB' AS concepto
                    FROM account_asset_value t0
                      INNER JOIN account_asset_asset t1 ON t1.id = t0.asset_id
                    UNION ALL
                    SELECT
                      t0.id as val_id,
                      t2.id                    AS category_id,
                      t0.date,
                      t0.credit                AS monto,
                      'D. BAJAS DE INVENTARIO' AS concepto
                    FROM account_move_line t0
                      INNER JOIN account_asset_asset t1 ON t1.name = t0.name
                      INNER JOIN account_asset_category t2 ON t2.id = t1.category_id
                      INNER JOIN account_invoice t3 ON t3.move_id = t0.move_id
                    WHERE t0.account_id = t2.account_asset_id
                          AND t3.type = 'out_invoice'
                    UNION ALL
                    SELECT
                      t0.id as val_id,
                      t1.category_id,
                      t0.date_accounting             AS date,
                      (SELECT
                         SUM(av.amount_inc_act) AS sum_inc_act
                       FROM account_asset_value av
                         WHERE av.asset_id = t0.asset_id
                         and av.date_accounting <= t0.date_accounting
                       GROUP BY av.asset_id) + t1.value as monto,
                      'E. VALOR ACTUALIZADO'         AS concepto
                    FROM account_asset_value t0
                      INNER JOIN account_asset_asset t1 ON t1.id = t0.asset_id
                    UNION ALL
                    SELECT
                      t0.id as val_id,
                      t1.category_id,
                      t0.date_accounting                      AS date,
                      t0.amount_dep_per AS monto,
                      'F. DEPRECIACION DE LA GESTION'         AS concepto
                    FROM account_asset_value t0
                      INNER JOIN account_asset_asset t1 ON t1.id = t0.asset_id
                    UNION ALL
                    SELECT
                      t0.id as val_id,
                      t1.category_id,
                      t0.date_accounting                 AS date,
                      t0.amount_dep_act                  AS monto,
                      'G. MANTENIMIENTO VALOR DEPRE ACUM.' AS concepto
                    FROM account_asset_value t0
                      INNER JOIN account_asset_asset t1 ON t1.id = t0.asset_id
                    UNION ALL
                    SELECT
                      t0.id as val_id,
                      t1.category_id,
                      t0.date_accounting                        AS date,
                      (SELECT
                         SUM(av.amount_dep_per)-SUM(av.amount_dep_act) AS sum_inc_act
                       FROM account_asset_value av
                         WHERE av.asset_id = t0.asset_id
                         and av.date_accounting <= t0.date_accounting
                       GROUP BY av.asset_id)     AS monto,
                      'I. DEPRECIACION ACUMULADA A LA GESTION.' AS concepto
                    FROM account_asset_value t0
                      INNER JOIN account_asset_asset t1 ON t1.id = t0.asset_id

                    UNION ALL
                    SELECT
                      t0.id as val_id,
                      t1.category_id,
                      t0.date_accounting                AS date,
                      (t1.value + (SELECT
                         SUM(av.amount_inc_act)-SUM(av.amount_dep_per)-SUM(av.amount_dep_act) AS sum_inc_act
                       FROM account_asset_value av
                         WHERE av.asset_id = t0.asset_id
                         and av.date_accounting <= t0.date_accounting
                       GROUP BY av.asset_id)) AS monto,
                      'J. VALOR NETO.'                    AS concepto
                    FROM account_asset_value t0
                      INNER JOIN account_asset_asset t1 ON t1.id = t0.asset_id
                  ) as foo
        )""")
