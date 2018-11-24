##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2017 CodUP (<http://codup.com>).
#
##############################################################################

import time
from odoo import api, fields, models, _
from odoo import netsvc
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import Warning, UserError

class PoiWorkshopInventory(models.Model):
    _name = 'poi.workshop.inventory'
    name = fields.Char('Nombre')


class PoiWorkshopInventoryList(models.Model):
    _name = 'poi.workshop.inventory.list'
    workshop_id = fields.Many2one("workshop.order", string=u"Orden de Trabajo")
    inventory_id = fields.Many2one("poi.workshop.inventory", string=u"Inventario")
    valido = fields.Boolean(string=u"Si")
    valor = fields.Char(string=u"N° Piezas")


class workshop_order(models.Model):
    """
    Maintenance Orders
    """
    _name = 'workshop.order'
    _description = 'Maintenance Order'
    _inherit = ['mail.thread']

    STATE_SELECTION = [
        ('draft', 'DRAFT'),
        ('released', 'PLANNED'),
        ('ready', 'APPROVED'),
        ('stop', 'STOP'),
        ('invoiced', 'INVOICED'),
        ('done', 'DONE'),
        ('cancel', 'CANCELED')
    ]

    MAINTENANCE_TYPE_SELECTION = [
        ('bm', 'Preventivo'),
        ('cm', 'Correctivo'),
        ('ch', 'Chaperio')
    ]

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'ready':
            return 'workshop.mt_order_confirmed'
        return super(workshop_order, self)._track_subtype(init_values)

    def _get_available_parts(self):
        for order in self:
            line_ids = []
            available_line_ids = []
            done_line_ids = []
            # if order.procurement_group_id:
            #     for procurement in order.procurement_group_id.procurement_ids:
            #         line_ids += [move.id for move in procurement.move_ids if
            #                      move.location_dest_id.id == order.workshop_type.location_ext_id.id]
            #
            #         line_ids += [move.id for move in procurement.move_ids if
            #                      move.location_dest_id.id == order.workshop_type.location_int_id.id]
            #
            #         available_line_ids += [move.id for move in procurement.move_ids if
            #                                move.location_dest_id.id == order.workshop_type.location_ext_id.id and move.state == 'assigned']
            #
            #         available_line_ids += [move.id for move in procurement.move_ids if
            #                                move.location_dest_id.id == order.workshop_type.location_int_id.id and move.state == 'assigned']
            #
            #         done_line_ids += [move.id for move in procurement.move_ids if
            #                           move.location_dest_id.id == order.workshop_type.location_ext_id.id and move.state == 'done']
            #
            #         done_line_ids += [move.id for move in procurement.move_ids if
            #                           move.location_dest_id.id == order.workshop_type.location_int_id.id and move.state == 'done']

            order.parts_ready_lines = line_ids
            order.parts_move_lines = available_line_ids
            order.parts_moved_lines = done_line_ids

    @api.depends('parts_lines.move_ids.state',
                 'parts_lines.move_ids.picking_id')
    def _compute_picking_ids(self):
        for maintenance in self:
            pickings = self.env['stock.picking']
            for line in maintenance.parts_lines:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids
                pickings |= moves.mapped('picking_id')
            maintenance.picking_ids = pickings
            maintenance.picking_count = len(pickings)

            #order.picking_ids = self.env['stock.picking'].search(
            #    [('group_id', '=', order.procurement_group_id.id)]) if order.procurement_group_id else []
            #order.delivery_count = len(order.picking_ids)

    @api.one
    @api.depends('services_lines', 'services_lines.price_unit', 'services_lines.parts_qty')
    def _compute_total_services(self):
        for workshop in self:
            if workshop.services_lines:
                workshop.update({
                    'total_services': sum([x.price_unit * x.parts_qty for x in self.services_lines])
                })
            else:
                workshop.update({
                    'total_services': 0
                })

    @api.one
    @api.depends('parts_lines', 'parts_lines.price_unit', 'parts_lines.parts_qty')
    def _compute_total_items(self):
        for workshop in self:
            if workshop.parts_lines:
                workshop.update({
                    'total_items': sum([x.price_unit * x.parts_qty for x in self.parts_lines])
                })
            else:
                workshop.update({
                    'total_items': 0
                })

    @api.one
    @api.depends('total_services', 'total_items')
    def _compute_amount_total(self):
        self.amount_total = self.total_services + self.total_items

    @api.depends('services_lines', 'parts_lines')
    def _compute_invoice(self):
        for workshop in self:
            invoices = self.env['account.invoice']
            invoices_ids = []
            total_facturado = 0
            total_ext_ot = 0
            for line in workshop.services_lines:
                invoice_lines = self.env['account.invoice.line'].search([('service_line_id', '=', line.id)])
                for line_invoice in invoice_lines:
                    invoices_ids.append(line_invoice.invoice_id.id)
                if line.cargo == 'externo':
                    total_ext_ot += (line.price_unit * line.parts_qty)

            for line in workshop.parts_lines:
                invoice_lines = self.env['account.invoice.line'].search([('item_line_id', '=', line.id)])
                for line_invoice in invoice_lines:
                    invoices_ids.append(line_invoice.invoice_id.id)
                if line.cargo == 'externo':
                    total_ext_ot += (line.price_unit * line.parts_qty)

            output = []
            seen = set()
            for value in invoices_ids:
                if value not in seen:
                    output.append(value)
                    seen.add(value)

            for out in output:
                invoice = self.env['account.invoice'].browse(out)
                if invoice.state in ('open', 'paid'):
                    total_facturado += invoice.amount_total
            if total_ext_ot > 0:
                workshop.invoice_porcentaje = (total_facturado / total_ext_ot) * 100
            workshop.invoice_ids = output
            workshop.invoice_count = len(output)

    name = fields.Char('Reference', size=64, copy=False)

    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
                             help="When the maintenance order is created the status is set to 'Draft'.\n\
        If the order is confirmed the status is set to 'Waiting Parts'.\n\
        If the stock is available then the status is set to 'Ready to Maintenance'.\n\
        When the maintenance is over, the status is set to 'Done'.", default='draft')
    maintenance_type = fields.Selection(MAINTENANCE_TYPE_SELECTION, 'Maintenance Type', required=True, readonly=True,
                                        states={'draft': [('readonly', False)]}, default='bm')
    task_id = fields.Many2one('workshop.task', 'Task', readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Char('Description', size=64, translate=True, required=True, readonly=True,
                              states={'draft': [('readonly', False)]})

    parts_lines = fields.One2many('workshop.order.parts.line', 'maintenance_id', 'Planned parts',
                                  readonly=True,
                                  states={'draft': [('readonly', False)], 'released': [('readonly', False)],
                                          'ready': [('readonly', False)]})

    services_lines = fields.One2many('workshop.order.service.line', 'maintenance_id', 'Planned services',
                                     readonly=True,
                                     states={'draft': [('readonly', False)], 'released': [('readonly', False)],
                                             'ready': [('readonly', False)]})

    parts_ready_lines = fields.One2many('stock.move', compute='_get_available_parts')
    parts_move_lines = fields.One2many('stock.move', compute='_get_available_parts')
    parts_moved_lines = fields.One2many('stock.move', compute='_get_available_parts')
    tools_description = fields.Text('Tools Description', translate=True)
    labor_description = fields.Text('Labor Description', translate=True)
    operations_description = fields.Text('Operations Description', translate=True)
    documentation_description = fields.Text('Documentation Description', translate=True)
    problem_description = fields.Text('Problem Description')

    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('workshop.order'))
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement group', copy=False)
    category_ids = fields.Many2many(related='asset_id.category_ids', string='Asset Category', readonly=True)
    wo_id = fields.Many2one('workshop.workorder', 'Work Order', ondelete='cascade')
    workshop_type = fields.Many2one('workshop.type', string=u'Tipo OT', readonly=True,
                                    states={'draft': [('readonly', False)]})
    recosteo = fields.Boolean(related='workshop_type.recosteo', string=u'Recosteo', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'Client', domain=[('customer', '=', True)], readonly=True,
                                 states={'draft': [('readonly', False)]})
    email = fields.Char(related="partner_id.email", string="Email", readonly=True,
                        states={'draft': [('readonly', False)]})
    phone = fields.Char(related="partner_id.phone", string="Phone", readonly=True,
                        states={'draft': [('readonly', False)]})
    user_id = fields.Many2one('res.users', 'Service advisor', default=lambda self: self._uid, readonly=True,
                              states={'draft': [('readonly', False)]})
    user_tec_id = fields.Many2one('res.users', u'Asesor Técnico', readonly=True,
                                  states={'draft': [('readonly', False)]})
    asset_id = fields.Many2one('poi.vehicle', u'Vehículo', required=False, readonly=True,
                               states={'draft': [('readonly', False)]})
    chasis_id = fields.Many2one(related='asset_id.chasis_id', string=u'Lote/Chasis', readonly=True,
                                states={'draft': [('readonly', False)]})
    marca = fields.Many2one('marca.toyosa', string=u'Marca', readonly=True, states={'draft': [('readonly', False)]})
    modelo = fields.Many2one('modelo.toyosa', 'Modelo', readonly=True, states={'draft': [('readonly', False)]})
    n_chasis = fields.Char(u'N° Chasis', readonly=True, states={'draft': [('readonly', False)]})
    kilometraje = fields.Float(u'Kilometraje', readonly=True, states={'draft': [('readonly', False)]})
    n_gasolina = fields.Float(u'Nivel de Gasolina', readonly=True, states={'draft': [('readonly', False)]})

    cita_origin = fields.Char('Cita Origen', size=64, readonly=True, states={'draft': [('readonly', False)]},
                              help='Referencia de la Cita de Origen.')
    origin = fields.Char('Sale Source Document', size=64, readonly=True, states={'draft': [('readonly', False)]},
                         help='Reference of the document that generated this maintenance order.')
    ot_antecedente = fields.Many2one('workshop.order', string=u'OT Antecedente',
                                     states={'draft': [('readonly', False)]})
    # user_tec_id = fields.Many2one('res.users', 'Technical advisor', default=lambda self: self._uid)
    no_fir = fields.Char(u'N° FIR', readonly=True, states={'draft': [('readonly', False)]})
    date_planned = fields.Datetime('Fecha/hora Prevista', required=True, readonly=True,
                                   states={'draft': [('readonly', False)]}, default=time.strftime('%Y-%m-%d %H:%M:%S'))

    date_scheduled = fields.Datetime(u'Fecha/hora de recepción', required=True, readonly=True,
                                     states={'draft': [('readonly', False)], 'released': [('readonly', False)],
                                             'ready': [('readonly', False)]},
                                     default=time.strftime('%Y-%m-%d %H:%M:%S'))

    dates_lines = fields.One2many('workshop.order.dates', 'maintenance_id', 'Dates planned')

    date_execution = fields.Datetime('Date of delivery', required=False,
                                     states={'done': [('readonly', True)]}, readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string=u'Almacén Taller', readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   help=u'Considere Crear una regla de abastecimiento en el almacén para especificar los abastecimientos de Partes y Repuestos')
    stop_reason = fields.Many2one('workshop.stop.reason', readonly=True)
    state_stop = fields.Char(u'Estado Stop', help=u"Estado actual de la OT antes de detener")
    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking_ids',
                                   string='Albaranes asociados a esta OT')
    picking_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    invoice_id = fields.Many2one('account.invoice', string='Factura', readonly=True)
    inventory_test_line = fields.One2many('poi.workshop.inventory.list', 'workshop_id', string=u"Inventario Recepción",
                                          copy=True)

    group_services = fields.Many2many(
        comodel_name='workshop.task.group',
        relation='task_group_workshop_rel',
        column1='task_group_id',
        column2='workshop_id',
        string="Agrupador",
    )

    total_services = fields.Float(
        compute=_compute_total_services,
        digits_compute=dp.get_precision('Account'), string='Total Servicios', store=True)
    amount_total = fields.Float(
        compute=_compute_amount_total,
        digits_compute=dp.get_precision('Account'), string='Total')
    total_items = fields.Float(
        compute=_compute_total_items,
        digits_compute=dp.get_precision('Account'), string='Total Items', store=True)

    invoice_ids = fields.Many2many('account.invoice', compute="_compute_invoice", string='Facturas', copy=False)
    invoice_count = fields.Integer(compute="_compute_invoice", string='# de Facturas', copy=False, default=0)
    invoice_porcentaje = fields.Integer(compute="_compute_invoice", string='Porcentaje', copy=False, default=0)
    pricelist_id = fields.Many2one('product.pricelist', string=u'Tarifa', required=True, readonly=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                   help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string=u"Moneda", readonly=True,
                                  required=True)

    _order = 'date_execution'

    @api.multi
    def action_view_invoice(self):
        invoice_ids = self.mapped('invoice_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }

        if len(invoice_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_ids.ids
        elif len(invoice_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.onchange('asset_id')
    def onchange_asset(self):
        res = {}
        if self.asset_id:
            self.category_ids = self.asset_id.category_ids
            # if self.asset_id.chasis_id:
            self.marca = self.asset_id.chasis_id.marca.id or self.asset_id.marca.id
            self.modelo = self.asset_id.chasis_id.modelo.id or self.asset_id.modelo.id
            self.n_chasis = self.asset_id.chasis_id.name or self.asset_id.n_chasis
            if self.asset_id.vendor_id:
                self.partner_id = self.asset_id.vendor_id.id

            ids_d = sorted([self.user_id.shop_assigned.id] + self.user_id.shop_ids.ids)
            # Actualizar domain dinamicamente para no tener que aplicar restricción de almacenes
            res.setdefault('domain', {})
            res['domain'] = {'warehouse_id': [('id', 'in', ids_d)]}
        return res
        # return {'domain': {'task_id': [('category_id', 'in', self.category_ids.ids),
        #                               ('maintenance_type', '=', self.maintenance_type)], 'warehouse_id': [('id', 'in', ids_d)]}}

    @api.onchange('user_id')
    def onchange_user_id(self):
        res = {}
        res.setdefault('domain', {})
        ids_d = sorted([self.user_id.shop_assigned.id] + self.user_id.shop_ids.ids)
        res['domain'] = {'warehouse_id': [('id', 'in', ids_d)]}
        return res

    @api.onchange('chasis_id')
    def onchange_chasis_id(self):
        if self.chasis_id:
            vehicle_obj = self.env['poi.vehicle'].search([('chasis_id', '=', self.chasis_id.id)])
            if vehicle_obj:
                self.asset_id = vehicle_obj[0].id
                self.category_ids = self.asset_id.category_ids
                # if self.asset_id.chasis_id:
                self.marca = self.asset_id.chasis_id.marca.id or self.asset_id.marca.id
                self.modelo = self.asset_id.chasis_id.modelo.id or self.asset_id.modelo.id
                self.n_chasis = self.asset_id.chasis_id.name or self.asset_id.n_chasis
                if self.asset_id.vendor_id:
                    self.partner_id = self.asset_id.vendor_id.id
            else:
                self.marca = self.chasis_id.marca.id or self.asset_id.marca.id
                self.modelo = self.chasis_id.modelo.id or self.asset_id.modelo.id
                self.partner_id = self.chasis_id.partner_id.id
        return {'domain': {'task_id': [('category_id', 'in', self.category_ids.ids),
                                       ('maintenance_type', '=', self.maintenance_type)]}}

    @api.onchange('workshop_type')
    def onchange_workshop_type(self):
        if not self.asset_id:
            if self.workshop_type:
                if self.workshop_type.recosteo:
                    ids_vehicle = self.env['poi.vehicle'].search(
                        [('chasis_id', '!=', False), ('active', '=', True)]).ids
                else:
                    ids_vehicle = self.env['poi.vehicle'].search([('chasis_id', '=', False), ('active', '=', True)]).ids
                return {'domain': {'asset_id': [('id', 'in', ids_vehicle)]}}

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.email = self.partner_id.email
            self.phone = self.partner_id.phone or self.partner_id.mobile
            self.pricelist_id = self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False

    # @api.onchange('date_planned')
    # def onchange_planned_date(self):
    #    self.date_scheduled = self.date_planned

    # @api.onchange('date_scheduled')
    # def onchange_scheduled_date(self):
    #    self.date_execution = self.date_scheduled

    # @api.onchange('date_execution')
    # def onchange_execution_date(self):
    #    if self.state == 'draft':
    #        self.date_planned = self.date_execution
    #    else:
    #        self.date_scheduled = self.date_execution

    @api.onchange('task_id')
    def onchange_task(self):
        task = self.task_id
        new_parts_lines = []
        for line in task.parts_lines:
            new_parts_lines.append([0, 0, {
                'name': line.name,
                'parts_id': line.parts_id.id,
                'parts_qty': line.parts_qty,
                'parts_uom': line.parts_uom.id,
            }])
        self.parts_lines = new_parts_lines
        self.description = task.name
        self.tools_description = task.tools_description
        self.labor_description = task.labor_description
        self.operations_description = task.operations_description
        self.documentation_description = task.documentation_description

    def test_ready(self):
        res = True
        for order in self:
            if order.parts_lines and order.procurement_group_id:
                states = []
                for procurement in order.procurement_group_id.procurement_ids:
                    states += [move.state not in ('assigned', 'done') for move in procurement.move_ids if
                               move.location_dest_id.id == order.workshop_type.location_ext_id.id]
                    states += [move.state not in ('assigned', 'done') for move in procurement.move_ids if
                               move.location_dest_id.id == order.workshop_type.location_int_id.id]
                if any(states) or len(states) == 0: res = False
        return res

    @api.multi
    def action_confirm(self):
        # procurement_obj = self.env['procurement.order']
        errors = []
        for order in self:
            proc_ids = []
            group_id = self.env['procurement.group'].create({'name': order.name})

            location_int_id = order.workshop_type.location_int_id
            location_ext_id = order.workshop_type.location_ext_id

            # rules_int = self.env['procurement.rule'].search(
            #     [('warehouse_id', '=', order.warehouse_id.id), ('location_id', '=', location_int_id.id),
            #      ('procure_method', '=', 'make_to_stock')],
            #     order="sequence asc")
            #
            # rules_ext = self.env['procurement.rule'].search(
            #     [('warehouse_id', '=', order.warehouse_id.id), ('location_id', '=', location_ext_id.id),
            #      ('procure_method', '=', 'make_to_stock')],
            #     order="sequence asc")
            #
            # if rules_int:
            #     for line in order.parts_lines:
            #         if not line.service_line:
            #             raise UserError(
            #                 _(
            #                     'Debe asignar un servicio al Item %s') % (
            #                     line.parts_id.name))
            #         if line.cargo == 'interno':
            #             vals = {
            #                 'name': order.name,
            #                 'origin': order.name,
            #                 'company_id': order.company_id.id,
            #                 'group_id': group_id.id,
            #                 'date_planned': order.date_planned,
            #                 'product_id': line.parts_id.id,
            #                 'product_qty': line.parts_qty,
            #                 'product_uom': line.parts_uom.id,
            #                 'location_id': location_int_id.id,
            #                 'warehouse_id': order.warehouse_id.id,
            #                 'service_line': line.service_line.id,
            #                 'parts_line': line.id,
            #                 'rule_id': rules_int[0].id
            #             }
            #             proc_id = procurement_obj.create(vals)
            #             proc_ids.append(proc_id)
            #         line.calculate = True
            # else:
            #     raise UserError(
            #         _(
            #             'No Existe Regla de Abastecimiento en el almacen %s, para la ubicación interna "%s"') % (
            #             order.warehouse_id.name,
            #             location_int_id.display_name))
            #
            # if rules_ext:
            #     for line in order.parts_lines:
            #         if not line.service_line:
            #             raise UserError(
            #                 _(
            #                     'Debe asignar un servicio al Item %s') % (
            #                     line.parts_id.name))
            #         if line.cargo == 'externo':
            #             vals = {
            #                 'name': order.name,
            #                 'origin': order.name,
            #                 'company_id': order.company_id.id,
            #                 'group_id': group_id.id,
            #                 'date_planned': order.date_planned,
            #                 'product_id': line.parts_id.id,
            #                 'product_qty': line.parts_qty,
            #                 'product_uom': line.parts_uom.id,
            #                 'location_id': location_ext_id.id,
            #                 'warehouse_id': order.warehouse_id.id,
            #                 'service_line': line.service_line.id,
            #                 'parts_line': line.id,
            #                 'rule_id': rules_ext[0].id
            #             }
            #             proc_id = procurement_obj.create(vals)
            #             proc_ids.append(proc_id)
            #         line.calculate = True
            # else:
            #     raise UserError(
            #         _(
            #             'No Existe Regla de Abastecimiento en el almacen %s, para la ubicación externa "%s"') % (
            #             order.warehouse_id.name,
            #             location_ext_id.display_name))
            # procurement_obj.run(proc_ids)
            for line in order.parts_lines:
                if line.parts_qty <= 0:
                    raise Warning(_('Error! Esta solicitando un producto con cantidad 0'))

                group_ab = line.maintenance_id.procurement_group_id
                if not group_ab:
                    group_ab = self.env["procurement.group"].create({'name': order.name, 'move_type': 'direct'})
                    line.maintenance_id.procurement_group_id = group_ab

                values = line._prepare_procurement_values(group_id=group_ab)
                product_qty = line.parts_qty
                procurement_uom = line.parts_uom
                quant_uom = line.parts_id.uom_id
                get_param = self.env['ir.config_parameter'].sudo().get_param
                if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                    product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                    procurement_uom = quant_uom

                try:
                    self.env['procurement.group'].run(line.parts_id, product_qty, procurement_uom, location_ext_id, line.parts_id.name, line.maintenance_id.name, values)
                except UserError as error:
                    errors.append(error.name)
            order.write({'state': 'released', 'procurement_group_id': group_id.id})
        return 0

    def action_ready(self):
        self.write({'state': 'ready'})
        return True

    def action_stop(self):
        self.write({'state': 'stop'})
        return True

    @api.multi
    def action_released(self):
        self.write({'state': self.state_stop})
        return True

    @api.multi
    def action_done(self):
        # Crear Coste en destino
        # Crear cabezara de costos en destinos
        self.write({'state': 'done', 'date_execution': time.strftime('%Y-%m-%d %H:%M:%S')})
        if self.workshop_type.recosteo:
            val_landed = {
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'quant_ids': [(6, 0, self.asset_id.chasis_id.quant_ids.ids)],
                'account_journal_id': self.workshop_type.journal_id.id,
            }
            cost_id = self.env['stock.landed.cost'].create(val_landed)
            for service_line in self.services_lines:
                val_lines_landed = {
                    'cost_id': cost_id.id,
                    'name': service_line.service_id.name,
                    'product_id': service_line.service_id.id,
                    'split_method': service_line.service_id.split_method,
                    'price_unit': service_line.total_cost_valuation,
                    'account_id': service_line.service_id.property_account_expense_id and service_line.service_id.property_account_expense_id.id or service_line.service_id.categ_id.property_account_expense_categ_id.id
                }
                self.env['stock.landed.cost.lines'].create(val_lines_landed)
            cost_id.compute_landed_cost_quant()
            cost_id.button_validate_quant()
            notification = _(
                '<div class="o_mail_notification">Coste en destino <a href="#id=%s&view_type=form&model=stock.landed.cost&menu_id=240&action=318" class="o_channel_redirect">%s</a> referido ha esta OT</div>') % (
                               cost_id.id, cost_id.name,)
            self.message_post(body=notification, message_type="notification", subtype="stock.landed.cost")
        else:
            # Generar asiento contable por los servicios internos que no han sido cobrados al cliente
            # Pero que si tiene un impacto contable para la empresa
            valid_ok = False
            for service in self.services_lines:
                if service.cargo == 'interno':
                    valid_ok = True

            if valid_ok:
                move = self.action_move_create()
                if move:
                    notification = _(
                        '<div class="o_mail_notification">Asiento Contable <a href="#id=%s&view_type=form&model=account.move&menu_id=139&action=163" class="o_channel_redirect">%s</a> referido ha esta OT</div>') % (
                                       move.id, move.name,)
                    self.message_post(body=notification, message_type="notification", subtype="account.move")

        # for order in self:
        # En caso de que los insumos solo se han reservado al confirmar la orden de trabajo se consumen los stocks
        #    order.parts_move_lines.action_done()

        return True

    @api.multi
    def account_move_get(self):
        if self.workshop_type.journal_id:
            if not self.workshop_type.journal_id.sequence_id.active:
                raise UserError(_('Por Favor Active la secuencia par el diario seleccionado !'))
            name = self.workshop_type.journal_id.sequence_id.with_context(
                ir_sequence_date=time.strftime(DEFAULT_SERVER_DATE_FORMAT)).next_by_id()
        elif self.name:
            name = self.name
        else:
            raise UserError(_('Por favor defina una secuencia para el diario seleccionado.'))

        move = {
            'name': name,
            'journal_id': self.workshop_type.journal_id.id,
            'narration': self.name,
            'date': self.date_execution,
            'ref': (self.name or ''),
        }
        return move

    @api.multi
    def _convert_amount(self, amount):
        return amount
        # Por si aplica cobrar en multimoneda considerar utulizar este codigo
        # for voucher in self:
        #    return voucher.currency_id.compute(amount, voucher.company_id.currency_id)

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        debit = credit = 0.0

        total = 0
        for service in self.services_lines:
            if service.cargo == 'interno' and service.service_id.purchase_ok:
                total += service.parts_qty * service.price_unit
        credit = self._convert_amount(total)
        if debit < 0.0: debit = 0.0
        if credit < 0.0: credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        if not self.workshop_type.property_account_expense_categ_id:
            raise UserError(_("Debe definir una cuenta contable para el tipo de OT"))
        # set the first line of the voucher
        if total > 0:
            move_line = {
                'name': self.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': self.workshop_type.property_account_expense_categ_id.id,
                'move_id': move_id,
                'journal_id': self.workshop_type.journal_id.id,
                'partner_id': self.partner_id.id,
                'currency_id': company_currency != current_currency and current_currency or False,
                'amount_currency': (sign * abs(total)  # amount < 0 for refunds
                                    if company_currency != current_currency else 0.0),
                'date': self.date_execution,
                'date_maturity': self.date_execution
            }
            return move_line
        else:
            return {}

    @api.multi
    def workshop_move_line_create(self, line_total, move_id, company_currency, current_currency):
        for line in self.services_lines:
            # controlar que solo sea cargo interno
            if line.cargo != 'interno':
                None
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            else:
                if line.price_unit > 0 and line.service_id.purchase_ok:
                    amount = self._convert_amount(line.price_unit * line.parts_qty)
                    account = line.service_id.product_tmpl_id._get_product_accounts()
                    move_line = {
                        'journal_id': self.workshop_type.journal_id.id,
                        'name': line.name or '/',
                        'account_id': account['expense'].id,
                        'move_id': move_id,
                        'partner_id': self.partner_id.id,
                        # 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                        'quantity': 1,
                        'credit': 0.0,
                        'debit': abs(amount),
                        'date': self.date_execution,
                        'amount_currency': amount if current_currency != company_currency else 0.0,
                        'currency_id': company_currency != current_currency and current_currency or False,
                    }

                    self.env['account.move.line'].create(move_line)
        return line_total

    @api.multi
    def action_move_create(self):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        for workshop in self:
            local_context = dict(self._context, force_company=workshop.workshop_type.journal_id.company_id.id)
            # if voucher.move_id:
            #    continue
            company_currency = workshop.workshop_type.journal_id.company_id.currency_id.id
            current_currency = company_currency
            ctx = local_context.copy()
            ctx['date'] = workshop.date_execution
            ctx['check_move_validity'] = False
            move = self.env['account.move'].create(workshop.account_move_get())
            move_data = workshop.with_context(ctx).first_move_line_get(move.id, company_currency, current_currency)
            if move_data:
                move_line = self.env['account.move.line'].with_context(ctx).create(move_data)
                line_total = move_line.debit - move_line.credit
                # Create one move line per voucher line where amount is not 0.0
                line_total = workshop.with_context(ctx).workshop_move_line_create(line_total, move.id, company_currency,
                                                                                  current_currency)
                move.post()
                return move
            else:
                move.unlink()
                return {}

    @api.multi
    def action_cancel(self):
        for order in self:
            order.parts_ready_lines.action_cancel()
        self.write({'state': 'cancel'})
        return True

    def test_if_parts(self):
        res = True
        for order in self:
            if not order.parts_lines:
                res = False
        return res

    @api.multi
    def force_done(self):
        # self.force_parts_reservation()
        #wf_service = netsvc.LocalService("workflow")
        if self.workshop_type.recosteo:
            for picking in self.picking_ids:
                if picking.state in ('done', 'cancel'):
                    valid_invoice = True
                else:
                    valid_invoice = False
                    break

            if not valid_invoice:
                raise UserError(_("La OT es de recosteo considere dar de baja los items para obtener los costes"))

            for order in self:
                #wf_service.trg_validate(self.env.user.id, 'workshop.order', order.id, 'button_done', self.env.cr)
                order.action_done()

        else:
            for order in self:
                #wf_service.trg_validate(self.env.user.id, 'workshop.order', order.id, 'parts_ready', self.env.cr)
                #wf_service.trg_validate(self.env.user.id, 'workshop.order', order.id, 'button_done', self.env.cr)
                order.action_done()
        return True

    @api.multi
    def force_parts_reservation(self):
        for order in self:
            order.parts_ready_lines.force_assign()
        return True

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('workshop.order') or '/'

        res = super(workshop_order, self).create(vals)
        accesorios = self.env['poi.workshop.inventory'].search([('name', '!=', '')])
        for acc in accesorios:
            vals_accesorios = {
                'workshop_id': res.id,
                'inventory_id': acc.id,
            }
            self.env['poi.workshop.inventory.list'].create(vals_accesorios)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('date_execution') and not vals.get('state'):
            # constraint for calendar view
            for order in self:
                if order.state == 'draft':
                    vals['date_planned'] = vals['date_execution']
                    vals['date_scheduled'] = vals['date_execution']
                elif order.state in ('released', 'ready'):
                    vals['date_scheduled'] = vals['date_execution']
                else:
                    del vals['date_execution']
        return super(workshop_order, self).write(vals)

    @api.multi
    def calculate_parts(self):
        tools_txt = ''
        labor_txt = ''
        operation_txt = ''
        documentation_txt = ''
        if self.group_services and self.state in ('draft'):
            for group in self.group_services:
                new_services_lines = []
                # Crear las lineas de servicios
                for services in self.services_lines:
                    # Eliminar los servicios en estado borrador
                    services.unlink()

                for task_group_line in group.group_lines:
                    product_lang = task_group_line.service_id.with_context({
                        'lang': self.partner_id.lang,
                        'partner_id': self.partner_id.id,
                        'pricelist': self.pricelist_id.id,
                    })
                    new_services_lines.append([0, 0, {
                        'name': task_group_line.task_id.name or task_group_line.service_id.name,
                        'task_id': task_group_line.task_id.id,
                        'service_id': task_group_line.service_id.id,
                        'price_unit': product_lang.price,
                        'parts_uom': task_group_line.service_id.uom_id.id,
                        'time_prev': task_group_line.service_id.time_service,
                        'parts_qty': 1,
                        'cargo': self.workshop_type.cargo,
                        'calculate': True,
                    }])
                self.services_lines = new_services_lines
                # Crear las lineas de servicios
                for parts in self.parts_lines:
                    # No eliminar los que vienen de un pedido de ventas
                    if not parts.origin:
                        parts.unlink()

                for task_line in self.services_lines:
                    task = task_line.task_id
                    new_parts_lines = []
                    for line in task.parts_lines:
                        product_lang = line.parts_id.with_context({
                            'lang': self.partner_id.lang,
                            'partner_id': self.partner_id.id,
                            'pricelist': self.pricelist_id.id,
                        })
                        new_parts_lines.append([0, 0, {
                            'name': line.name,
                            'parts_id': line.parts_id.id,
                            'parts_qty': line.parts_qty * task_line.parts_qty,
                            'parts_uom': line.parts_uom.id,
                            'price_unit': product_lang.price,
                            'cargo': task_line.cargo,
                            'service_line': task_line.id,
                            'calculate': True,
                        }])
                    self.parts_lines = new_parts_lines
                    # self.description = task.name
                    if task:
                        if tools_txt == '':
                            tools_txt = tools_txt + '==' + (task.name or '') + '==\n'
                        else:
                            tools_txt = tools_txt + '\n==' + (task.name or '') + '==\n'
                        self.tools_description = tools_txt + (task.tools_description or '')
                        tools_txt = (self.tools_description or '')

                        if labor_txt == '':
                            labor_txt = labor_txt + '==' + (task.name or '') + '==\n'
                        else:
                            labor_txt = labor_txt + '\n==' + (task.name or '') + '==\n'
                        self.labor_description = labor_txt + (task.labor_description or '')
                        labor_txt = (self.labor_description or '')

                        if operation_txt == '':
                            operation_txt = operation_txt + '==' + (task.name or '') + '==\n'
                        else:
                            operation_txt = operation_txt + '\n==' + (task.name or '') + '==\n'
                        self.operations_description = operation_txt + (task.operations_description or '')
                        operation_txt = (self.operations_description or '')

                        if documentation_txt == '':
                            documentation_txt = documentation_txt + '==' + (task.name or '') + '==\n'
                        else:
                            documentation_txt = documentation_txt + '\n==' + (task.name or '') + '==\n'
                        self.documentation_description = documentation_txt + (task.documentation_description or '')
                        documentation_txt = (self.documentation_description or '')
        elif self.state in ('ready', 'released'):
            # for parts in self.parts_lines:
            #    if not parts.origin and not parts.calculate:
            #        parts.unlink()

            for task_line in self.services_lines:
                # Realizar las tareas para que calcule los que falta entregar
                if not task_line.calculate:
                    task = task_line.task_id
                    new_parts_lines = []
                    procurement_obj = self.env['procurement.order']
                    for order in self:
                        proc_ids = []
                        group_id = self.env['procurement.group'].search([('name', '=', order.name)])
                        if order.recosteo:
                            location_id = order.workshop_type.location_int_id
                        else:
                            location_id = order.workshop_type.location_ext_id

                        rules = self.env['procurement.rule'].search(
                            [('warehouse_id', '=', order.warehouse_id.id), ('location_id', '=', location_id.id)],
                            order="sequence asc")
                        if rules:
                            for line in order.parts_lines:
                                if not line.service_line:
                                    raise UserError(
                                        _(
                                            'Debe asignar un servicio al Item %s') % (
                                            line.parts_id.name))

                            for line in task.parts_lines:
                                product_lang = line.parts_id.with_context({
                                    'lang': self.partner_id.lang,
                                    'partner_id': self.partner_id.id,
                                    'pricelist': self.pricelist_id.id,
                                })
                                new_parts_lines.append([0, 0, {
                                    'name': line.name,
                                    'parts_id': line.parts_id.id,
                                    'parts_qty': line.parts_qty * task_line.parts_qty,
                                    'parts_uom': line.parts_uom.id,
                                    'price_unit': product_lang.price,
                                    'cargo': task_line.cargo,
                                    'service_line': task_line.id,
                                    'calculate': True,
                                }])
                                vals = {
                                    'name': order.name,
                                    'origin': order.name,
                                    'company_id': order.company_id.id,
                                    'group_id': group_id.id,
                                    'date_planned': order.date_planned,
                                    'product_id': line.parts_id.id,
                                    'product_qty': line.parts_qty,
                                    'product_uom': line.parts_uom.id,
                                    'location_id': location_id.id,
                                    'warehouse_id': order.warehouse_id.id,
                                    'service_line': task_line.id,
                                    'parts_line': line.id,
                                    # 'route_ids': line.route_id and [(4, line.route_id.id)] or [],
                                    'rule_id': rules[0].id
                                }
                                proc_id = procurement_obj.create(vals)
                                proc_ids.append(proc_id)
                            procurement_obj.run(proc_ids)
                            # order.write({'procurement_group_id': group_id.id})

                            self.parts_lines = new_parts_lines
                            # self.description = task.name
                            if tools_txt == '':
                                tools_txt = tools_txt + '==' + str(task.name) + '==\n'
                            else:
                                tools_txt = tools_txt + '\n==' + str(task.name) + '==\n'
                            self.tools_description = tools_txt + (str(task.tools_description) or '')
                            tools_txt = str(self.tools_description)

                            if labor_txt == '':
                                labor_txt = labor_txt + '==' + str(task.name) + '==\n'
                            else:
                                labor_txt = labor_txt + '\n==' + str(task.name) + '==\n'
                            self.labor_description = labor_txt + (str(task.labor_description) or '')
                            labor_txt = str(self.labor_description)

                            if operation_txt == '':
                                operation_txt = operation_txt + '==' + str(task.name) + '==\n'
                            else:
                                operation_txt = operation_txt + '\n==' + str(task.name) + '==\n'
                            self.operations_description = operation_txt + (str(task.operations_description) or '')
                            operation_txt = str(self.operations_description)

                            if documentation_txt == '':
                                documentation_txt = documentation_txt + '==' + str(task.name) + '==\n'
                            else:
                                documentation_txt = documentation_txt + '\n==' + str(task.name) + '==\n'
                            self.documentation_description = documentation_txt + (
                                        str(task.documentation_description) or '')
                            documentation_txt = str(self.documentation_description)
                        else:
                            raise UserError(
                                _(
                                    'No Existe Regla de Abastecimiento en el almacen %s, para la ubicación %s') % (
                                    order.warehouse_id.name,
                                    location_id.display_name))
                else:
                    procurement_obj = self.env['procurement.order']
                    for order in self:
                        proc_ids = []
                        group_id = self.env['procurement.group'].search([('name', '=', order.name)])
                        if order.recosteo:
                            location_id = order.workshop_type.location_int_id
                        else:
                            location_id = order.workshop_type.location_ext_id

                        rules = self.env['procurement.rule'].search(
                            [('warehouse_id', '=', order.warehouse_id.id), ('location_id', '=', location_id.id)],
                            order="sequence asc")
                        if rules:
                            for line in order.parts_lines:
                                if not line.service_line:
                                    raise UserError(
                                        _(
                                            'Debe asignar un servicio al Item %s') % (
                                            line.parts_id.name))

                            for line in order.parts_lines:
                                if not line.calculate and task_line.id == line.service_line.id:
                                    vals = {
                                        'name': order.name,
                                        'origin': order.name,
                                        'company_id': order.company_id.id,
                                        'group_id': group_id.id,
                                        'date_planned': order.date_planned,
                                        'product_id': line.parts_id.id,
                                        'product_qty': line.parts_qty,
                                        'product_uom': line.parts_uom.id,
                                        'location_id': location_id.id,
                                        'warehouse_id': order.warehouse_id.id,
                                        'service_line': task_line.id,
                                        'parts_line': line.id,
                                        # 'route_ids': line.route_id and [(4, line.route_id.id)] or [],
                                        'rule_id': rules[0].id
                                    }
                                    proc_id = procurement_obj.create(vals)
                                    proc_ids.append(proc_id)
                                procurement_obj.run(proc_ids)
        else:
            for parts in self.parts_lines:
                if not parts.origin:
                    parts.unlink()

            for task_line in self.services_lines:
                task = task_line.task_id
                new_parts_lines = []
                for line in task.parts_lines:
                    product_lang = line.parts_id.with_context({
                        'lang': self.partner_id.lang,
                        'partner_id': self.partner_id.id,
                        'pricelist': self.pricelist_id.id,
                    })
                    new_parts_lines.append([0, 0, {
                        'name': line.name,
                        'parts_id': line.parts_id.id,
                        'parts_qty': line.parts_qty * task_line.parts_qty,
                        'parts_uom': line.parts_uom.id,
                        'price_unit': product_lang.price,
                        'cargo': task_line.cargo,
                        'service_line': task_line.id,
                    }])
                self.parts_lines = new_parts_lines
                # self.description = task.name
                if tools_txt == '':
                    tools_txt = tools_txt + '==' + (task.name or '') + '==\n'
                else:
                    tools_txt = tools_txt + '\n==' + (task.name or '') + '==\n'
                self.tools_description = tools_txt + (task.tools_description or '')
                tools_txt = self.tools_description or ''

                if labor_txt == '':
                    labor_txt = labor_txt + '==' + (task.name or '') + '==\n'
                else:
                    labor_txt = labor_txt + '\n==' + (task.name or '') + '==\n'
                self.labor_description = labor_txt + (task.labor_description or '')
                labor_txt = (self.labor_description or '')

                if operation_txt == '':
                    operation_txt = operation_txt + '==' + (task.name or '') + '==\n'
                else:
                    operation_txt = operation_txt + '\n==' + (task.name or '') + '==\n'
                self.operations_description = operation_txt + (task.operations_description or '')
                operation_txt = (self.operations_description or '')

                if documentation_txt == '':
                    documentation_txt = documentation_txt + '==' + (task.name or '') + '==\n'
                else:
                    documentation_txt = documentation_txt + '\n==' + (task.name or '') + '==\n'
                self.documentation_description = documentation_txt + (task.documentation_description or '')
                documentation_txt = (self.documentation_description or '')

    @api.multi
    def calculate_parts_line(self):
        procurement_obj = self.env['procurement.order']
        if self.state in ('ready', 'released'):
            for order in self:
                proc_ids = []
                group_id = self.env['procurement.group'].search([('name', '=', order.name)])
                location_int_id = order.workshop_type.location_int_id
                location_ext_id = order.workshop_type.location_ext_id

                rules_int = self.env['procurement.rule'].search(
                    [('warehouse_id', '=', order.warehouse_id.id), ('location_id', '=', location_int_id.id),
                     ('procure_method', '=', 'make_to_stock')],
                    order="sequence asc")

                rules_ext = self.env['procurement.rule'].search(
                    [('warehouse_id', '=', order.warehouse_id.id), ('location_id', '=', location_ext_id.id),
                     ('procure_method', '=', 'make_to_stock')],
                    order="sequence asc")
                if rules_int:
                    for line in order.parts_lines:
                        if line.calculate:
                            continue
                        if not line.service_line:
                            raise UserError(
                                _(
                                    'Debe asignar un servicio al Item %s') % (
                                    line.parts_id.name))
                        if line.cargo == 'interno':
                            vals = {
                                'name': order.name,
                                'origin': order.name,
                                'company_id': order.company_id.id,
                                'group_id': group_id.id,
                                'date_planned': order.date_planned,
                                'product_id': line.parts_id.id,
                                'product_qty': line.parts_qty,
                                'product_uom': line.parts_uom.id,
                                'location_id': location_int_id.id,
                                'warehouse_id': order.warehouse_id.id,
                                'service_line': line.service_line.id,
                                'parts_line': line.id,
                                'rule_id': rules_int[0].id
                            }
                            proc_id = procurement_obj.create(vals)
                            proc_ids.append(proc_id)
                            line.calculate = True

                else:
                    raise UserError(
                        _(
                            'No Existe Regla de Abastecimiento en el almacen %s, para la ubicación interna "%s"') % (
                            order.warehouse_id.name,
                            location_int_id.display_name))

                if rules_ext:
                    for line in order.parts_lines:
                        if line.calculate:
                            continue
                        if not line.service_line:
                            raise UserError(
                                _(
                                    'Debe asignar un servicio al Item %s') % (
                                    line.parts_id.name))
                        if line.cargo == 'externo':
                            vals = {
                                'name': order.name,
                                'origin': order.name,
                                'company_id': order.company_id.id,
                                'group_id': group_id.id,
                                'date_planned': order.date_planned,
                                'product_id': line.parts_id.id,
                                'product_qty': line.parts_qty,
                                'product_uom': line.parts_uom.id,
                                'location_id': location_ext_id.id,
                                'warehouse_id': order.warehouse_id.id,
                                'service_line': line.service_line.id,
                                'parts_line': line.id,
                                # 'route_ids': line.route_id and [(4, line.route_id.id)] or [],
                                'rule_id': rules_ext[0].id
                            }
                            proc_id = procurement_obj.create(vals)
                            proc_ids.append(proc_id)
                            line.calculate = True
                else:
                    raise UserError(
                        _(
                            'No Existe Regla de Abastecimiento en el almacen %s, para la ubicación externa "%s"') % (
                            order.warehouse_id.name,
                            location_ext_id.display_name))
                procurement_obj.run(proc_ids)

    @api.multi
    def action_view_items(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }

        pick_ids = sum([order.picking_ids.ids for order in self], [])

        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            form = self.env.ref('stock.view_picking_form', False)
            form_id = form.id if form else False
            result['views'] = [(form_id, 'form')]
            result['res_id'] = pick_ids[0]
        return result


class workshop_order_dates(models.Model):
    _name = 'workshop.order.dates'
    _description = 'Maintenance Planned Dates'

    date_planned = fields.Datetime('Fecha/hora Prevista', required=True, default=time.strftime('%Y-%m-%d %H:%M:%S'))

    reason = fields.Char('Motivo', size=200)
    observations = fields.Char('Observaciones', size=200)
    maintenance_id = fields.Many2one('workshop.order', 'Maintenance Order')

    def unlink(self):
        self.write({'maintenance_id': False})
        return True


class workshop_order_service_line(models.Model):
    _name = 'workshop.order.service.line'
    _description = 'Maintenance Planned Service'

    def _get_cost_total(self):
        for line in self:
            total = 0.0
            # if line.maintenance_id.procurement_group_id:
            #     for procurement in line.maintenance_id.procurement_group_id.procurement_ids:
            #         if procurement.service_line.id == line.id:
            #             for move in procurement.move_ids:
            #                 if move.location_dest_id.id == line.maintenance_id.workshop_type.location_ext_id.id and move.state == 'done':
            #                     for quant in move.quant_ids:
            #                         if quant.qty > 0:
            #                             total += quant.inventory_value
            #                 if move.location_dest_id.id == line.maintenance_id.workshop_type.location_int_id.id and move.state == 'done':
            #                     for quant in move.quant_ids:
            #                         if quant.qty > 0:
            #                             total += quant.inventory_value

            line.total_cost_valuation = total + (line.parts_qty * line.price_unit)

    task_id = fields.Many2one('workshop.task', 'Servicio/Repuestos', required=False)
    cargo = fields.Selection([
        ('interno', 'Interno'),
        ('externo', 'Externo'),
    ], required=True, default='interno',
        help="El 'Interno' usado para generar asiento contable costo asumido\n " \
             "El uso 'Externo' para generar factura y el cargo esta asignado al cliente " \
             "")
    service_id = fields.Many2one('product.product', 'Service Item', required=True)
    name = fields.Char('Description', size=64)
    parts_qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    parts_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    time_prev = fields.Float('Horas Previstas', help="Horas previstas para el servicio")
    time_real = fields.Float('Horas Reales', help="Horas reales por el servicio")
    total_cost_valuation = fields.Float('Costo + Repuestos', compute='_get_cost_total',
                                        help="Costo de Servicio + repuestos utilizados")
    mecanico = fields.Many2one('res.partner', help=u"Mecánico")
    maintenance_id = fields.Many2one('workshop.order', 'Maintenance Order')
    partner_id = fields.Many2one('res.partner', related='maintenance_id.partner_id', string='Partner', readonly=True,
                                 store=True)
    return_parts = fields.Boolean("Devolver?")
    calculate = fields.Boolean("Calculado")

    @api.onchange('task_id')
    def onchange_parts(self):
        self.service_id = self.task_id.product_id.id
        if self.maintenance_id.workshop_type:
            self.cargo = self.maintenance_id.workshop_type.cargo

    @api.onchange('return_parts')
    def onchange_return_parts(self):
        for line in self:
            parts = self.env['workshop.order.parts.line'].search([('service_line', '=', self._origin.id)])
            for part in parts:
                if self.return_parts:
                    self._cr.execute(
                        "update workshop_order_parts_line set return_parts = True where id =" + str(part.id) + "")
                else:
                    part.return_parts = False

    @api.onchange('service_id')
    def onchange_service(self):
        if self.service_id:
            product_lang = self.service_id.with_context({
                'lang': self.partner_id.lang,
                'partner_id': self.partner_id.id,
                'pricelist': self.maintenance_id.pricelist_id.id,
            })
            self.name = product_lang.display_name
            if product_lang.description_purchase:
                self.name += '\n' + product_lang.description_purchase

            self.parts_uom = product_lang.uom_id
            self.price_unit = product_lang.price

    @api.multi
    def unlink(self):
        for service in self:
            service.write({'maintenance_id': False})
        return True

    # @api.model
    # def create(self, values):
    #     ids = self.search(
    #         [('maintenance_id', '=', values['maintenance_id']), ('service_id', '=', values['service_id'])])
    #     if len(ids) > 0:
    #         values['parts_qty'] = ids[0].parts_qty + values['parts_qty']
    #         ids[0].write(values)
    #         return ids[0]
    #     ids = self.search([('maintenance_id', '=', False)])
    #     if len(ids) > 0:
    #         ids[0].write(values)
    #         return ids[0]
    #     return super(workshop_order_service_line, self).create(values)


class workshop_order_parts_line(models.Model):
    _name = 'workshop.order.parts.line'
    _description = 'Maintenance Planned Parts'

    name = fields.Char('Description', size=64)
    parts_id = fields.Many2one('product.product', 'Parts', required=True)
    parts_qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    parts_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    cargo = fields.Selection([
        ('interno', 'Interno'),
        ('externo', 'Externo'),
    ], required=True, default='externo',
        help="El 'Interno' usado para facturar\n " \
             "El uso 'Externo' no genera linea de factura " \
             "")
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    mecanico = fields.Many2one('res.partner', help=u"Mecánico")
    maintenance_id = fields.Many2one('workshop.order', 'Maintenance Order')
    partner_id = fields.Many2one('res.partner', related='maintenance_id.partner_id', string='Partner', readonly=True,
                                 store=True)
    service_line = fields.Many2one('workshop.order.service.line', string=u'Line Service')
    origin = fields.Char('Origen', default='')
    return_parts = fields.Boolean("Devolver?")
    calculate = fields.Boolean("Calculado")
    route_id = fields.Many2one('stock.location.route', string='Ruta')
    move_ids = fields.One2many('stock.move', 'parts_line', string='Reservas', readonly=True,
                               ondelete='set null', copy=False)
    @api.onchange('parts_id')
    def onchange_parts(self):
        if self.parts_id:
            product_lang = self.parts_id.with_context({
                'lang': self.partner_id.lang,
                'partner_id': self.partner_id.id,
                'pricelist': self.maintenance_id.pricelist_id.id,
            })
            self.name = product_lang.display_name
            if product_lang.description_purchase:
                self.name += '\n' + product_lang.description_purchase

            self.parts_uom = product_lang.uom_id
            self.price_unit = product_lang.price

    @api.multi
    def unlink(self):
        self.write({'maintenance_id': False})
        return True

    @api.model
    def create(self, values):
        ids = self.search([('maintenance_id', '=', values['maintenance_id']), ('parts_id', '=', values['parts_id'])])
        if len(ids) > 0:
            values['parts_qty'] = ids[0].parts_qty + values['parts_qty']
            ids[0].write(values)
            return ids[0]
        ids = self.search([('maintenance_id', '=', False)])
        if len(ids) > 0:
            ids[0].write(values)
            return ids[0]
        return super(workshop_order_parts_line, self).create(values)

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        """ Prepara los datos especificos para crear el abastecimiento
        """
        values = {}
        self.ensure_one()
        date_planned = datetime.strptime(self.maintenance_id.date_planned, DEFAULT_SERVER_DATETIME_FORMAT) \
                       + timedelta(days=1 or 0.0) - timedelta(days=self.maintenance_id.company_id.security_lead)
        values.update({
            'company_id': self.maintenance_id.company_id,
            'group_id': group_id,
            'date_planned': date_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            #'route_ids': self.request_id.route_id,
            'warehouse_id': self.maintenance_id.warehouse_id or False,
            'parts_line': self.id,
        })
        return values

class workshop_task(models.Model):
    """
    Maintenance Tasks (Template for order)
    """
    _name = 'workshop.task'
    _description = 'Maintenance Task'

    MAINTENANCE_TYPE_SELECTION = [
        ('cm', 'Corrective')
    ]

    name = fields.Char('Description', size=64, required=True, translate=True)
    category_id = fields.Many2one('product.category', 'Vehicle Category', ondelete='restrict', required=True)
    product_id = fields.Many2one('product.product', 'Item Service', ondelete='restrict', required=True,
                                 domain=[('type', '=', 'service'), ('isParts', '=', True)])
    maintenance_type = fields.Selection(MAINTENANCE_TYPE_SELECTION, 'Maintenance Type', required=True, default='cm')
    parts_lines = fields.One2many('workshop.task.parts.line', 'task_id', 'Parts')
    tools_description = fields.Text('Tools Description', translate=True)
    labor_description = fields.Text('Labor Description', translate=True)
    operations_description = fields.Text('Operations Description', translate=True)
    documentation_description = fields.Text('Documentation Description', translate=True)
    active = fields.Boolean('Active', default=True)
    # time_prev = fields.Float('Horas Estimadas', help="Horas estimadas para este servicio")
    # kilometraje = fields.Float('Kilometraje', help="Kilometraje estimado para este servicio")
    # time = fields.Float('Tiempo', help="Tiempo real facturable para este servicio")
    garantia = fields.Boolean(u'Garantía', help=u"Si el servicio es un garantía para el mantenimiento")

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.name = self.product_id.name
        self.category_id = self.product_id.categ_id.id


class workshop_task_parts_line(models.Model):
    _name = 'workshop.task.parts.line'
    _description = 'Maintenance Planned Parts'

    name = fields.Char('Description', size=64)
    parts_id = fields.Many2one('product.product', 'Parts', required=True,
                               domain=['|', ('isParts', '=', True), ('type', '!=', 'service')])
    parts_qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    parts_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    task_id = fields.Many2one('workshop.task', 'Maintenance Task')

    @api.onchange('parts_id')
    def onchange_parts(self):
        self.parts_uom = self.parts_id.uom_id.id

    @api.multi
    def unlink(self):
        self.write({'task_id': False})
        return True

    @api.model
    def create(self, values):
        ids = self.search([('task_id', '=', values['task_id']), ('parts_id', '=', values['parts_id'])])
        product = self.env['product.product'].browse(values['parts_id'])
        if product.uom_id.id != values['parts_uom']:
            raise UserError(
                _('Porfavor verifique que el producto %s no se ha modificado su unidad de medida en la linea.') % (
                    product.name))
        if len(ids) > 0:
            values['parts_qty'] = ids[0].parts_qty + values['parts_qty']
            ids[0].write(values)
            return ids[0]
        ids = self.search([('task_id', '=', False)])
        if len(ids) > 0:
            ids[0].write(values)
            return ids[0]
        return super(workshop_task_parts_line, self).create(values)


class workshop_task_group(models.Model):
    """
    Maintenance Tasks (Template for order)
    """
    _name = 'workshop.task.group'

    name = fields.Char('Nombre', size=64, required=True, translate=True)
    group_lines = fields.One2many('workshop.task.group.line', 'task_group_id', 'Parts')
    active = fields.Boolean('Active', default=True)


class workshop_task_group_line(models.Model):
    _name = 'workshop.task.group.line'

    name = fields.Char('Nombre', size=64)
    task_id = fields.Many2one('workshop.task', string=u'Servicio/Repuestos')
    service_id = fields.Many2one('product.product', 'Servicio', required=True,
                                 domain=[('type', '=', 'service')])
    task_group_id = fields.Many2one('workshop.task.group', 'Maintenance Task')

    @api.onchange('task_id')
    def onchange_task_id(self):
        self.service_id = self.task_id.product_id.id
        if self.task_id.product_id:
            self.name = self.task_id.name + '|' + self.task_id.product_id.name
        else:
            self.name = self.task_id.name


class workshop_request(models.Model):
    _name = 'workshop.request'
    _description = 'Maintenance Request'
    _inherit = ['mail.thread']

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('claim', 'Claim'),
        ('run', 'Execution'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled')
    ]

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'claim':
            return 'poi_workshop.mt_request_sent'
        elif 'state' in init_values and self.state == 'run':
            return 'poi_workshop.mt_request_confirmed'
        elif 'state' in init_values and self.state == 'reject':
            return 'poi_workshop.mt_request_rejected'
        return super(workshop_request, self)._track_subtype(init_values)

    name = fields.Char('Reference', size=64)
    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
                             help="When the maintenance request is created the status is set to 'Draft'.\n\
        If the request is sent the status is set to 'Claim'.\n\
        If the request is confirmed the status is set to 'Execution'.\n\
        If the request is rejected the status is set to 'Rejected'.\n\
        When the maintenance is over, the status is set to 'Done'.", track_visibility='onchange', default='draft')
    asset_id = fields.Many2one('poi.vehicle', 'Asset', required=True, readonly=True,
                               states={'draft': [('readonly', False)]})
    cause = fields.Char('Cause', size=64, translate=True, required=True, readonly=True,
                        states={'draft': [('readonly', False)]})
    description = fields.Text('Description', readonly=True, states={'draft': [('readonly', False)]})
    reject_reason = fields.Text('Reject Reason', readonly=True)
    requested_date = fields.Datetime('Requested Date', required=True, readonly=True,
                                     states={'draft': [('readonly', False)]},
                                     help="Date requested by the customer for maintenance.",
                                     default=time.strftime('%Y-%m-%d %H:%M:%S'))
    execution_date = fields.Datetime('Execution Date', required=True, readonly=True,
                                     states={'draft': [('readonly', False)], 'claim': [('readonly', False)]},
                                     default=time.strftime('%Y-%m-%d %H:%M:%S'))
    breakdown = fields.Boolean('Breakdown', readonly=True, states={'draft': [('readonly', False)]}, default=False)
    create_uid = fields.Many2one('res.users', 'Responsible')

    @api.onchange('requested_date')
    def onchange_requested_date(self):
        self.execution_date = self.requested_date

    @api.onchange('execution_date', 'state', 'breakdown')
    def onchange_execution_date(self):
        if self.state == 'draft' and not self.breakdown:
            self.requested_date = self.execution_date

    def action_send(self):
        value = {'state': 'claim'}
        for request in self:
            if request.breakdown:
                value['requested_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
            request.write(value)

    def action_confirm(self):
        order = self.env['workshop.order']
        order_id = False
        for request in self:
            order_id = order.create({
                'date_planned': request.requested_date,
                'date_scheduled': request.requested_date,
                'date_execution': request.requested_date,
                'origin': request.name,
                'state': 'draft',
                'maintenance_type': 'bm',
                'asset_id': request.asset_id.id,
                'description': request.cause,
                'problem_description': request.description,
            })
        self.write({'state': 'run'})
        return order_id.id

    def action_done(self):
        self.write({'state': 'done', 'execution_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    def action_reject(self):
        self.write({'state': 'reject', 'execution_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    def action_cancel(self):
        self.write({'state': 'cancel', 'execution_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('workshop.request') or '/'
        return super(workshop_request, self).create(vals)


class workshop_type(models.Model):
    _name = 'workshop.type'
    _description = 'Workshop Type'

    name = fields.Char('Description', size=64)
    property_account_expense_categ_id = fields.Many2one('account.account', company_dependent=True,
                                                        string="Expense Account",
                                                        oldname="property_account_expense_categ",
                                                        domain=[('deprecated', '=', False)],
                                                        help="This account will be used for invoices to value expenses.")
    location_int_id = fields.Many2one('stock.location', 'Ubicación Interno', required=True,
                                      help='Ubicación de baja para los casos internos')
    location_ext_id = fields.Many2one('stock.location', 'Ubicación Externo', required=True,
                                      help='Ubicación de baja para los casos externos')
    recosteo = fields.Boolean(string=u'Aplica recosteo')
    journal_id = fields.Many2one(comodel_name='account.journal', string=u"Diario Contable", required=True,
                                 domain=[('type', 'in', ['purchase', 'general'])])

    cargo = fields.Selection([
        ('interno', 'Interno'),
        ('externo', 'Externo'),
    ], required=True, default='externo',
        help="El 'Interno' usado para facturar\n " \
             "El uso 'Externo' no genera linea de factura " \
             "")

    sale_type_id = fields.Many2one('sale.type', string=u"Tipo de Venta")


class workshop_stop_reason(models.Model):
    _name = 'workshop.stop.reason'
    _description = 'Workshop stop reason'

    name = fields.Char(u'Motivo')
    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
