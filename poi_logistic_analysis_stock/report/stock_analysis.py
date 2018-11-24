##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Poiesis Consulting
#    autor: Grover Menacho
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


from openerp.osv import fields,osv
import openerp.tools
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.report import report_sxw
from openerp import models, fields, api, _, tools
import time
from datetime import datetime, timedelta

import psycopg2.extras
import psycopg2.extensions
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_READ_COMMITTED, ISOLATION_LEVEL_REPEATABLE_READ
from psycopg2.pool import PoolError

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)

class except_osv(Exception):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.args = (name, value)

service = None


class poi_report_kardex(models.Model):
    _name = 'poi.stock.kardex.analysis'
    _description = "Kardex Analysis"
    _auto = False

    price_unit = fields.Float(string='Costo del movimiento (Bs)')
    date = fields.Datetime(string='Fecha',readonly=True)
    string_date = fields.Char('Fecha', readonly=True)
    product_id= fields.Many2one('product.product',string='Producto', readonly=True)
    location_id= fields.Many2one('stock.location',string='Location')
    stock_to_date= fields.Float(string='Stock a la Fecha')

    def _select(self, select=False):
        if select:
            select_str= select
        else:
            select_str = """
SELECT
	product_id,
	location_id,
	precio as price_unit,
	date,
	'['||coalesce(origin,'')||']'||cast(cast(date as timestamp) + c_interval as varchar) as string_date,
	cantidad_en_fecha as stock_to_date
FROM poi_report_kardex_inv prk
LEFT JOIN
	(
		SELECT id, cast(substring(tz_offset from 1 for 3)||':'||substring(tz_offset from 4 for 2) as interval) as c_interval FROM res_company
	) as company_tz
	ON company_tz.id = prk.company_id

ORDER BY date
        """
        return select_str

    def init(self, cr, select=False, mlc=False, mlr=False):
        table = "poi_stock_kardex_analysis"
        cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = '%s';
            """ % table)
        vista = cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        cr.execute("""

            DROP MATERIALIZED VIEW IF EXISTS %s;
            CREATE MATERIALIZED VIEW %s as ((
            SELECT row_number() over() as id, *
                FROM ((
                    %s
                )) as asd
            ))""" % (table, table, self._select(select)))

