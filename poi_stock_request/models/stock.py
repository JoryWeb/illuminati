# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    request_id = fields.Many2one('stock.request', string="Purchase Orders", readonly=True)

    @api.multi
    def request_products(self):

        created_id = self.env['poi.request.products'].create({'picking_id': len(self.id) and self[0].id or False})
        return self.pool['poi.request.products'].wizard_view(created_id)

    @api.multi
    def prepare_stock_request_lines(self, request_id):
        res = []
        for move in self.move_lines:
            # if move.move_dest_id:
            #    raise Warning(
            #        u'Por favor procese el albarán %s no es necesario transferir a otra ubicación' % move.move_dest_id.picking_id.name)
            if move.location_dest_id.usage in ('customer', 'supplier', 'inventory'):
                raise Warning(
                    'No puede crear un solicitud en una ubicación de tipo proveedor, cliente o inventario')
            else:
                move_oper = self.env['stock.move.operation.link'].search([('move_id', '=', move.id)])
                for move_quant in move_oper:
                    res.append({'request_id': request_id.id,
                                'product_id': move.product_id.id,
                                'product_uom_qty': move_quant.qty,
                                'lot_id': move_quant.reserved_quant_id.lot_id.id or False,
                                'product_uom': move.product_uom.id})

        return res

    @api.multi
    def create_sending_request(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """

        stock_request_obj = self.env['stock.request']
        stock_request_lines_obj = self.env['stock.request.line']

        stock_request_id = stock_request_obj.create({'description': _('Para el Movimiento %s' % self.name),
                                                     'location_id': self.location_dest_id.id,
                                                     'use_location_id': True,
                                                     'type': 'request',
                                                     'request_id': self.request_id and self.request_id.id or False,
                                                     'picking_id': self.id,
                                                     'warehouse_id': self.request_id.warehouse_dest_id.id or self.picking_type_id.warehouse_id.id})

        for request_line in self.prepare_stock_request_lines(stock_request_id):
            stock_request_lines_obj.create(request_line)

        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        stock_request_form = self.env.ref('poi_stock_request.view_sending_stock_form', False)
        ctx = dict(
            default_model='stock.request',
        )
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.request',
            'views': [(stock_request_form.id, 'form')],
            'view_id': stock_request_form.id,
            'target': 'current',
            'context': ctx,
            'res_id': stock_request_id.id
        }

    @api.multi
    def action_cancel(self):
        """In addition to what the method in the parent class does,
        cancel the batches for which all pickings are cancelled
        """
        result = super(StockPicking, self).action_cancel()
        for picking in self:
            pickings = self.search([('request_id', '=', picking.request_id.id)])
            bandera = True
            for pick in pickings:
                if pick.state != 'cancel':
                    bandera = False
            if picking.request_id and bandera:
                picking.request_id.state = 'cancel'

        return result


class StockMove(models.Model):
    _inherit = 'stock.move'

    request_line_id = fields.Many2one('stock.request.line',
                                      'Purchase Order Line', ondelete='set null', index=True, readonly=True, copy=False)

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('request_line_id')
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted.append(move.request_line_id.id)
        return keys_sorted

    def _prepare_procurement_values(self):
        """ Heredado para agregar la linea request_line_id
        """
        result = super(StockMove, self)._prepare_procurement_values()
        if self.request_line_id:
            result['request_line_id'] = self.request_line_id.id
        return result

    def _prepare_move_split_vals(self, uom_qty):
        vals = super(StockMove, self)._prepare_move_split_vals(uom_qty)
        vals['request_line_id'] = self.request_line_id.id
        return vals

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None,
                                  owner_id=None, strict=True):

        if self.request_line_id.lot_id and self.procure_method == 'make_to_stock':
            lot_id_req = self.sale_line_id.lot_id
            res = super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id,
                                                                   lot_id=lot_id_req, package_id=package_id,
                                                                   owner_id=owner_id, strict=strict)
        else:
            res = super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id,
                                                                   lot_id=lot_id, package_id=package_id,
                                                                   owner_id=owner_id,
                                                                   strict=strict)
        return res

    @api.model
    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        if self.request_line_id:
            return False
        else:
            return super(StockMove, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id)

class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values,
                               group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom,
                                                                     location_id, name, origin, values, group_id)
        if values.get('request_line_id', False):
            result['request_line_id'] = values['request_line_id']
        return result
