# Developer Miguel Angel Callisaya miguel.callisaya@poiesisconsulting.com
import time
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from odoo.addons import decimal_precision as dp
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class StockRequest(models.Model):
    _name = 'stock.request'
    _inherit = ['mail.thread']
    _order = "id desc"

    @api.onchange('warehouse_dest_id')
    def warehouse_id_change(self):
        res = {}
        if self.warehouse_dest_id:
            if 'value' not in res:
                res['value'] = {}
            if 'domain' not in res:
                res['domain'] = {}
            all_routes = []
            if self.warehouse_id:
                all_routes += self.warehouse_dest_id._get_all_routes()
                # domain = [('id', 'in', all_routes)]
                all_r = []
                for router_id in all_routes:
                    router = self.env['stock.location.route'].browse(router_id.id)
                    if router.pull_ids:
                        for pulls in router.pull_ids:
                            if pulls.propagate_warehouse_id.id == self.warehouse_id.id:
                                all_r.append(router_id)

                res['domain']['route_id'] = [('id', 'in', all_r)]
            else:
                all_routes += self.warehouse_dest_id._get_all_routes()
                all_ids = []
                for rout in all_routes:
                    all_ids.append(rout.id)
                res['domain']['route_id'] = [('id', 'in', all_ids)]
        return res

    @api.onchange('route_id')
    def route_id_change(self):
        res = {}
        if self.warehouse_dest_id:
            if 'value' not in res:
                res['value'] = {}
            if 'domain' not in res:
                res['domain'] = {}
            all_routes = []
            if self.warehouse_id:
                all_routes += self.warehouse_dest_id._get_all_routes()
                all_r = []
                for router_id in all_routes:
                    router = self.env['stock.location.route'].browse(router_id)
                    if router.pull_ids:
                        for pulls in router.pull_ids:
                            if pulls.propagate_warehouse_id.id == self.warehouse_id.id:
                                all_r.append(router_id)

                res['domain']['route_id'] = [('id', 'in', all_r)]
            else:
                all_routes += self.warehouse_dest_id._get_all_routes()
                all_ids = []
                for rout in all_routes:
                    all_ids.append(rout.id)
                res['domain']['route_id'] = [('id', 'in', all_ids)]
        return res

    @api.depends('request_lines.move_ids.state',
                 'request_lines.move_ids.picking_id')
    def _compute_picking(self):
        for request in self:
            pickings = self.env['stock.picking']
            for line in request.request_lines:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids
                pickings |= moves.mapped('picking_id')
            request.picking_ids = pickings
            request.picking_count = len(pickings)

    @api.one
    @api.depends('location_id', 'location_dest_id', 'warehouse_id', 'warehouse_dest_id')
    def _get_sources(self):
        origin = ''
        destination = ''
        if self.warehouse_id:
            origin = self.warehouse_id.name
        elif self.location_id:
            origin = self.location_id.complete_name

        if self.warehouse_dest_id:
            destination = self.warehouse_dest_id.name
        elif self.location_dest_id:
            destination = self.location_dest_id.complete_name

        self.origin = origin
        self.destination = destination

    name = fields.Char(string='Name', index=True, readonly=True, default='Borrador', copy=False)
    description = fields.Char(string='Request Description')
    warehouse_id = fields.Many2one('stock.warehouse', string='From')
    route_id = fields.Many2one('stock.location.route', string='Usar Ruta',
                               states={'requested': [('readonly', True)], 'sent': [('readonly', True)]})
    warehouse_dest_id = fields.Many2one('stock.warehouse', string='To')
    use_location_id = fields.Boolean(string='Use location id', default=False)
    location_id = fields.Many2one('stock.location', string='From')
    use_location_dest_id = fields.Boolean(string='Use location id', default=False)
    location_dest_id = fields.Many2one('stock.location', string='To')
    origin = fields.Char(string='Origin', compute=_get_sources, copy=False)
    destination = fields.Char(string='Destination', compute=_get_sources, copy=False)
    notes = fields.Text('Notes')
    state = fields.Selection([('draft', 'Draft'),
                              ('requested', 'Requested'),
                              ('partially_sent', 'Partially Sent'),
                              ('sent', 'Completed'),
                              ('denied', 'Denied'),
                              ('cancel', 'Cancel')], 'State',
                             default='draft',
                             copy=False,
                             track_visibility='always')
    request_lines = fields.One2many('stock.request.line', 'request_id', 'Requested Lines',
                                    states={'requested': [('readonly', True)], 'sent': [('readonly', True)]}, copy=True)
    requestor = fields.Many2one('res.users', string='Requestor', copy=False, track_visibility='always')
    request_date = fields.Datetime('Request Date', required=True, default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    request_date_planned = fields.Datetime('Date Planned', required=True,
                                           default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('stock.request'))

    picking_count = fields.Integer(string='# Albarnes', readonly=True, compute='_compute_picking', default=0,
                                   store=True)
    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking', string='Albaranes', copy=False,
                                   store=True)
    type = fields.Selection([('sending', 'Sending'), ('request', 'Request')], 'Type')

    procurement_group_id = fields.Many2one('procurement.group', string=u'Grupo de Abastecimiento')

    # def copy(self, cr, uid, id, default=None, context=None):
    #     request = self.browse(cr, uid, id, context=context)
    #     default.update(
    #         name=_("%s (copy)") % (request['name'] or ''),
    #         state='draft',
    #         request_id=id)
    #     return super(StockRequest, self).copy(cr, uid, id, default, context=context)

    @api.multi
    def _create_stock_request(self, request_description, request_lines, request_data=None, type='request'):

        request_line_obj = self.env['stock.request.line']
        product_obj = self.env['product.product']

        warehouse_id = None
        location_id = None
        use_location_id = False

        warehouse_dest_id = None
        location_dest_id = None
        use_location_dest_id = False

        if not request_data:
            request_data = {}

        if request_data.get('warehouse_id'):
            warehouse_id = request_data['warehouse_id']
        elif request_data.get('location_id'):
            location_id = request_data['location_id']
            use_location_id = True

        if request_data.get('warehouse_dest_id'):
            warehouse_dest_id = request_data['warehouse_dest_id']
        elif request_data.get('location_dest_id'):
            location_dest_id = request_data['location_dest_id']
            use_location_dest_id = True

        if not request_lines:
            raise Warning(_('Error'), _('Request MUST have lines'))

        val_request = {'description': request_description,
                       'warehouse_id': warehouse_id,
                       'location_id': location_id,
                       'use_location_id': use_location_id,
                       'warehouse_dest_id': warehouse_dest_id,
                       'location_dest_id': location_dest_id,
                       'use_location_dest_id': use_location_dest_id,
                       'requestor': self._uid,
                       'type': type,
                       'picking_id': request_data.get('picking_id') or None,
                       }
        request_id = self.create(val_request)

        for line in request_lines:
            product = product_obj.browse(line.get('product_id'))
            val_line_request = {'product_id': line.get('product_id'),
                                'product_uom_qty': line.get('quantity') or 0.0,
                                'product_uom': line.get('product_uom_id') or product.uom_id.id,
                                'request_id': request_id.id,
                                'lot_id': line.get('lot_id') or False}
            request_line_obj.create(val_line_request)

        return request_id

    @api.multi
    def create_request(self, request_description, request_lines, request_data=None):

        if not request_data:
            request_data = {}

        mod_obj = self.env['ir.model.data']

        warehouse_dest = request_data['warehouse_dest_id']
        request_data['warehouse_dest_id'] = False
        request_id = self._create_stock_request(request_description, request_lines, request_data=request_data,
                                                type='request')
        request_id.warehouse_dest_id = warehouse_dest
        res = mod_obj.get_object_reference('poi_stock_request', 'view_stock_request_form')
        res_id = res and res[1] or False,

        return {
            'name': _('Stock Request'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'stock.request',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': request_id.id,
        }

    @api.multi
    def create_sending(self, cr, uid, request_description, request_lines, request_data, context=None):

        if not request_data:
            request_data = {}

        mod_obj = self.env['ir.model.data']

        request_id = self._create_stock_request(request_description, request_lines, request_data=request_data,
                                                type='sending', context=context)

        res = mod_obj.get_object_reference(cr, uid, 'poi_stock_request', 'view_sending_stock_form')
        res_id = res and res[1] or False,

        return {
            'name': _('Sending Stock'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'stock.request',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': request_id,
        }

    @api.multi
    def unlink(self):
        for request in self:
            if request.state not in ('draft', 'cancel'):
                raise Warning(_('You cannot delete a request which is not draft or cancelled.'))
        return super(StockRequest, self).unlink()

    # Funcion que crea los abastecimientos
    @api.multi
    def action_picking_create(self):
        errors = []
        if self.type == 'request':
            request_name = self.env['ir.sequence'].next_by_code('stock.request.in') or '/'
        elif self.type == 'sending':
            request_name = self.env['ir.sequence'].next_by_code('stock.request.out') or '/'

        self.requestor = self._uid
        self.name = request_name
        for request in self:
            for line in request.request_lines:

                if line.product_uom_qty <= 0:
                    raise Warning(_('Error! Esta solicitando un producto con cantidad 0'))

                if not line.lot_id and line.product_id.tracking in ('serial', 'lot'):
                    raise Warning(_('Error! El producto %s, requiere que registre lote o serie' % line.product_id.name))

                group_ab = line.request_id.procurement_group_id
                if not group_ab:
                    group_ab = self.env["procurement.group"].create({'name': request.name, 'move_type': 'direct'})
                    line.request_id.procurement_group_id = group_ab

                values = line._prepare_procurement_values(group_id=group_ab)
                product_qty = line.product_uom_qty
                procurement_uom = line.product_uom
                quant_uom = line.product_id.uom_id
                get_param = self.env['ir.config_parameter'].sudo().get_param
                if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                    product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                    procurement_uom = quant_uom

                try:
                    self.env['procurement.group'].run(line.product_id, product_qty, procurement_uom,
                                                      line.request_id.warehouse_dest_id.lot_stock_id,
                                                      line.product_id.name, line.request_id.name, values)
                except UserError as error:
                    errors.append(error.name)

            self.state = 'requested'
            self.picking_ids.action_assign()
            #     pull_id = False
            #     # Actualizar aca el punto de crear los abastecimientos
            #     # para efectuar la creación de albaranes
            #     if len(request.route_id.pull_ids) <= 1:
            #         for pulls in request.route_id.pull_ids:
            #             pull_id = pulls.id
            #         vals = {
            #             'product_id': line.product_id.id,
            #             'product_uom': line.product_uom.id,
            #             'product_qty': line.product_uom_qty,
            #             'warehouse_id': request.warehouse_dest_id.id,
            #             'location_id': request.warehouse_dest_id.lot_stock_id.id,
            #             'name': request.name,
            #             'route_ids': [(4, request.route_id.id)],
            #             'group_id': group_ab.id,
            #             'request_line_id': line.id,
            #             'rule_id': pull_id,
            #             'date_planned': request.request_date_planned,
            #             'lot_id': line.lot_id.id or False,
            #         }
            #     else:
            #         vals = {
            #             'product_id': line.product_id.id,
            #             'product_uom': line.product_uom.id,
            #             'product_qty': line.product_uom_qty,
            #             'warehouse_id': request.warehouse_dest_id.id,
            #             'location_id': request.warehouse_dest_id.lot_stock_id.id,
            #             'name': request.name,
            #             'route_ids': [(4, request.route_id.id)],
            #             'group_id': group_ab.id,
            #             'request_line_id': line.id,
            #             'origin': request.name,
            #             'date_planned': request.request_date_planned,
            #             'lot_id': line.lot_id.id or False,
            #         }
            #     procu = self.env['procurement.order'].create(vals)
            #     procu.run()
            #
            # pickings = self.env['stock.picking'].search([('group_id', '=', group_ab.id)])
            # for picking in pickings:
            #     picking.request_id = request.id
            #     picking.action_assign()

    @api.multi
    def action_view_picking(self):
        '''
        Funcion utilizada  de compras para ver los albaranes de una
        Solicitud de stock
        '''
        action = self.env.ref('stock.action_picking_tree')
        result = action.read()[0]

        # override the context to get rid of the default filtering on operation type
        result['context'] = {}
        pick_ids = self.mapped('picking_ids')
        # choose the view_mode accordingly
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids.id
        return result


class stock_request_line(models.Model):
    _name = 'stock.request.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        location_id = self.request_id.route_id.supplier_wh_id.lot_stock_id.id
        lot_ids = []
        quant_ids = self.env['stock.quant'].search(
             [('location_id', '=', location_id), ('product_id', '=', self.product_id.id)])
        for quant in quant_ids:
            if quant.reserved_quantity < quant.quantity:
                lot_ids.append(quant.lot_id.id)
        self.product_uom = self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)],
                            'lot_id': [('product_id', '=', self.product_id.id), ('id', 'in', lot_ids)]}

        return result

    @api.onchange('lot_id')
    def onchange_lot_id(self):
        result = {}
        if not self.lot_id:
            return result
        location_id = self.request_id.route_id.supplier_wh_id.lot_stock_id.id
        quant_ids = self.env['stock.quant'].search(
            [('location_id', '=', location_id), ('product_id', '=', self.product_id.id), ('lot_id', '=', self.lot_id.id)])
        qty_available = 0.0
        for quant in quant_ids:
            qty_available = quant.quantity - quant.reserved_quantity

        self.product_uom_qty = qty_available
        return result

    # @api.multi
    # def product_id_change(self, product_id, product_uom, product_uom_qty, route_id):
    #     res = self.on_change_tests(product_id, product_uom, product_uom_qty)
    #     if 'value' not in res:
    #         res['value'] = {}
    #     if 'domain' not in res:
    #         res['domain'] = {}
    #
    #     if product_id and not product_uom:
    #         product = self.env['product.product'].browse(product_id)
    #         res['value']['product_uom'] = product.uom_id.id
    #     routes = self.env['stock.location.route'].browse(route_id)
    #
    #     loc_ids = []
    #     for pull in routes.pull_ids:
    #         loc_ids.append(pull.propagate_warehouse_id.lot_stock_id.id)
    #         break
    #     quant_ids = self.env['stock.quant'].search(
    #         [('location_id', 'in', loc_ids), ('product_id', '=', product_id), ('reservation_id', '=', False)])
    #     lot_ids = []
    #     for quant in quant_ids:
    #         lot_ids.append(quant.lot_id.id)
    #     res['domain']['lot_id'] = [('id', 'in', lot_ids)]
    #     return res

    @api.one
    def _qty_calc(self):
        qty_total = self.product_uom_qty
        procurement_obj = self.pool.get('procurement.order')

        if self.request_id.state in ('requested', 'partially_sent', 'sent'):
            move_ids = self.move_ids
            qty_processed = 0.0
            qty_pending = 0.0
            for move in move_ids:
                if move.state == 'done' and move.location_id.usage == 'transit':
                    qty_processed += move.product_uom_qty
                elif move.state != 'done' and move.state != 'cancel' and move.location_id.usage == 'transit':
                    qty_pending += move.product_uom_qty

            self.qty_processed = qty_processed
            self.qty_pending = qty_pending
            self.qty_lost = qty_total - qty_processed - qty_pending
        else:
            self.qty_processed = 0
            self.qty_pending = 0
            self.qty_lost = 0

    request_id = fields.Many2one('stock.request', 'Stock Request')
    product_id = fields.Many2one('product.product', 'Product', required=True, change_default=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lote')
    product_uom_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    qty_processed = fields.Float('Quantity Processed', digits_compute=dp.get_precision('Product Unit of Measure'),
                                 compute='_qty_calc')
    qty_pending = fields.Float('Quantity Pending', digits_compute=dp.get_precision('Product Unit of Measure'),
                               compute='_qty_calc')
    qty_lost = fields.Float('Quantity Lost', digits_compute=dp.get_precision('Product Unit of Measure'),
                            compute='_qty_calc')
    move_ids = fields.One2many('stock.move', 'request_line_id', string='Reservas', readonly=True,
                               ondelete='set null', copy=False)

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        """ Prepara los datos especificos para crear el abastecimiento
        """
        values = {}
        self.ensure_one()
        date_planned = datetime.strptime(self.request_id.request_date_planned, DEFAULT_SERVER_DATETIME_FORMAT) \
                       + timedelta(days=1 or 0.0) - timedelta(days=self.request_id.company_id.security_lead)
        values.update({
            'company_id': self.request_id.company_id,
            'group_id': group_id,
            'date_planned': date_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'route_ids': self.request_id.route_id,
            'warehouse_id': self.request_id.warehouse_dest_id or False,
            'request_line_id': self.id,
        })
        return values
