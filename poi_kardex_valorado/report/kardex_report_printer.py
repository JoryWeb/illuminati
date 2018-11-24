
from odoo import api, models, _
from odoo.exceptions import UserError

class ReportKardexPrinter(models.AbstractModel):
    _name = 'report.poi_kardex_valorado.report_kardex'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        return {
            'data': data['form'],
            'get_lines': self.get_lines(data.get('form')),
        }

    @api.model
    def get_lines(self, options):
        sql = """
        with data as (
               select
                 sm.id                                  as move_id,
                 sml.date,
                 pt.default_code                        as codigo,
                 pt.name                                as producto,
                 pp.id                                  as product_id,
                 sm.name                                as name_mov,
                 sml.lot_id,
                 spl.name as lote,
                 coalesce(sml.qty_done * (-1), 0) as product_uom_qty,
                 sm.product_uom,
                 pu.name as udm,
                 coalesce(sm.price_unit * (-1), 0)      AS precio,
                 coalesce(sm.price_unit*sml.qty_done * (-1), 0)           as valor,
                 0                                      AS cantidad_en_fecha,
                 0                                      AS total_inventario,
                 0                                      AS valor_inventario_fecha,
                 lo.complete_name                       as origen,
                 ld.complete_name                       as destino,
                 sp.name as picking,
                 CASE
                 WHEN spt.code = 'incoming'
                   THEN 'Proveedores'
                 WHEN spt.code = 'outgoing'
                   THEN 'Clientes'
                 WHEN spt.code = 'internal'
                   THEN 'Interno o Ajuste'
                 ELSE 'Otros'
                 END                                    AS tipo
               from stock_move_line sml
                 inner join stock_move sm on sm.id = sml.move_id
                 inner join product_product pp on pp.id = sm.product_id
                 inner join product_template pt on pp.product_tmpl_id = pt.id
                 inner join stock_picking_type spt on sm.picking_type_id = spt.id
                 inner join stock_location lo on sm.location_id = lo.id
                 inner join stock_location ld on sm.location_dest_id = ld.id
                 inner join stock_picking sp on sp.id = sm.picking_id
                 inner join product_uom pu on pu.id = sm.product_uom
                 left join stock_production_lot spl on spl.id = sml.lot_id
               where sml.state = 'done'
              and sm.date between '""" + options['date_from'] + """' and '""" + options['date_to'] + """'
                     and sm.product_id = """ + str(options['product_id'][0]) + """ and sm.location_id = """ + str(options['location_id'][0]) + """
               UNION ALL
               select
                 sm.id                      as move_id,
                 sml.date,
                 pt.default_code            as codigo,
                 pt.name                    as producto,
                 pp.id                      as product_id,
                 sm.name                    as name_mov,
                 sml.lot_id,
                 spl.name as lote,
                 sml.qty_done as product_uom_qty,
                 sm.product_uom,
                 pu.name as udm,
                 coalesce(sm.price_unit, 0) as precio,
                 coalesce(sm.price_unit*sml.qty_done, 0)      as valor,
                 0                          AS cantidad_en_fecha,
                 0                          AS total_inventario,
                 0                          AS valor_inventario_fecha,
                 lo.complete_name           as origen,
                 ld.complete_name           as destino,
                 sp.name as picking,
                 CASE
                 WHEN spt.code = 'incoming'
                   THEN 'Proveedores'
                 WHEN spt.code = 'outgoing'
                   THEN 'Clientes'
                 WHEN spt.code = 'internal'
                   THEN 'Interno o Ajuste'
                 ELSE 'Otros'
                 END                        AS tipo
               from stock_move_line sml
                 inner join stock_move sm on sm.id = sml.move_id
                 inner join product_product pp on pp.id = sm.product_id
                 inner join product_template pt on pp.product_tmpl_id = pt.id
                 inner join stock_picking_type spt on sm.picking_type_id = spt.id
                 inner join stock_location lo on sm.location_id = lo.id
                 inner join stock_location ld on sm.location_dest_id = ld.id
                 inner join stock_picking sp on sp.id = sm.picking_id
                 inner join product_uom pu on pu.id = sm.product_uom
                 left join stock_production_lot spl on spl.id = sml.lot_id
               where sml.state = 'done'
               and sm.date between '""" + options['date_from'] + """' and '""" + options['date_to'] + """'
                  and sm.product_id = """ + str(options['product_id'][0]) + """ and sm.location_dest_id = """ + str(options['location_id'][0]) + """
               order by 4,1
        
        )
        select
          *,
          sum(product_uom_qty) over (order by product_id, date asc rows between unbounded preceding and current row) as cantidad_fecha,
          sum(valor) over (order by product_id, date asc rows between unbounded preceding and current row) as valor_fecha
        from data
        """
        cr = self.env.cr
        cr.execute(sql)
        res_lines = cr.dictfetchall()
        return res_lines


class ReportKardexValoradoPrinter(models.AbstractModel):
    _name = 'report.poi_kardex_valorado.report_kardex_valorado'

    @api.model
    def get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        return {
            'data': data['form'],
            'get_lines': self.get_lines(data.get('form')),
        }

    @api.model
    def get_lines(self, options):
        sql = """
                with data as (
                       select
                         sm.id                                  as move_id,
                         sml.date,
                         pt.default_code                        as codigo,
                         pt.name                                as producto,
                         pp.id                                  as product_id,
                         sm.name                                as name_mov,
                         sml.lot_id,
                         spl.name as lote,
                         coalesce(sml.qty_done * (-1), 0) as product_uom_qty,
                         sm.product_uom,
                         pu.name as udm,
                         coalesce(sm.price_unit * (-1), 0)      AS precio,
                         coalesce(sm.price_unit*sml.qty_done * (-1), 0)           as valor,
                         0                                      AS cantidad_en_fecha,
                         0                                      AS total_inventario,
                         0                                      AS valor_inventario_fecha,
                         lo.complete_name                       as origen,
                         ld.complete_name                       as destino,
                         sp.name as picking,
                         CASE
                         WHEN spt.code = 'incoming'
                           THEN 'Proveedores'
                         WHEN spt.code = 'outgoing'
                           THEN 'Clientes'
                         WHEN spt.code = 'internal'
                           THEN 'Interno o Ajuste'
                         ELSE 'Otros'
                         END                                    AS tipo
                       from stock_move_line sml
                         inner join stock_move sm on sm.id = sml.move_id
                         inner join product_product pp on pp.id = sm.product_id
                         inner join product_template pt on pp.product_tmpl_id = pt.id
                         inner join stock_picking_type spt on sm.picking_type_id = spt.id
                         inner join stock_location lo on sm.location_id = lo.id
                         inner join stock_location ld on sm.location_dest_id = ld.id
                         inner join stock_picking sp on sp.id = sm.picking_id
                         inner join product_uom pu on pu.id = sm.product_uom
                         left join stock_production_lot spl on spl.id = sml.lot_id
                       where sml.state = 'done'
                      and sm.date between '""" + options['date_from'] + """' and '""" + options['date_to'] + """'
                             and sm.product_id = """ + str(
            options['product_id'][0]) + """ and sm.location_id = """ + str(options['location_id'][0]) + """
                       UNION ALL
                       select
                         sm.id                      as move_id,
                         sml.date,
                         pt.default_code            as codigo,
                         pt.name                    as producto,
                         pp.id                      as product_id,
                         sm.name                    as name_mov,
                         sml.lot_id,
                         spl.name as lote,
                         sml.qty_done as product_uom_qty,
                         sm.product_uom,
                         pu.name as udm,
                         coalesce(sm.price_unit, 0) as precio,
                         coalesce(sm.price_unit*sml.qty_done, 0)      as valor,
                         0                          AS cantidad_en_fecha,
                         0                          AS total_inventario,
                         0                          AS valor_inventario_fecha,
                         lo.complete_name           as origen,
                         ld.complete_name           as destino,
                         sp.name as picking,
                         CASE
                         WHEN spt.code = 'incoming'
                           THEN 'Proveedores'
                         WHEN spt.code = 'outgoing'
                           THEN 'Clientes'
                         WHEN spt.code = 'internal'
                           THEN 'Interno o Ajuste'
                         ELSE 'Otros'
                         END                        AS tipo
                       from stock_move_line sml
                         inner join stock_move sm on sm.id = sml.move_id
                         inner join product_product pp on pp.id = sm.product_id
                         inner join product_template pt on pp.product_tmpl_id = pt.id
                         inner join stock_picking_type spt on sm.picking_type_id = spt.id
                         inner join stock_location lo on sm.location_id = lo.id
                         inner join stock_location ld on sm.location_dest_id = ld.id
                         inner join stock_picking sp on sp.id = sm.picking_id
                         inner join product_uom pu on pu.id = sm.product_uom
                         left join stock_production_lot spl on spl.id = sml.lot_id
                       where sml.state = 'done'
                       and sm.date between '""" + options['date_from'] + """' and '""" + options['date_to'] + """'
                          and sm.product_id = """ + str(
            options['product_id'][0]) + """ and sm.location_dest_id = """ + str(options['location_id'][0]) + """
                       order by 4,1

                )
                select
                  *,
                  sum(product_uom_qty) over (order by product_id, date asc rows between unbounded preceding and current row) as cantidad_fecha,
                  sum(valor) over (order by product_id, date asc rows between unbounded preceding and current row) as valor_fecha
                from data
                """
        cr = self.env.cr
        cr.execute(sql)
        res_lines = cr.dictfetchall()
        return res_lines
