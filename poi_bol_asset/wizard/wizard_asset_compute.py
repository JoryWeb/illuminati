from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import time
import calendar


class AssetDepreciationUfvWizard(models.TransientModel):
    _name = 'asset.depreciation.ufv.wizard'
    _description = 'Asistente de depreciacion y actualizacion UFV'

    @api.model
    def _prev_month_m(self):
        today = date.today()
        first = today.replace(day=1)
        lastMonth = first - timedelta(days=1)

        return lastMonth.strftime("%m")

    @api.model
    def _prev_month_y(self):
        today = date.today()
        first = today.replace(day=1)
        lastMonth = first - timedelta(days=1)

        return int(lastMonth.strftime("%Y"))

    date_transaction = fields.Date('Fecha Transacción', required=True, default=fields.Date.context_today,
                                   help="Choose the period for which you want to automatically post the depreciation lines of running assets")
    month = fields.Selection(
        [('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'), ('05', 'Mayo'), ('06', 'Junio'),
         ('07', 'Julio'), ('08', 'Agosto'), ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'),
         ('12', 'Diciembre')],
        string='Mes', required=True, default=_prev_month_m)
    year = fields.Integer(u'Año', size=4, required=True, default=_prev_month_y)

    # date_prev = fields.Date('Anterior fecha de ejecución', required=True, help="Muestra la última fecha de ejecución según registros globales")
    category_id = fields.Many2one('account.asset.category', string='Category')
    journal_id = fields.Many2one('account.journal', string='Diario')

    @api.multi
    def asset_compute(self):
        self.ensure_one()
        context = self._context
        # ToDo  !!!!!!!  check assets that have exeeded time or value... update State!!!
        head = self.env['account.asset.value.header']
        last_date = head.sudo().search_read([], ['date_trans'], order='date_trans desc', limit=1)
        ufv_id = self.env['ir.model.data'].xmlid_to_res_id('poi_bol_base.res_currency_ufv', raise_if_not_found=True)
        val_days = calendar.monthrange(int(self.year), int(self.month))
        date_init_ufv = datetime(int(self.year), int(self.month), 1) - relativedelta(days=1)
        date_end_ufv = datetime(int(self.year), int(self.month), val_days[1])
        date_str_init_ufv = date_init_ufv.strftime('%Y-%m-%d')
        date_str_end_ufv = date_end_ufv.strftime('%Y-%m-%d')
        ufv_ini = 0.0
        ufv_fin = 0.0
        # Obtner indice de valor en moneda UFV según el rango de fechas seleccionado
        self._cr.execute("""
                            SELECT rate FROM res_currency_rate WHERE currency_id = %s and to_char(name,'YYYY-MM-dd') = %s
                           """, (ufv_id, date_str_init_ufv,))
        res = self._cr.fetchall()
        for line in res:
            ufv_ini = line[0]

        self._cr.execute("""
                            SELECT rate FROM res_currency_rate WHERE currency_id = %s and to_char(name,'YYYY-MM-dd') = %s
                           """, (ufv_id, date_str_end_ufv,))
        res = self._cr.fetchall()
        for line in res:
            ufv_fin = line[0]
        reference = 'Asiento Contable Activos'
        # ufv_end = company_currency.compute(1, ufv_currency, round=False)
        if not ufv_ini or ufv_fin == 0:
            raise ValidationError(
                _('No se ha configurado el tipo de cambio de la Moneda UFV para la periodo seleccionado'))

        # Validar que todas las categorias tengan configurado la cuenta AITB
        asset_categ = self.env['account.asset.category'].search([('account_aitb_asset_id', '=', False)])
        for asset_cat in asset_categ:
            raise ValidationError(
                _('Configure la cuenta AITB para la categoría de activo %s') % (asset_cat.name))
        # Verificar que los activos ya han sido depreciados en un mes respectivo
        ids_asset = []
        asset_value = self.env['account.asset.value'].search([('date_accounting', '=', date_str_end_ufv)])
        for asset in asset_value:
            ids_asset.append(asset.asset_id.id)

        # Validar que los activos esten con un mes de diferencia para depreciar
        self._cr.execute("""select * from (
                  SELECT
                    *,
                    date_part('month', age('%s'::DATE + interval '1' day, tmp.date_accounting::DATE + interval '1' day)) AS meses_diff
                  FROM (
                         SELECT
                           av.asset_id,
                           av.date_accounting,
                           row_number()
                           OVER (PARTITION BY av.asset_id
                             ORDER BY av.date_accounting DESC) AS rownum
                         FROM account_asset_value av
                       ) tmp
                  WHERE rownum < 2
                ) as foo
                where meses_diff != 1""" % (date_str_end_ufv))
        res = self._cr.dictfetchall()
        for r in res:
            ids_asset.append(r['asset_id'])

        ids_asset = list(set(ids_asset))
        # Puede que solo algunos activos no tengan que generarse se filtran en este lugar
        if ids_asset:
            self._cr.execute("""
                        DO $$
                            DECLARE
                              ufv_ini    DECIMAL := %s;
                              ufv_end    DECIMAL := %s;
                              date_trans DATE := %s;
                              uid        INTEGER := %s;
                              date_accounting DATE := %s;
                              date_init DATE := %s;
                              ufv_id INTEGER := %s;
                            BEGIN
                              INSERT INTO account_asset_value (create_uid, write_uid, create_date, write_date, asset_id, value_type, time_delta, date_trans, date_accounting, amount_dep_per, amount_inc_act, amount_dep_act)
                                SELECT
                                  uid                                                                                                      AS create_uid,
                                  uid                                                                                                      AS write_uid,
                                  CURRENT_TIMESTAMP                                                                                        AS create_date,
                                  CURRENT_TIMESTAMP                                                                                        AS write_date,
                                  aa.id :: INTEGER                                                                                         AS asset_id,
                                  'DEPR' :: VARCHAR                                                                                        AS value_type,
                                  -1 :: INTEGER                                                                                            AS time_delta,
                                  date_trans                                                                                               AS date_trans,
                                  date_accounting                                                                                          AS date_accounting,
                                    CASE WHEN aa.date BETWEEN date_init AND date_accounting THEN
                                        ((aa.value + COALESCE(ahist.sum_inc_act, 0)) :: DECIMAL * (ufv_end / (SELECT rate FROM res_currency_rate
                                        WHERE currency_id = ufv_id and to_char(name,'YYYY-MM-dd') = aa.date::TEXT))) / (
                                        CASE WHEN COALESCE(aa.method_number, 0) = 0
                                          THEN 1
                                        ELSE aa.method_number END)
                                      ELSE
                                      ((aa.value + COALESCE(ahist.sum_inc_act, 0)) :: DECIMAL * (ufv_end / ufv_ini)) / (
                                        CASE WHEN COALESCE(aa.method_number, 0) = 0
                                          THEN 1
                                        ELSE aa.method_number END)
                                      END AS amount_dep_per,
                                  --(aa.value + COALESCE(ahist.sum_inc_act, 0) - COALESCE(ahist.sum_dep_per, 0) -
                                  --COALESCE(ahist.sum_dep_act, 0)) :: DECIMAL * ((ufv_end / ufv_ini) -
                                  --                                               1)                                                        AS amount_inc_act,
                                    CASE WHEN aa.date BETWEEN date_init AND date_accounting THEN
                                      ((ufv_end / (SELECT rate FROM res_currency_rate
                                        WHERE currency_id = ufv_id and to_char(name,'YYYY-MM-dd') = aa.date::TEXT)) - 1) * (aa.value + COALESCE(ahist.sum_inc_act, 0))
                                      ELSE
                                      ((ufv_end / ufv_ini) - 1) * (aa.value + COALESCE(ahist.sum_inc_act, 0))
                                        END AS amount_inc_act,

                                    CASE WHEN aa.date BETWEEN date_init AND date_accounting THEN
                                      (COALESCE(ahist.sum_dep_per, 0) + COALESCE(ahist.sum_dep_act, 0)) :: DECIMAL * ((ufv_end / (SELECT rate FROM res_currency_rate
                                        WHERE currency_id = ufv_id and to_char(name,'YYYY-MM-dd') = aa.date::TEXT)) -
                                                                                                                      1)
                                      ELSE
                                      (COALESCE(ahist.sum_dep_per, 0) + COALESCE(ahist.sum_dep_act, 0)) :: DECIMAL * ((ufv_end / ufv_ini) -
                                                                                                                      1)
                                        END AS amount_dep_act
                                FROM account_asset_asset aa
                                  INNER JOIN account_asset_category ac ON aa.category_id = ac.id
                                  LEFT OUTER JOIN (SELECT
                                                     av.asset_id,
                                                     SUM(av.amount_inc_act)    sum_inc_act,
                                                     SUM(av.amount_dep_per) AS sum_dep_per,
                                                     SUM(av.amount_dep_act) AS sum_dep_act
                                                   FROM account_asset_value av
                                                   GROUP BY av.asset_id
                                                  ) ahist ON ahist.asset_id = aa.id
                                WHERE aa.state = 'open'
                                and aa.date <= date_accounting
                                and aa.id NOT IN %s;
                            END $$;
                            """,
                             (ufv_ini, ufv_fin, self.date_transaction, self._uid, date_str_end_ufv, date_str_init_ufv, ufv_id, tuple(ids_asset)))
        else:
            self._cr.execute("""
                        DO $$
                            DECLARE
                              ufv_ini    DECIMAL := %s;
                              ufv_end    DECIMAL := %s;
                              date_trans DATE := %s;
                              uid        INTEGER := %s;
                              date_accounting DATE := %s;
                              date_init DATE := %s;
                              ufv_id INTEGER := %s;
                            BEGIN
                              INSERT INTO account_asset_value (create_uid, write_uid, create_date, write_date, asset_id, value_type, time_delta, date_trans, date_accounting, amount_dep_per, amount_inc_act, amount_dep_act)
                                SELECT
                                  uid                                                                                                      AS create_uid,
                                  uid                                                                                                      AS write_uid,
                                  CURRENT_TIMESTAMP                                                                                        AS create_date,
                                  CURRENT_TIMESTAMP                                                                                        AS write_date,
                                  aa.id :: INTEGER                                                                                         AS asset_id,
                                  'DEPR' :: VARCHAR                                                                                        AS value_type,
                                  -1 :: INTEGER                                                                                            AS time_delta,
                                  date_trans                                                                                               AS date_trans,
                                  date_accounting                                                                                          AS date_accounting,
                                  CASE WHEN aa.date BETWEEN date_init AND date_accounting THEN
                                        ((aa.value + COALESCE(ahist.sum_inc_act, 0)) :: DECIMAL * (ufv_end / (SELECT rate FROM res_currency_rate
                                        WHERE currency_id = ufv_id and to_char(name,'YYYY-MM-dd') = aa.date::TEXT))) / (
                                        CASE WHEN COALESCE(aa.method_number, 0) = 0
                                          THEN 1
                                        ELSE aa.method_number END)
                                      ELSE
                                      ((aa.value + COALESCE(ahist.sum_inc_act, 0)) :: DECIMAL * (ufv_end / ufv_ini)) / (
                                        CASE WHEN COALESCE(aa.method_number, 0) = 0
                                          THEN 1
                                        ELSE aa.method_number END)
                                      END AS amount_dep_per,
                                  --(aa.value + COALESCE(ahist.sum_inc_act, 0) - COALESCE(ahist.sum_dep_per, 0) -
                                  --COALESCE(ahist.sum_dep_act, 0)) :: DECIMAL * ((ufv_end / ufv_ini) -
                                  --                                               1)                                                        AS amount_inc_act,
                                    CASE WHEN aa.date BETWEEN date_init AND date_accounting THEN
                                      ((ufv_end / (SELECT rate FROM res_currency_rate
                                        WHERE currency_id = ufv_id and to_char(name,'YYYY-MM-dd') = aa.date::TEXT)) - 1) * (aa.value + COALESCE(ahist.sum_inc_act, 0))
                                      ELSE
                                      ((ufv_end / ufv_ini) - 1) * (aa.value + COALESCE(ahist.sum_inc_act, 0))
                                        END AS amount_inc_act,

                                    CASE WHEN aa.date BETWEEN date_init AND date_accounting THEN
                                      (COALESCE(ahist.sum_dep_per, 0) + COALESCE(ahist.sum_dep_act, 0)) :: DECIMAL * ((ufv_end / (SELECT rate FROM res_currency_rate
                                        WHERE currency_id = ufv_id and to_char(name,'YYYY-MM-dd') = aa.date::TEXT)) -
                                                                                                                      1)
                                      ELSE
                                      (COALESCE(ahist.sum_dep_per, 0) + COALESCE(ahist.sum_dep_act, 0)) :: DECIMAL * ((ufv_end / ufv_ini) -
                                                                                                                      1)
                                        END AS amount_dep_act
                                FROM account_asset_asset aa
                                  INNER JOIN account_asset_category ac ON aa.category_id = ac.id
                                  LEFT OUTER JOIN (SELECT
                                                     av.asset_id,
                                                     SUM(av.amount_inc_act)    sum_inc_act,
                                                     SUM(av.amount_dep_per) AS sum_dep_per,
                                                     SUM(av.amount_dep_act) AS sum_dep_act
                                                   FROM account_asset_value av
                                                   GROUP BY av.asset_id
                                                  ) ahist ON ahist.asset_id = aa.id
                                WHERE aa.state = 'open'
                                and aa.date <= date_accounting;
                            END $$;
                            """,
                             (ufv_ini, ufv_fin, self.date_transaction, self._uid, date_str_end_ufv, date_str_init_ufv, ufv_id))

        self._cr.commit()
        # ToDo: Generar Asiento

        # self._cr.execute("""
        #            SELECT id, asset_id, amount_inc_act, amount_dep_per, amount_dep_act FROM account_asset_value WHERE date_accounting = '""" + date_str_end_ufv + """' and move_id ISNULL""")
        self._cr.execute("""SELECT
          t2.company_id,
          t2.account_analytic_id,
          t2.account_asset_id,
          t2.account_income_recognition_id,
          t2.account_depreciation_id,
          t2.account_aitb_asset_id,
          t2.account_aitb_asset_util_id,
          sum(t0.amount_inc_act) as amount_inc_act,
          sum(t0.amount_dep_per) as amount_dep_per,
          sum(t0.amount_dep_act) as amount_dep_act
        FROM account_asset_value t0
          inner join account_asset_asset t1 on t1.id = t0.asset_id
          inner join account_asset_category t2 on t2.id = t1.category_id
        WHERE t0.date_accounting = '""" + date_str_end_ufv + """' and t0.move_id ISNULL
        group by t2.company_id,
          t2.account_analytic_id,
          t2.account_asset_id,
          t2.account_income_recognition_id,
          t2.account_depreciation_id,
          t2.account_aitb_asset_id,
          t2.account_aitb_asset_util_id""")
        res = self._cr.dictfetchall()
        if res:
            move_vals = {
                'ref': reference,
                'date': date_str_end_ufv or False,
                'journal_id': self.journal_id.id,
            }
            move = self.env['account.move'].create(move_vals)
        total_asiento = 0
        for r in res:
            # Datos del activo
            # asset_data = self.env['account.asset.asset'].browse(r['asset_id'])
            # Debito
            account_debit = r['account_income_recognition_id']
            account_credit = r['account_depreciation_id']
            account_aitb = r['account_aitb_asset_id']
            account_aitb_util = r['account_aitb_asset_util_id']
            account_asset = r['account_asset_id']
            company_id = r['company_id']
            account_analytic_id = r['account_analytic_id']
            if account_analytic_id is None:
                account_analytic_id = 'NULL'
            amount_dc = r['amount_dep_per']
            amount_aitb = r['amount_inc_act']
            amount_aitb_ac = r['amount_dep_act']
            amount_ne = float(r['amount_dep_per'] * (-1))
            amount_aitb_ne = float(r['amount_inc_act'] * (-1))
            amount_aitb_ac_ne = float(r['amount_dep_act'] * (-1))
            total_asiento += amount_dc + amount_aitb + amount_aitb_ac
            # Depreciacion
            self._cr.execute(("""
                        INSERT INTO account_move_line(id,create_date,account_id,company_id,
                        date_maturity,user_type_id,blocked,create_uid,
                        amount_residual,journal_id,amount_residual_currency,debit,
                        debit_cash_basis,reconciled,credit,balance_cash_basis,
                        write_date,date,write_uid,move_id,
                        name,company_currency_id,credit_cash_basis,amount_currency,
                        balance, analytic_account_id
                        )
                        VALUES(DEFAULT,CURRENT_TIMESTAMP,%s,%s,
                              '%s',14,'false',%s,
                              0,%s,0,%s,
                              %s,'false',0,%s,
                              CURRENT_TIMESTAMP,'%s',%s,%s,
                              '%s',62,0,0,
                              %s,%s);
                        """) % (account_debit, company_id, date_str_end_ufv, self._uid,
                                self.journal_id.id, amount_dc, amount_dc, amount_dc, date_str_end_ufv, self._uid,
                                move.id,
                                u'DEPRECIACIÓN UFV', amount_dc, account_analytic_id))

            self._cr.execute(("""
                        INSERT INTO account_move_line(id,create_date,account_id,company_id,
                        date_maturity,user_type_id,blocked,create_uid,
                        amount_residual,journal_id,amount_residual_currency,debit,
                        debit_cash_basis,reconciled,credit,balance_cash_basis,
                        write_date,date,write_uid,move_id,
                        name,company_currency_id,credit_cash_basis,amount_currency,
                        balance, analytic_account_id
                        )
                        VALUES(DEFAULT,CURRENT_TIMESTAMP,%s,%s,
                              '%s',14,'false',%s,
                              0,%s,0,0,
                              0,'false',%s,%s,
                              CURRENT_TIMESTAMP,'%s',%s,%s,
                              '%s',62,%s,0,
                              %s,%s);
                        """) % (account_credit, company_id, date_str_end_ufv, self._uid,
                                self.journal_id.id, amount_dc, amount_ne, date_str_end_ufv, self._uid, move.id,
                                u'DEPRECIACIÓN UFV', amount_dc, amount_ne, account_analytic_id))
            # AITB Calculado
            self._cr.execute(("""
                                INSERT INTO account_move_line(id,create_date,account_id,company_id,
                                date_maturity,user_type_id,blocked,create_uid,
                                amount_residual,journal_id,amount_residual_currency,debit,
                                debit_cash_basis,reconciled,credit,balance_cash_basis,
                                write_date,date,write_uid,move_id,
                                name,company_currency_id,credit_cash_basis,amount_currency,
                                balance, analytic_account_id
                                )
                                VALUES(DEFAULT,CURRENT_TIMESTAMP,%s,%s,
                                      '%s',14,'false',%s,
                                      0,%s,0,%s,
                                      %s,'false',0,%s,
                                      CURRENT_TIMESTAMP,'%s',%s,%s,
                                      '%s',62,0,0,
                                      %s,%s);
                                """) % (account_asset, company_id, date_str_end_ufv, self._uid,
                                        self.journal_id.id, amount_aitb, amount_aitb, amount_aitb, date_str_end_ufv,
                                        self._uid, move.id,
                                        u'AITB', amount_aitb, account_analytic_id))

            self._cr.execute(("""
                                INSERT INTO account_move_line(id,create_date,account_id,company_id,
                                date_maturity,user_type_id,blocked,create_uid,
                                amount_residual,journal_id,amount_residual_currency,debit,
                                debit_cash_basis,reconciled,credit,balance_cash_basis,
                                write_date,date,write_uid,move_id,
                                name,company_currency_id,credit_cash_basis,amount_currency,
                                balance, analytic_account_id
                                )
                                VALUES(DEFAULT,CURRENT_TIMESTAMP,%s,%s,
                                      '%s',14,'false',%s,
                                      0,%s,0,0,
                                      0,'false',%s,%s,
                                      CURRENT_TIMESTAMP,'%s',%s,%s,
                                      '%s',62,%s,0,
                                      %s,%s);
                                """) % (account_aitb, company_id, date_str_end_ufv, self._uid,
                                        self.journal_id.id, amount_aitb, amount_aitb_ne, date_str_end_ufv, self._uid,
                                        move.id,
                                        u'AITB', amount_aitb, amount_aitb_ne, account_analytic_id))

            # Depreciacion AITB Acumulado
            if amount_aitb_ac > 0:
                self._cr.execute(("""
                                    INSERT INTO account_move_line(id,create_date,account_id,company_id,
                                    date_maturity,user_type_id,blocked,create_uid,
                                    amount_residual,journal_id,amount_residual_currency,debit,
                                    debit_cash_basis,reconciled,credit,balance_cash_basis,
                                    write_date,date,write_uid,move_id,
                                    name,company_currency_id,credit_cash_basis,amount_currency,
                                    balance, analytic_account_id
                                    )
                                    VALUES(DEFAULT,CURRENT_TIMESTAMP,%s,%s,
                                          '%s',14,'false',%s,
                                          0,%s,0,%s,
                                          %s,'false',0,%s,
                                          CURRENT_TIMESTAMP,'%s',%s,%s,
                                          '%s',62,0,0,
                                          %s,%s);
                                    """) % (account_aitb_util, company_id, date_str_end_ufv, self._uid,
                                            self.journal_id.id, amount_aitb_ac, amount_aitb_ac, amount_aitb_ac,
                                            date_str_end_ufv,
                                            self._uid, move.id,
                                            u'AITB DEPRECIACIÓN ACUMULADA', amount_aitb_ac, account_analytic_id))

                self._cr.execute(("""
                                    INSERT INTO account_move_line(id,create_date,account_id,company_id,
                                    date_maturity,user_type_id,blocked,create_uid,
                                    amount_residual,journal_id,amount_residual_currency,debit,
                                    debit_cash_basis,reconciled,credit,balance_cash_basis,
                                    write_date,date,write_uid,move_id,
                                    name,company_currency_id,credit_cash_basis,amount_currency,
                                    balance, analytic_account_id
                                    )
                                    VALUES(DEFAULT,CURRENT_TIMESTAMP,%s,%s,
                                          '%s',14,'false',%s,
                                          0,%s,0,0,
                                          0,'false',%s,%s,
                                          CURRENT_TIMESTAMP,'%s',%s,%s,
                                          '%s',62,%s,0,
                                          %s,%s);
                                    """) % (account_credit, company_id, date_str_end_ufv, self._uid,
                                            self.journal_id.id, amount_aitb_ac, amount_aitb_ac_ne,
                                            date_str_end_ufv, self._uid,
                                            move.id,
                                            u'AITB DEPRECIACIÓN ACUMULADA', amount_aitb_ac, amount_aitb_ac_ne,
                                            account_analytic_id))

        if res:
            move.amount = total_asiento
            # move.post()
        self._cr.execute("""
                           SELECT id, asset_id, amount_inc_act, amount_dep_per, amount_dep_act FROM account_asset_value WHERE date_accounting = '""" + date_str_end_ufv + """' and move_id ISNULL""")

        res2 = self._cr.dictfetchall()
        for r2 in res2:
            # Escribir la linea con move_id lo cual indica que ya se genero su asiento contable
            av_obj = self.env['account.asset.value'].browse(r2['id'])
            av_obj.move_id = move.id

        compose_form = self.env.ref('poi_bol_asset.view_asset_value_tree', False)
        domain = "[('date_accounting', '=', '%s')]" % (date_str_end_ufv)
        return {
            'name': _('Depreciacion de Activos'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.value',
            'views': [(compose_form.id, 'tree')],
            'view_id': compose_form.id,
            'domain': domain,
        }
