##############################################################################
# For copyright and license notices, see __odoo__.py file in root directory
##############################################################################
from odoo import models, api, fields, _
from odoo.osv import osv
import collections

class StockRequest(models.Model):
    _inherit = 'stock.request'

    # @api.multi
    # def action_picking_create(self):
    #     for request in self:
    #
    #         group_ab = self.env["procurement.group"].create({'name': request.name})
    #         lot_verif = []
    #         for line_lot in request.request_lines:
    #             if line_lot.lot_id:
    #                 lot_verif.append(line_lot.lot_id.id)
    #
    #         list_repeat = [item for item, count in collections.Counter(lot_verif).items() if count > 1]
    #
    #         for list_r in list_repeat:
    #             name = self.env['stock.production.lot'].browse(list_r).name
    #             raise osv.except_osv(_('Error!'), _('El chasis %s esta repetido en dos o mas lineas') % (name) )
    #
    #         for line in request.request_lines:
    #
    #
    #             if line.product_uom_qty <= 0:
    #                 raise osv.except_osv(_('Error!'), _('Esta solicitando un producto con cantidad 0'))
    #
    #             if not line.lot_id and line.product_id.tracking in ('serial', 'lot'):
    #                 raise osv.except_osv(_('Error!'),
    #                                      _('El producto %s, requiere que registre lote o serie') % (line.product_id.name))
    #
    #             if line.lot_id and line.product_id.tracking in ('serial') and int(line.product_uom_qty) != 1:
    #                 raise osv.except_osv(_('Error!'),
    #                                      _('El producto %s, para el lote %s requiere que la cantidad solo sea 1') % (line.product_id.name, line.lot_id.name))
    #             pull_id = False
    #             if len(request.route_id.pull_ids) <= 1:
    #                 for pulls in request.route_id.pull_ids:
    #                     pull_id = pulls.id
    #                 vals = {
    #                     'product_id': line.product_id.id,
    #                     'product_uom': line.product_uom.id,
    #                     'product_qty': line.product_uom_qty,
    #                     'warehouse_id': request.warehouse_dest_id.id,
    #                     'location_id': request.warehouse_dest_id.lot_stock_id.id,
    #                     'name': request.name,
    #                     'route_ids': [(4, request.route_id.id)],
    #                     'group_id': group_ab.id,
    #                     'request_line_id': line.id,
    #                     'rule_id': pull_id,
    #                     'date_planned': request.request_date_planned,
    #                     'lot_id': line.lot_id.id or False,
    #                 }
    #             else:
    #                 vals = {
    #                     'product_id': line.product_id.id,
    #                     'product_uom': line.product_uom.id,
    #                     'product_qty': line.product_uom_qty,
    #                     'warehouse_id': request.warehouse_dest_id.id,
    #                     'location_id': request.warehouse_dest_id.lot_stock_id.id,
    #                     'name': request.name,
    #                     'route_ids': [(4, request.route_id.id)],
    #                     'group_id': group_ab.id,
    #                     'request_line_id': line.id,
    #                     'origin': request.name,
    #                     'date_planned': request.request_date_planned,
    #                     'lot_id': line.lot_id.id or False,
    #                 }
    #             procu = self.env['procurement.order'].create(vals)
    #             procu.run()
    #
    #         pickings = self.env['stock.picking'].search([('group_id', '=', group_ab.id)])
    #         for picking in pickings:
    #             picking.request_id = request.id
    #             picking.action_assign()