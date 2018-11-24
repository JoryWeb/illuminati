# -*- encoding: utf-8 -*-
##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2017 Poiesis Consulting (<http://www.poiesisconsulting.com>). All Rights Reserved.
#    Autor: Miguel Angel Callisaya Mamani
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from odoo import api, fields, models, _

LCV_QUERY_INDIVIDUAL = """
    select *,(monto + descuento) as importe ,(monto + descuento - exento - ice) as subtotal_c,(monto + descuento - ice - exporta - exento) as subtotal_v,(ice + exento) as monto_nosujeto
    FROM
    (
        SELECT
          'in'                                                      AS case,
          '1'                                                       AS spec,
          '1'                                                       AS tipo_com,
          CASE WHEN ai.estado_fac = 'A'
            THEN '0'
          ELSE ai.nit END                                           AS nit,
          CASE WHEN ai.estado_fac = 'A'
            THEN 'ANULADA'
          ELSE coalesce(ai.razon, '') END                           AS razon,
          ai.cc_nro,
          (REGEXP_REPLACE(ai.cc_nro, '[^0-9]+', '', 'g')) :: BIGINT AS cc_nro_int,
          ai.imp_pol,
          ai.cc_aut,
          to_char(ai.date_invoice, 'DD/MM/YYYY')                    AS cc_fecha,
          ai.date_invoice                                           AS date_invoice,
          Extract('year' FROM ai.date_invoice)                      AS year_invoice,
          Extract('month' FROM ai.date_invoice)                     AS month_invoice,
          CASE WHEN estado_fac = 'A'
            THEN 0
          ELSE round((ai.iva / 13 * 100) + ai.ice, 2) END AS monto,
          CASE WHEN estado_fac = 'A'
            THEN 0
          ELSE round(coalesce(ai.ice, 0), 2) END               AS ice,
          CASE WHEN estado_fac = 'A'
            THEN 0
          ELSE round(coalesce(exento, 0), 2) END               AS exento,
          0                                                         AS exporta,
          CASE WHEN estado_fac = 'A'
            THEN 0
          ELSE round(coalesce(sum_desc, 0), 2) END                  AS descuento,
          CASE WHEN estado_fac = 'A'
            THEN 0
          ELSE round(ai.iva / 13 * 100, 2) END                 AS monto_neto,
          CASE WHEN estado_fac = 'A'
            THEN 0
          ELSE round(ai.iva, 2) END                            AS monto_iva,
          CASE WHEN estado_fac = 'A'
            THEN '0'
          ELSE coalesce(cc_cod, '0') END                            AS cc_cod,
          0                                                         AS cc_dos,
          ''                                                        AS cc_dos_name,
          state,
          coalesce(tipo_com, '1')                                   AS tipo_com_val,
          estado_fac,
          estado_fac                                                AS estado_fac_val,
          ai.company_id,
          ai.id                                                     AS res_id,
          'account.invoice' :: VARCHAR                              AS res_obj,
          ai.number                                                 AS res_name,
          'Factura DUI' :: VARCHAR                                  AS res_type,
          coalesce(dos.warehouse_id, 0)                             AS shop_id,
          ''                                                        AS origen_cc_fecha,
          NULL :: DATE                                              AS origen_date_invoice,
          '0'                                                       AS origen_cc_nro,
          '0'                                                       AS origen_cc_aut,
          0                                                         AS origen_monto,
          ai.create_uid                                             AS user_id,
          ai.move_id                                                AS move_id
        FROM account_invoice ai
          LEFT OUTER JOIN poi_bol_base_cc_dosif dos ON dos.id = ai.cc_dos
        WHERE ai.tipo_fac = '12' AND (state IN ('open', 'paid') OR (state IN ('draft', 'cancel') AND estado_fac = 'A')) AND
              estado_fac = 'V'
    ) as lcv order by lcv.cc_nro_int,lcv.date_invoice
        """


class poi_lcv_import(models.Model):
    _name = "poi_bol.import.lcv.report"

    def init(self, cr, select=False, mlc=False, mlr=False):
        #Al momento de iniciar el addon SOLO se crea una Vista SQL que contiene el query individual de este modulo unicamente. Esta vista no estara vinculada a este objeto. Sera incorporada a la vista general LCV desde el modulo poi_bol_base
        table = "poi_bol_lcv_report_imports"

        individual_query_to_exe = LCV_QUERY_INDIVIDUAL

        cr.execute("""

            DROP VIEW IF EXISTS %s CASCADE;
            CREATE VIEW %s as ((
            SELECT *
                FROM ((
                    %s
                )) as base
            ))""" % (table, table, individual_query_to_exe))

