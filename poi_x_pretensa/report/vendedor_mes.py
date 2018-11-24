##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting
#    autor: Nicolas Bustillos
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp.osv import fields, osv
from openerp import tools
import openerp.addons.decimal_precision as dp
import unicodedata

from lxml import etree


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


class pret_vendedor_report(osv.osv):
    _name = "pret.vendedor.report"
    _description = "Informe Vendedor por mes"
    _auto = False

    _columns = {
        'name': fields.char('Name', size=64, readonly=True),
        'partner_id': fields.many2one('res.partner', 'Cliente', readonly=True),
        'user_id': fields.many2one('res.users', 'Vendedor', readonly=True),
        'shop_id': fields.many2one('stock.warehouse', 'Sucursal', readonly=True),
        'date_order': fields.date('Fecha', readonly=True),
        'state': fields.char('Estado', size=24, readonly=True),
        'date_year': fields.char(u'Año', size=10, readonly=True),
        'date_day': fields.char(u'Día', size=10, readonly=True),
        'date_week': fields.char(u'Semana', size=8, readonly=True),
        'amount_total': fields.float('Precio de venta', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'ene_m': fields.float('Enero', digits=(16, 2), readonly=True),
        'feb_m': fields.float('Febero', digits=(16, 2), readonly=True),
        'mar_m': fields.float('Marzo', digits=(16, 2), readonly=True),
        'abr_m': fields.float('Abril', digits=(16, 2), readonly=True),
        'may_m': fields.float('Mayo', digits=(16, 2), readonly=True),
        'jun_m': fields.float('Junio', digits=(16, 2), readonly=True),
        'jul_m': fields.float('Julio', digits=(16, 2), readonly=True),
        'ago_m': fields.float('Agosto', digits=(16, 2), readonly=True),
        'sep_m': fields.float('Septiembre', digits=(16, 2), readonly=True),
        'oct_m': fields.float('Octubre', digits=(16, 2), readonly=True),
        'nov_m': fields.float('Noviembre', digits=(16, 2), readonly=True),
        'dec_m': fields.float('Diciembre', digits=(16, 2), readonly=True),
        'total': fields.float('Total anual', digits=(16, 2), readonly=True),
        'ene_p': fields.float('%', digits=(16, 1), readonly=True),
        'feb_p': fields.float('%', digits=(16, 1), readonly=True),
        'mar_p': fields.float('%', digits=(16, 1), readonly=True),
        'abr_p': fields.float('%', digits=(16, 1), readonly=True),
        'may_p': fields.float('%', digits=(16, 1), readonly=True),
        'jun_p': fields.float('%', digits=(16, 1), readonly=True),
        'jul_p': fields.float('%', digits=(16, 1), readonly=True),
        'ago_p': fields.float('%', digits=(16, 1), readonly=True),
        'sep_p': fields.float('%', digits=(16, 1), readonly=True),
        'oct_p': fields.float('%', digits=(16, 1), readonly=True),
        'nov_p': fields.float('%', digits=(16, 1), readonly=True),
        'dec_p': fields.float('%', digits=(16, 1), readonly=True),
    }
    _order = 'total'

    def fields_view_get(self, cr, uid, view_id=None, view_type='search', context=None, toolbar=False, submenu=False):
        if view_type == 'search':
            cr.execute("REFRESH MATERIALIZED VIEW pret_vendedor_report;")
        res = super(pret_vendedor_report, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
        return res

    def init(self, cr):
        #tools.sql.drop_view_if_exists(cr, 'pret_vendedor_report')
        query_to_exe = '''DROP MATERIALIZED VIEW IF EXISTS pret_vendedor_report;
                    CREATE MATERIALIZED VIEW pret_vendedor_report as (
                select ventas.*,dims.*,(dims.ene_m + dims.feb_m + dims.mar_m + dims.abr_m + dims.may_m + dims.jun_m + dims.jul_m + dims.ago_m + dims.sep_m + dims.oct_m + dims.nov_m + dims.dec_m ) as total
                from
                    (select so.id,so.name,so.partner_id,so.user_id, so.warehouse_id as shop_id,so.state,so.create_date,so.date_order
                        ,to_char(so.date_order,'DD/MM/YYYY') as date_day,cast(extract(year from so.date_order) as char(4)) as date_year,cast(extract(year from so.date_order) as char(4)) || '/' || cast(extract(week from so.date_order) as char(3)) as date_week
                    from sale_order_line sol inner join sale_order so on sol.order_id=so.id
                    group by so.id
                    order by so.create_date) ventas
                left outer join
                    (select so.id as idd,case when extract(month from so.date_order) = 1 then sum(sol.total_dimension) else 0.0 end as ene_m,case when extract(month from so.date_order) = 1 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as ene_p
                        ,case when extract(month from so.date_order) = 2 then sum(sol.total_dimension) else 0.0 end as feb_m,case when extract(month from so.date_order) = 2 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as feb_p
                        ,case when extract(month from so.date_order) = 3 then sum(sol.total_dimension) else 0.0 end as mar_m,case when extract(month from so.date_order) = 3 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as mar_p
                        ,case when extract(month from so.date_order) = 4 then sum(sol.total_dimension) else 0.0 end as abr_m,case when extract(month from so.date_order) = 4 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as abr_p
                        ,case when extract(month from so.date_order) = 5 then sum(sol.total_dimension) else 0.0 end as may_m,case when extract(month from so.date_order) = 5 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as may_p
                        ,case when extract(month from so.date_order) = 6 then sum(sol.total_dimension) else 0.0 end as jun_m,case when extract(month from so.date_order) = 6 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as jun_p
                        ,case when extract(month from so.date_order) = 7 then sum(sol.total_dimension) else 0.0 end as jul_m,case when extract(month from so.date_order) = 7 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as jul_p
                        ,case when extract(month from so.date_order) = 8 then sum(sol.total_dimension) else 0.0 end as ago_m,case when extract(month from so.date_order) = 8 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as ago_p
                        ,case when extract(month from so.date_order) = 9 then sum(sol.total_dimension) else 0.0 end as sep_m,case when extract(month from so.date_order) = 9 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as sep_p
                        ,case when extract(month from so.date_order) = 10 then sum(sol.total_dimension) else 0.0 end as oct_m,case when extract(month from so.date_order) = 10 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as oct_p
                        ,case when extract(month from so.date_order) = 11 then sum(sol.total_dimension) else 0.0 end as nov_m,case when extract(month from so.date_order) = 11 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as nov_p
                        ,case when extract(month from so.date_order) = 12 then sum(sol.total_dimension) else 0.0 end as dec_m,case when extract(month from so.date_order) = 12 then sum(sol.total_dimension)/(mest.total)*100 else 0.0 end as dec_p

                    from sale_order_line sol inner join sale_order so on sol.order_id=so.id
                        left outer join (select extract(month from so.date_order) as mes,sum(sol.total_dimension) as total
                                from sale_order_line sol inner join sale_order so on sol.order_id=so.id
                                group by extract(month from so.date_order) order by extract(month from so.date_order)) mest on mest.mes=extract(month from so.date_order)
                    group by so.id, mest.total order by so.id) dims on dims.idd=ventas.id
                order by ventas.create_date
            )'''

        cr.execute(query_to_exe)


pret_vendedor_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
