from odoo import models, fields, api, _, tools
from datetime import datetime
import time
import odoo.addons.decimal_precision as dp
from odoo.osv import expression

class TrafficAnalysis(models.Model):
    _name = 'traffic.analysis'
    _description = 'Reporte de Analisis de Trafico de Clietes'
    _auto = False

    type0 = fields.Char('Tipo de Servicio')
    type = fields.Char('Venta o Motivo de Visita')
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen')
    date = fields.Datetime('Fecha')
    user_id = fields.Many2one('res.users', 'Vendedor')
    count_s = fields.Integer('Total Servicios')
    count_v = fields.Integer('Total Ventas')
    proccess = fields.Char('Proceso')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):

        self.env.cr.execute("REFRESH MATERIALIZED VIEW traffic_analysis");

        res = super(TrafficAnalysis, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        return res


    def _select(self):

        select_str ="""
            select
            	'SERVICIO' as type0,
            	tr.name as type,
            	t.date,
            	t.user_id2,
            	t.warehouse_id,
            	'1'::int as count_s,
            	'0'::int as count_v,
            	'complete' as proccess
            from
            	crm_traffic t
            	left join crm_traffic_reason tr on tr.id = t.reason_id

            where
            	report = True
            union all
            select
            	'VENTAS' as type0,
            	'INICIATIVAS' as type,
            	t.date,
            	t.user_id2,
            	t.warehouse_id,
            	'0'::int as count_s,
            	'1'::int as count_v,
            	'complete' as proccess
            from
            	crm_traffic t
            	left join crm_traffic_reason tr on tr.id = t.reason_id
            	left join crm_lead l on l.traffic_id = t.id
            	left join sale_order so on so.opportunity_id = l.id

            where
            	report = True and l.id is not null
            union all
            select
            	'VENTAS' as type0,
            	'OPORTUNIDADES' as type,
            	t.date,
            	t.user_id2,
            	t.warehouse_id,
            	'0'::int as count_s,
            	'1'::int as count_v,
            	'complete' as proccess

            from
            	crm_traffic t
            	left join crm_traffic_reason tr on tr.id = t.reason_id
            	left join crm_lead l on l.traffic_id = t.id
            	left join sale_order so on so.opportunity_id = l.id

            where
            	report = True and l.id is not null and l.type = 'opportunity'
            union all
            select
            	'VENTAS' as type0,
            	'COTIZACIONES' as type,
                so.date_order,
            	so.user_id,
            	so.warehouse_id,
            	'0'::int as count_s,
            	'1'::int as count_v,
            	'complete' as proccess
            from
            	crm_traffic t
            	left join crm_traffic_reason tr on tr.id = t.reason_id
            	left join crm_lead l on l.traffic_id = t.id
            	left join sale_order so on so.opportunity_id = l.id

            where
            	report = True and so.id is not null
            union all
            select
            	'VENTAS' as type0,
            	'INICIATIVAS' as type,
            	l.create_date,
            	l.user_id,
            	l.warehouse_id,
            	'0'::int as count_s,
            	'1'::int as count_v,
            	'no_complete' as proccess
            from
            	crm_lead l
            where
            	l.traffic_id is null and  not l.type = 'opportunity'
            union all
            select
            	'VENTAS' as type0,
            	'OPORTUNIDADES' as type,
            	l.create_date,
            	l.user_id,
            	l.warehouse_id,
            	'0'::int as count_s,
            	'1'::int as count_v,
            	'no_complete' as proccess
            from
            	crm_lead l
            where
            	l.traffic_id is null and l.type = 'opportunity'
            union all
            select
            	'VENTAS' as type0,
            	'COTIZACIONES' as type,
            	s.order_date,
            	s.user_id,
            	s.warehouse_id,
            	'0'::int as count_s,
            	'1'::int as count_v,
            	'no_complete' as proccess

            from
            	sale_order s

            where
            	s.opportunity_id is null

            union all
            select
            	'VENTAS' as type0,
            	'COTIZACIONES' as type,
            	so.date_order,
            	so.user_id,
            	so.warehouse_id,
            	'0'::int as count_s,
            	'1'::int as count_v,
            	'complete' as proccess
            from
                	crm_lead l
                	left join sale_order so on so.opportunity_id = l.id
    	    where
    		l.traffic_id is NULL and so.id is not null

        """
        return select_str

    @api.model_cr
    def init(self):
        table = "traffic_analysis"
        self.env.cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = 'traffic_analysis';
            """)
        vista =self.env.cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                self.env.cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS traffic_analysis;
            CREATE MATERIALIZED VIEW traffic_analysis as (
            SELECT row_number() over() as id, *
                FROM(%s) as asd
            )""" % (self._select()))
