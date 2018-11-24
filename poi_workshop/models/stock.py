##############################################################################
#
#    Odoo
#    Copyright (C) 2014-2016 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'
    parts_line = fields.Many2one('workshop.order.parts.line', 'Item Planificado')

    # @api.multi
    # def write(self, vals):
    #     res = super(StockMove, self).write(vals)
    #     for move in self:
    #         if move.procurement_id:
    #             if vals.get('state') == 'assigned' and move.procurement_id.service_line:
    #                 from odoo import workflow
    #                 workshop_obj = self.env['workshop.order']
    #                 order_ids = workshop_obj.search([('procurement_group_id', 'in', [x.group_id.id for x in move])])
    #                 for order_id in order_ids:
    #                     if order_id.test_ready():
    #                         workflow.trg_validate(self.env.user.id, 'workshop.order', order_id.id, 'parts_ready', move.env.cr)
    #     return res
    #
    # @api.model
    # def _prepare_procurement_from_move(self, move):
    #     vals = super(StockMove, self)._prepare_procurement_from_move(move)
    #     vals['restrict_lot_id'] = move.restrict_lot_id.id
    #     return vals

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('parts_line')
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted.append(move.parts_line.id)
        return keys_sorted

    def _prepare_procurement_values(self):
        """ Heredado para agregar la linea request_line_id
        """
        result = super(StockMove, self)._prepare_procurement_values()
        if self.parts_line:
            result['parts_line'] = self.parts_line.id
        return result

    def _prepare_move_split_vals(self, uom_qty):
        vals = super(StockMove, self)._prepare_move_split_vals(uom_qty)
        vals['parts_line'] = self.parts_line.id
        return vals

class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values,
                               group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom,
                                                                     location_id, name, origin, values, group_id)
        if values.get('parts_line', False):
            result['parts_line'] = values['parts_line']
        return result

# class ProcurementOrder(models.Model):
#     _inherit = 'procurement.order'
#     service_line = fields.Many2one('workshop.order.service.line', 'Planned services')
#     parts_line = fields.Many2one('workshop.order.parts.line', 'Item Planificado')
#     restrict_lot_id = fields.Many2one('stock.production.lot', string='Lot')
#
#     @api.model
#     def _run_move_create(self, procurement):
#         res = super(ProcurementOrder, self)._run_move_create(procurement)
#         if procurement.restrict_lot_id:
#             res['restrict_lot_id'] = procurement.restrict_lot_id.id
#         if procurement.parts_line:
#             res['parts_line'] = procurement.parts_line.id
#         return res

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    group_maintenance = fields.Many2one('procurement.group', 'Group Maintenance', readonly=True)
    maintenance_id = fields.Many2one('workshop.order', string="Orden de Mantenimiento", readonly=True)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: