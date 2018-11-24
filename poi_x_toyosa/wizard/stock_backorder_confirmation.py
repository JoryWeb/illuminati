# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.tools.translate import _


class stock_backorder_confirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'
    _description = 'Backorder Confirmation'

    # @api.multi
    # def _process(self, cancel_backorder=False):
    #     # rescatar las series no utilizadas
    #     lot_save = []
    #     for pack in self.pick_id.pack_operation_product_ids:
    #         for pack_lot in pack.pack_lot_ids:
    #             if pack_lot.qty < pack_lot.qty_todo:
    #                 d = {
    #                     'product_id': pack.product_id.id,
    #                     'lot_id': pack_lot.lot_id.id,
    #                     'lot_name': pack_lot.lot_name,
    #                     'state_finanzas': pack_lot.lot_id.state_finanzas,
    #                     'katashiki': pack_lot.lot_id.katashiki.id,
    #                     'modelo': pack_lot.lot_id.modelo.id,
    #                     'embarque': pack_lot.lot_id.embarque,
    #                     'edicion': pack_lot.edicion,
    #                     'colorinterno': pack_lot.colorinterno.id,
    #                     'colorexterno': pack_lot.colorexterno.id,
    #                     'n_correlativo': pack_lot.n_correlativo,
    #                     'edicion': pack_lot.edicion,
    #                     'n_produccion': pack_lot.n_produccion,
    #                     'price_unit': pack_lot.price_unit,
    #                 }
    #                 lot_save.append(d)
    #     super(stock_backorder_confirmation, self)._process(cancel_backorder=cancel_backorder)
    #     backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', self.pick_id.id)])
    #     pack_lot = self.env['stock.pack.operation.lot']
    #     for pack in backorder_pick.pack_operation_product_ids:
    #         if not pack.pack_lot_ids:
    #             if pack.product_id.tracking in ('serial', 'lot'):
    #                 for move in lot_save:
    #                     if pack.product_id.id == move['product_id'] and pack.colorinterno.id == move['colorinterno'] and pack.colorexterno.id == move['colorexterno'] and pack.edicion == move['edicion']:
    #                         if pack.product_id.tracking == 'serial':
    #                             sum_qty = 1
    #                             serie = 1
    #                             pack_lot.create({
    #                                 'lot_id': move['lot_id'],
    #                                 'operation_id': pack.id,
    #                                 'qty': 0,
    #                                 'qty_todo': sum_qty,
    #                                 'lot_name': move['lot_name'],
    #                                 'edicion': move['edicion'],
    #                                 'colorinterno': move['colorinterno'],
    #                                 'colorexterno': move['colorexterno'],
    #                                 'n_correlativo': move['n_correlativo'],
    #                                 'n_produccion': move['n_produccion'],
    #                                 'price_unit': move['price_unit'],
    #                             })
    #                             serie += 1
