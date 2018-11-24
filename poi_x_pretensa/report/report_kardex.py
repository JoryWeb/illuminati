from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp import tools
import unicodedata
from openerp.report import report_sxw

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

class report_kardex(osv.osv):
    """docstring for pret_cubiertas_report"""
    _name = "report.kardex"
    _description = 'Reporte Kardex'
    _auto = False

    _columns = {
        'pick_name': fields.char('Nro. de Doc', readonly=True),
        'tipo': fields.char('CI', readonly=True),
        'date': fields.date('Fecha', readonly=True),
        'code': fields.char('Codigo', readonly=True),
        'detail': fields.char('Detalle', readonly=True),
        'warehouse_id': fields.many2one('stock.warehouse', 'Almacen', readonly=True),
        'lote': fields.char('Lote', readonly=True),
        'entrada': fields.float('Entrada',  digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'salida': fields.float('Salida', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'qtyy': fields.float('Saldo', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'standard_price': fields.float('C/U', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'entrada_v': fields.float('Entrada', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'salida_v': fields.float('Salida', digits_compute=dp.get_precision('Sale Price'), readonly=True),
        'saldo_v': fields.float('Saldo', digits_compute=dp.get_precision('Sale Price'), readonly=True),

    }

    def _select(self, cr, date_from, date_to, lote_id, warehouse_id, saldo):
        where = ""
        where_w = ""
        where_s = ""
        date_from_s = False
        if date_from:
            date_from_s = "'"+date_from+"'"
            where = where + " and date(to_char((date::timestamp - '4 hr'::interval),'yyyy-MM-dd')) >= '"+ date_from +"'"
        if date_to:
            where = where + " and date(to_char((date::timestamp - '4 hr'::interval),'yyyy-MM-dd')) <= '"+ date_to +"'"
        if lote_id:
            where = where + " and prodlot_id = "+ lote_id
        if warehouse_id:
            #where = where + " and (sw1.id = "+ warehouse_id +" or sw2.id = "+ warehouse_id +")"
            where_w = "where warehouse_id = " + warehouse_id
        if saldo:
            if lote_id:
                where_s = where_s + " and prodlot_id = "+ lote_id
            if date_from:
                where_s = where_s + " and date(to_char((date::timestamp - '4 hr'::interval),'yyyy-MM-dd')) < '" + date_from + "'"
            else:
                saldo = False

        sql_saldo = """
            select
            null as pick_name, 
            'SALDO'::varchar as tipo, 
            """+ str(date_from_s or 'null') +"""::timestamp as date, 
            max(code) as code, 
            'SALDO: Hasta """+str(date_from)+"""'::varchar as detail, 
            """+ str(warehouse_id or 'null') +"""::integer as warehouse_id,
            max(lote) as lote,
            sum(entrada) as entrada,
            sum(salida)as salida,
            sum(qtyy) as qtyy,
            max(standard_price) as standard_price, 
            sum(entrada_v) as entrada_v,
            sum(salida_v) as salida_v,
            sum(saldo_v) as saldo_v
        from
            (

            select
            
                pick_name,
               case
                    when name1 like  'Recupera%' then 'RECUPERADO'
                    when name_sm like '%Inicial' then 'SI'
                    when tp = 'out' then 'VENTAS'
                    when inventory_id is not null then 'AJUSTE'
                    when name1 like 'Transito%' then 'TRANF'
                    when name2 like 'Transito%' then 'TRANF'
                    when name3 like 'Transito%' then 'TRANF'
                    else tipo
                end as tipo,
                date::timestamp - '4 hr'::interval,
                pp.default_code as code,
                case
                    when name1 like  'Recupera%' then 'RECUPERADO'
                    when name_sm like '%Inicial' then name1
                    when tp = 'out' then name3
                    when inventory_id is not null then name_sm
                    when name1 like 'Transito%' then name1
                    when name2 like 'Transito%' then name2
                    when name3 like 'Transito%' then name3             
                    else tipo
                end as detail,
                warehouse_id,
                case
                    when spl_name is not null then spl_name
                    else name_sm
                end as lote,   
                case
                    when qtyy > 0 then  qtyy
                    else 0
                end as entrada,
                case
                    when qtyy < 0 then  qtyy * -1
                    else 0
                end as salida,
                qtyy,
                pt.standard_price,
                case
                    when qtyy > 0 then qtyy * total_computed * standard_price
                    else 0
                end as entrada_v,
                case
                  
                    when qtyy < 0  then qtyy *-1 * total_computed * standard_price
                    else 0
                end as salida_v,
                case
                    when qtyy > 0 then qtyy * total_computed * standard_price
                    when qtyy < 0 then (qtyy * total_computed * standard_price)
                    else 0
                end as saldo_v

            from
            (
             select
                *   
                from
              
              (
            SELECT min(m.id) AS id,
                m.date,
                to_char(m.date, 'YYYY'::text) AS year,
                to_char(m.date, 'MM'::text) AS month,
                m.partner_id,
                m.location_id,
                m.product_id,
                pt.categ_id AS product_categ_id,
                l.usage AS location_type,
                l.scrap_location,
                m.company_id,
                m.state,
                m.prodlot_id,
                COALESCE(sum((- m.product_qty) * pu.factor / pu2.factor), 0.0) AS qtyy,
                max(sw.id) as warehouse_id,
                max(sp.name) as pick_name,
                max(l.name) as tipo,
                max(sim.inventory_id) as inventory_id,
                max(sp.type) as tp,
                l.usage,
                m.name as name_sm,
                max(spl.name) as spl_name,
                case
                   when max(pd.metric_type) = 'lineal' then max(pd.var_x)
                   when max(pd.metric_type) = 'volume' then max(pd.var_z) * max(pd.var_y) * max(pd.var_x)
                   else max(pd.var_y) * max(pd.var_x)
                end as total_computed,
                max(sl2.name) as name2,
                max(sl1.name) as name1,
                max(sl3.name) as name3
               FROM stock_move m
                 LEFT JOIN stock_picking p ON m.picking_id = p.id
                 LEFT JOIN product_product pp ON m.product_id = pp.id
                 LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                 LEFT JOIN product_uom pu ON pt.uom_id = pu.id
                 LEFT JOIN product_uom pu2 ON m.product_uom = pu2.id
                 LEFT JOIN product_uom u ON m.product_uom = u.id
                 LEFT JOIN stock_location l ON m.location_id = l.id
                 left join stock_location sl1 on sl1.id = m.location_dest_id
                 left join stock_location sl2 on sl2.id = sl1.location_id
                 left join stock_location sl3 on sl3.id = l.location_id
                 left join stock_warehouse sw on sw.lot_stock_id = l.id
                 left join stock_picking sp on sp.id = m.picking_id
                 left join stock_inventory_move_rel sim on sim.move_id = m.id 
                 left join stock_production_lot spl on spl.id = m.prodlot_id
                 left join product_dimension pd on pd.id = spl.dimension_id
              WHERE m.state::text <> 'cancel'::text
              GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id, m.location_dest_id, m.prodlot_id, m.date, m.state, l.usage, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'::text), to_char(m.date, 'MM'::text)
            UNION ALL
             SELECT - m.id AS id,
                m.date,
                to_char(m.date, 'YYYY'::text) AS year,
                to_char(m.date, 'MM'::text) AS month,
                m.partner_id,
                m.location_dest_id AS location_id,
                m.product_id,
                pt.categ_id AS product_categ_id,
                l.usage AS location_type,
                l.scrap_location,
                m.company_id,
                m.state,
                m.prodlot_id,
                COALESCE(sum(m.product_qty * pu.factor / pu2.factor), 0.0) AS qtyy,
                max(sw.id) as warehouse_id,
                max(sp.name) as pick_name,
                max(l.name) as tipo,
                max(sim.inventory_id) as inventory_id,
                max(sp.type) as tp,
                l.usage,
                m.name as name_sm,
                max(spl.name) as spl_name,
                case
                   when max(pd.metric_type) = 'lineal' then max(pd.var_x)
                   when max(pd.metric_type) = 'volume' then max(pd.var_z) * max(pd.var_y) * max(pd.var_x)
                   else max(pd.var_y) * max(pd.var_x)
                end as total_computed,
                max(sl2.name) as name2,
                max(sl1.name) as name1,
                max(sl3.name) as name3
               FROM stock_move m
                 LEFT JOIN stock_picking p ON m.picking_id = p.id
                 LEFT JOIN product_product pp ON m.product_id = pp.id
                 LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                 LEFT JOIN product_uom pu ON pt.uom_id = pu.id
                 LEFT JOIN product_uom pu2 ON m.product_uom = pu2.id
                 LEFT JOIN product_uom u ON m.product_uom = u.id
                 LEFT JOIN stock_location l ON m.location_dest_id = l.id
                 left join stock_location sl1 on sl1.id = m.location_id
                 left join stock_location sl2 on sl2.id = l.location_id
                 left join stock_location sl3 on sl3.id = sl1.location_id
                 left join stock_warehouse sw on sw.lot_stock_id = l.id
                 left join stock_picking sp on sp.id = m.picking_id
                 left join stock_inventory_move_rel sim on sim.move_id = m.id
                 left join stock_production_lot spl on spl.id = m.prodlot_id 
                 left join product_dimension pd on pd.id = spl.dimension_id
              WHERE m.state::text <> 'cancel'::text
              GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id, m.location_dest_id, m.prodlot_id, m.date, m.state, l.usage, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'::text), to_char(m.date, 'MM'::text)
              )as asd
             where
                state = 'done' 
                """+ where_s +"""

                               ) as f
                left join product_product pp on pp.id = f.product_id
                left join product_template pt on pt.id = pp.product_tmpl_id
            """+ where_w +"""
            order by date) as asd
        """
        sql = """
            select
                pick_name,
                case
                    when name1 like  'Recupera%' then 'RECUPERADO'
                    when name_sm like '%Inicial' then 'SI'
                    when tp = 'out' then 'VENTAS'
                    when inventory_id is not null then 'AJUSTE'
                    when name1 like 'Transito%' then 'TRANF'
                    when name2 like 'Transito%' then 'TRANF'
                    when name3 like 'Transito%' then 'TRANF'
                    else tipo
                end as tipo,
                date::timestamp - '4 hr'::interval,
                pp.default_code as code,
                case
                    when name1 like  'Recupera%' then 'RECUPERADO'
                    when name_sm like '%Inicial' then name1
                    when tp = 'out' then name3
                    when inventory_id is not null then name_sm
                    when name1 like 'Transito%' then name1
                    when name2 like 'Transito%' then name2
                    when name3 like 'Transito%' then name3             
                    else tipo
                end as detail,
                warehouse_id,
                case
                    when spl_name is not null then spl_name
                    else name_sm
                end as lote,   
                case
                    when qtyy > 0 then  qtyy
                    else 0
                end as entrada,
                case
                    when qtyy < 0 then  qtyy *-1
                    else 0
                end as salida,
                qtyy,
                pt.standard_price,
                case
                    when qtyy > 0 then qtyy * total_computed * standard_price
                    else 0
                end as entrada_v,
                case
                  
                    when qtyy < 0  then qtyy *-1 * total_computed * standard_price
                    else 0
                end as salida_v,
                case
                    when qtyy > 0 then qtyy * total_computed * standard_price
                    when qtyy < 0 then (qtyy * total_computed * standard_price)
                    else 0
                end as saldo_v

            from(
                    select
            *
        from
        (
            SELECT min(m.id) AS id,
                m.date,
                to_char(m.date, 'YYYY'::text) AS year,
                to_char(m.date, 'MM'::text) AS month,
                m.partner_id,
                m.location_id,
                m.product_id,
                pt.categ_id AS product_categ_id,
                l.usage AS location_type,
                l.scrap_location,
                m.company_id,
                m.state,
                m.prodlot_id,
                COALESCE(sum((- m.product_qty) * pu.factor / pu2.factor), 0.0) AS qtyy,
                max(sw.id) as warehouse_id,
                max(sp.name) as pick_name,
                max(l.name) as tipo,
                max(sim.inventory_id) as inventory_id,
                max(sp.type) as tp,
                l.usage,
                m.name as name_sm,
                max(spl.name) as spl_name,
                case
                   when max(pd.metric_type) = 'lineal' then max(pd.var_x)
                   when max(pd.metric_type) = 'volume' then max(pd.var_z) * max(pd.var_y) * max(pd.var_x)
                   else max(pd.var_y) * max(pd.var_x)
                end as total_computed,
                max(sl2.name) as name2,
                max(sl1.name) as name1,
                max(sl3.name) as name3
               FROM stock_move m
                 LEFT JOIN stock_picking p ON m.picking_id = p.id
                 LEFT JOIN product_product pp ON m.product_id = pp.id
                 LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                 LEFT JOIN product_uom pu ON pt.uom_id = pu.id
                 LEFT JOIN product_uom pu2 ON m.product_uom = pu2.id
                 LEFT JOIN product_uom u ON m.product_uom = u.id
                 LEFT JOIN stock_location l ON m.location_id = l.id
                 left join stock_location sl1 on sl1.id = m.location_dest_id
                 left join stock_location sl2 on sl2.id = sl1.location_id
                 left join stock_location sl3 on sl3.id = l.location_id
                 left join stock_warehouse sw on sw.lot_stock_id = l.id
                 left join stock_picking sp on sp.id = m.picking_id
                 left join stock_inventory_move_rel sim on sim.move_id = m.id 
                 left join stock_production_lot spl on spl.id = m.prodlot_id
                 left join product_dimension pd on pd.id = spl.dimension_id
              WHERE m.state::text <> 'cancel'::text
              GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id, m.location_dest_id, m.prodlot_id, m.date, m.state, l.usage, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'::text), to_char(m.date, 'MM'::text)
            UNION ALL
             SELECT - m.id AS id,
                m.date,
                to_char(m.date, 'YYYY'::text) AS year,
                to_char(m.date, 'MM'::text) AS month,
                m.partner_id,
                m.location_dest_id AS location_id,
                m.product_id,
                pt.categ_id AS product_categ_id,
                l.usage AS location_type,
                l.scrap_location,
                m.company_id,
                m.state,
                m.prodlot_id,
                COALESCE(sum(m.product_qty * pu.factor / pu2.factor), 0.0) AS qtyy,
                max(sw.id) as warehouse_id,
                max(sp.name) as pick_name,
                max(l.name) as tipo,
                max(sim.inventory_id) as inventory_id,
                max(sp.type) as tp,
                l.usage,
                m.name as name_sm,
                max(spl.name) as spl_name,
                case
                   when max(pd.metric_type) = 'lineal' then max(pd.var_x)
                   when max(pd.metric_type) = 'volume' then max(pd.var_z) * max(pd.var_y) * max(pd.var_x)
                   else max(pd.var_y) * max(pd.var_x)
                end as total_computed,
                max(sl2.name) as name2,
                max(sl1.name) as name1,
                max(sl3.name) as name3
               FROM stock_move m
                 LEFT JOIN stock_picking p ON m.picking_id = p.id
                 LEFT JOIN product_product pp ON m.product_id = pp.id
                 LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                 LEFT JOIN product_uom pu ON pt.uom_id = pu.id
                 LEFT JOIN product_uom pu2 ON m.product_uom = pu2.id
                 LEFT JOIN product_uom u ON m.product_uom = u.id
                 LEFT JOIN stock_location l ON m.location_dest_id = l.id
                 left join stock_location sl1 on sl1.id = m.location_id
                 left join stock_location sl2 on sl2.id = l.location_id
                 left join stock_location sl3 on sl3.id = sl1.location_id
                 left join stock_warehouse sw on sw.lot_stock_id = l.id
                 left join stock_picking sp on sp.id = m.picking_id
                 left join stock_inventory_move_rel sim on sim.move_id = m.id
                 left join stock_production_lot spl on spl.id = m.prodlot_id 
                 left join product_dimension pd on pd.id = spl.dimension_id
              WHERE m.state::text <> 'cancel'::text
              GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id, m.location_dest_id, m.prodlot_id, m.date, m.state, l.usage, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'::text), to_char(m.date, 'MM'::text)
              )as asd
             where
                state = 'done' 
                """+ where +"""

                               ) as f
                left join product_product pp on pp.id = f.product_id
                left join product_template pt on pt.id = pp.product_tmpl_id
            """+ where_w +"""
            order by date
            """
        if saldo:
            sql = sql_saldo + "UNION ALL" + sql
        return sql


    def init(self, cr, date_from=False, date_to=False, lote_id=False, warehouse_id=False, saldo=False):
        tools.sql.drop_view_if_exists(cr, 'report_kardex')
        sql = """
            CREATE or REPLACE VIEW report_kardex as ((
            SELECT row_number() over() as id, *
                FROM ((
                    %s
                )) as asd
            ))""" % (self._select(cr, date_from, date_to, lote_id, warehouse_id, saldo))
        cr.execute(sql)

class report_kardex_pdf_pre(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        res = super(report_kardex_pdf_pre, self).__init__(cr, uid, name, context)
        pro_obj = self.pool.get("stock.production.lot")
        if context['lote_id']:
            pro_id =  pro_obj.search(cr, uid, [('id', '=', context['lote_id'][0])])
            pro = pro_obj.browse(self.cr, self.uid, pro_id)[0]
        else:
            pro = False
        self.localcontext.update({
            'get_all_lines': self.get_all_lines,
            'pro': pro
        })

    def get_all_lines(self):
        obj_kardex = self.pool.get("report.kardex")
        ids_kardex = obj_kardex.search(self.cr, self.uid, [('id', '>', '0')])
        res = obj_kardex.browse(self.cr, self.uid, ids_kardex)
        return res


report_sxw.report_sxw('report.kardex_pdf_pre2', 'report.kardex', 'poi_x_pretensa/report/report_kardex_pdf.mako', parser=report_kardex_pdf_pre)

class report_kardex_pdf_pre5(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        res = super(report_kardex_pdf_pre5, self).__init__(cr, uid, name, context)
        pro_obj = self.pool.get("stock.production.lot")
        if context['lote_id']:
            pro_id =  pro_obj.search(cr, uid, [('id', '=', context['lote_id'][0])])
            pro = pro_obj.browse(self.cr, self.uid, pro_id)[0]
        else:
            pro = False
        self.localcontext.update({
            'get_all_lines': self.get_all_lines,
            'pro': pro
        })

    def get_all_lines(self):
        obj_kardex = self.pool.get("report.kardex")
        ids_kardex = obj_kardex.search(self.cr, self.uid, [('id', '>', '0')])
        res = obj_kardex.browse(self.cr, self.uid, ids_kardex)
        return res

report_sxw.report_sxw('report.kardex_pdf_pre3', 'report.kardex', 'poi_x_pretensa/report/report_kardex_pdf3.mako', parser=report_kardex_pdf_pre)


class report_kardex_wiz(osv.osv_memory):

    _name  = "report.kardex_wiz"

    _columns = {
        'lote_id': fields.many2one('stock.production.lot', string='Lote', required=True),
        'warehouse_id': fields.many2one('stock.warehouse', string='Alamacen'),
        'date_from': fields.date('Desde'),
        'date_to': fields.date('Hasta'),
        'saldo': fields.boolean('Saldo'),
    }

    _defaults = {
        'saldo': True,
    }   

    def open_table(self, cr, uid, ids, context=None):
        obj_kardex = self.pool.get('report.kardex')
        data = self.read(cr, uid, ids,context=context)[0]
        warehouse_id = False
        lote_id = False
        saldo = data['saldo']
        if data['warehouse_id']:
            warehouse_id = str(data['warehouse_id'][0])
        if data['lote_id']:
            lote_id = str(data['lote_id'][0])
        obj_kardex.init(cr, date_from=data['date_from'], date_to=data['date_to'], lote_id=lote_id, warehouse_id=warehouse_id, saldo=saldo)
        datas = {}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'kardex_pdf_pre2',
            'datas': datas,
            'context':data,
        }

report_kardex_wiz()


class report_kardex_wiz3(osv.osv_memory):

    _name  = "report.kardex_wiz3"

    _columns = {
        'lote_id': fields.many2one('stock.production.lot', string='Lote', required=True),
        'warehouse_id': fields.many2one('stock.warehouse', string='Alamacen'),
        'date_from': fields.date('Desde'),
        'date_to': fields.date('Hasta'),
        'saldo': fields.boolean('Saldo'),
    }

    _defaults = {
        'saldo': True,
    }

    def open_table(self, cr, uid, ids, context=None):
        obj_kardex = self.pool.get('report.kardex')
        data = self.read(cr, uid, ids,context=context)[0]
        warehouse_id = False
        lote_id = False
        saldo = data['saldo']
        if data['warehouse_id']:
            warehouse_id = str(data['warehouse_id'][0])
        if data['lote_id']:
            lote_id = str(data['lote_id'][0])
        obj_kardex.init(cr, date_from=data['date_from'], date_to=data['date_to'], lote_id=lote_id, warehouse_id=warehouse_id, saldo=saldo)
        datas = {}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'kardex_pdf_pre3',
            'datas': datas,
            'context':data,
        }

report_kardex_wiz()