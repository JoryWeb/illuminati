# -*- encoding: utf-8 -*-
##############################################################################
#
#    Poiesis Consulting, odoo Partner
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
    select *,(monto + descuento) as importe ,(monto + descuento - exento) as subtotal_c,(monto + descuento - ice - exporta - exento) as subtotal_v,(ice + exento) as monto_nosujeto
    FROM
    (
        select 'out' as case, '3' as spec,
                    NULL as tipo_com,
                    case when estado_fac = 'A' then '0' else po.nit end as nit,
                    case when estado_fac = 'A' then 'ANULADA' else coalesce(po.razon,'') end as razon,
                    po.cc_nro,
                    (REGEXP_REPLACE(po.cc_nro, '[^0-9]+', '', 'g'))::bigint as cc_nro_int,
                    '0' as imp_pol,po.cc_aut,
                    to_char(cast(po.date_order - interval '4h' as date),'DD/MM/YYYY') as cc_fecha,
                    cast(po.date_order - interval '4h' as date) as date_invoice,
                    Extract('year' from cast(po.date_order - interval '4h' as date)) as year_invoice,
                    Extract('month' from cast(po.date_order - interval '4h' as date)) as month_invoice,
                    case when po.estado_fac = 'A' then 0 else round(cast(po.total_bs as numeric),2) end as monto,
                    case when po.estado_fac = 'A' then 0 else round(coalesce(po.ice,0),2) end as ice,
                    case when po.estado_fac = 'A' then 0 else round(coalesce(po.exento,0),2) end as exento, 0 as exporta,
                    round(coalesce(d.discount,0.0),2) as descuento,
                    case when po.estado_fac = 'A' then 0 else round(cast(po.total_bs - coalesce(po.ice,0) - coalesce(po.exento,0) as numeric),2) end as monto_neto,
                    case when po.estado_fac = 'A' then 0 else round(cast(po.tax_bs as numeric),2) end as monto_iva,coalesce(po.cc_cod,'0') as cc_cod,coalesce(po.cc_dos,0) as cc_dos, coalesce(dos.name,'') as cc_dos_name, 
                    po.state,
                    NULL as tipo_com_val,
                    po.estado_fac,
                    po.estado_fac as estado_fac_val,
                    po.company_id,
                    po.id as res_id,
                    'pos.order'::varchar as res_obj,
                    coalesce(dos.warehouse_id,0) as shop_id,
                    '' as origen_cc_fecha,
                    NULL::DATE as origen_date_invoice,
                    '0' as origen_cc_nro, 
                    '0' as origen_cc_aut, 
                    0 as origen_monto,
                    po.create_uid as user_id,
                    0 as move_id 
                from pos_order po 
                inner join pos_session ps on ps.id=po.session_id 
                left outer join account_bank_statement abs on abs.id=ps.cash_register_id 
                left outer join poi_bol_base_cc_dosif dos on dos.id=po.cc_dos
                left join (SELECT order_id, sum((price_unit *qty)*(discount/100)) as discount FROM pos_order_line GROUP BY order_id) as d ON d.order_id = po.id
                where (po.state in ('done','paid','invoiced') 
                       or (po.state in ('draft','cancel') and po.estado_fac = 'A')) 
                       and po.estado_fac != 'na'
    ) as lcv order by lcv.cc_nro_int,lcv.date_invoice
        """


class poi_lcv_import(models.Model):
    _inherit = "poi_bol.lcv.report"

    def init(self, cr, select=False, mlc=False, mlr=False):
        #Al momento de iniciar el addon SOLO se crea una Vista SQL que contiene el query individual de este modulo unicamente. Esta vista no estara vinculada a este objeto. Sera incorporada a la vista general LCV desde el modulo poi_bol_base
        table = "poi_bol_lcv_report_pos"

        individual_query_to_exe = LCV_QUERY_INDIVIDUAL

        cr.execute("""

            DROP VIEW IF EXISTS %s CASCADE;
            CREATE VIEW %s as ((
            SELECT *
                FROM ((
                    %s
                )) as base
            ))""" % (table, table, individual_query_to_exe))

