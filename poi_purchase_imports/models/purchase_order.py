# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from odoo import models, api, fields, exceptions, registry, SUPERUSER_ID, _
import odoo.addons.decimal_precision as dp
from odoo.tools.safe_eval import safe_eval
from psycopg2 import OperationalError

import logging
import threading
STATE_COLOR_SELECTION = [
    ('0', 'Red'),
    ('1', 'Green'),
    ('2', 'Blue'),
    ('3', 'Yellow'),
    ('4', 'Magenta'),
    ('5', 'Cyan'),
    ('6', 'Black'),
    ('7', 'White'),
    ('8', 'Orange'),
    ('9', 'SkyBlue')
]
_logger = logging.getLogger(__name__)

class PurchaseOrderEmbalaje(models.Model):
    _name = 'purchase.order.embalaje'
    name = fields.Char("Forma Embalaje")


class StageImportsDate(models.Model):
    _name = 'stage.imports.date'
    order_id = fields.Many2one("purchase.order", u"Importación")
    name = fields.Many2one("imports.stage", string="Situación")
    date = fields.Date(string=u"Fecha Estado")

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # _authmode = True
    @api.one
    @api.depends('order_line', 'order_line.total_weight')
    def _compute_total_weight(self):
        self.total_weight = sum([x.total_weight for x in self.order_line])

    @api.one
    @api.depends('order_line', 'order_line.total_volume')
    def _compute_total_volume(self):
        self.total_volume = sum([x.total_volume for x in self.order_line])

    # Obtener si se tiene un conteo de importaciones
    @api.model
    def _compute_imports(self):
        for order in self:
            imports_count = self.env['poi.purchase.imports'].search([('order_id', '=', order.id)])
            order.imports_count = len(imports_count)

    # imports = fields.Many2one("poi.purchase.imports", "Carpeta de Importaciones", copy=False)
    # imports_count = fields.Integer(compute="_compute_imports", string='Carpeta de Importaciones', copy=False, default=0)

    total_weight = fields.Float(
        compute=_compute_total_weight, string='Peso Total (Kg.)',
        readonly=True,
        digits_compute=dp.get_precision('Stock Weight'))
    total_volume = fields.Float(
        compute=_compute_total_volume, string='Volumen Total (m3)', readonly=True)
    tipo_fac = fields.Selection(
        [('1', 'Compra'), ('2', 'Boleto BCP'), ('3', 'Importación'), ('4', 'Recibo de Alquiler'),
         ('5', 'Nota de débito proveedor'), ('6', 'Nota de crédito cliente'), ('7', 'Venta'),
         ('8', 'Nota de débito cliente'), ('9', 'Nota de crédito proveedor'), ('10', 'Sin Asignar'),
         ('11', 'Rectificación')], string='Tipo de Factura', default='1',
        help=u"Tipificación de facturas para fines técnicos.")
    pais_lugar = fields.Char("Pais/lugar")
    embalaje = fields.Many2one("purchase.order.embalaje", string=u"Forma de embalaje")
    stage_id = fields.Many2one('imports.stage', string=u"Situación", track_visibility='onchange', group_expand='_read_group_stage_ids',)

    stage_date = fields.One2many('stage.imports.date', 'order_id', string=u"Estados Importación", copy=False)
    state_color = fields.Selection(related='stage_id.state_color',
                                   selection=STATE_COLOR_SELECTION, string="Color", readonly=True)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):

        # perform search
        stage_ids = self.env['imports.stage'].search([('state_color', '!=', '')])
        stg_id = []
        for st in stage_ids:
            stg_id.append(st.id)
        return stages.browse(stg_id)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New' and vals.get('tipo_fac') != '3':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.imports') or '/'
        return super(PurchaseOrder, self).create(vals)

    @api.onchange('partner_id')
    def onchange_partner_id_import(self):
        if self.partner_id:
            pais = self.partner_id.country_id.name and self.partner_id.country_id.name or ""
            lugar1 = self.partner_id.street and self.partner_id.street or ""
            lugar2 = self.partner_id.street2 and self.partner_id.street2 or ""
            self.pais_lugar = pais + '/' + lugar1 + ' ' + lugar2

    @api.multi
    def action_view_imports(self):

        action = self.env.ref('poi_purchase_imports.action_poi_purchase_imports')
        result = action.read()[0]
        imports_count = self.env['poi.purchase.imports'].search([('order_id', '=', self.id)])
        imports_ids = []
        for imports in imports_count:
            imports_ids.append(imports.id)

        if self.imports_count > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, imports_ids)) + "])]"
        else:
            res = self.env.ref('poi_purchase_imports.poi_purchase_imports_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = imports_ids[0]
        return result

    @api.multi
    def action_open_landed_cost(self):
        self.ensure_one()
        line_obj = self.env['purchase.cost.distribution.line']
        lines = line_obj.search([('purchase_id', '=', self.id)])
        if lines:
            mod_obj = self.env['ir.model.data']
            model, action_id = tuple(
                mod_obj.get_object_reference(
                    'purchase_landed_cost',
                    'action_purchase_cost_distribution'))
            action = self.env[model].browse(action_id).read()[0]
            ids = set([x.distribution.id for x in lines])
            if len(ids) == 1:
                res = mod_obj.get_object_reference(
                    'purchase_landed_cost', 'purchase_cost_distribution_form')
                action['views'] = [(res and res[1] or False, 'form')]
                action['res_id'] = list(ids)[0]
            else:
                action['domain'] = "[('id', 'in', %s)]" % list(ids)
            return action


    @api.multi
    def _button_confirm_threading(self):
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            self._purchase_confirm(
                use_new_cursor=new_cr.dbname,
                company_id=self.env.user.company_id.id)
            new_cr.close()
            return {}

    @api.model
    def _purchase_confirm(self, use_new_cursor=False, company_id=False):
        if use_new_cursor:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        try:
            self.button_confirm()
            if use_new_cursor:
                cr.commit()
                user_id = self._uid
                usuario = self.env['res.users'].browse(user_id)
                body_html_send = "Orde de Compra " + str(self.name) + " Confirmado"
                new_msg = self.message_post(body=body_html_send)
                new_msg.sudo().write({'needaction_partner_ids': [(4, usuario.partner_id.id)]})
        except OperationalError:
            if use_new_cursor:
                cr.rollback()
            else:
                raise

        if use_new_cursor:
            cr.commit()
            cr.close()

        return {}

    @api.multi
    def purchase_threading(self):
        threaded_calculation = threading.Thread(target=self._button_confirm_threading, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_view_invoice(self):

        result = super(PurchaseOrder, self).action_view_invoice()
        # Actualizar para que use el tipo_fac de la compra en el pedido
        if hasattr(self, 'tipo_fac'):
            context = result['context']
            context.update({'type': 'in_invoice', 'default_purchase_id': self.id,
                            'default_tipo_fac': self.tipo_fac})
        return result

    @api.multi
    def action_your_imports(self):
        action = self.env['ir.model.data'].xmlid_to_object('poi_purchase_imports.poi_purchase_imports_tree_view').read()[0]
        tree_view_id = self.env.ref('purchase.purchase_order_tree').id
        form_view_id = self.env.ref('poi_purchase_imports.purchase_order_imports').id
        kanb_view_id = self.env.ref('poi_purchase_imports.imports_kanban_view').id
        action_context = safe_eval(action['context'], {'uid': self.env.uid})
        action['views'] = [
            [kanb_view_id, 'kanban'],
            [tree_view_id, 'tree'],
            [form_view_id, 'form'],
            [False, 'graph'],
            [False, 'calendar'],
            [False, 'pivot']
        ]
        action['context'] = action_context
        return action

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        for imports in self and self._origin:
            # Borrar los picking asignados
            stage = self.env['stage.imports.date']
            stage_vals = stage.search([('order_id', '=', self._origin.id), ('name', '=', imports.stage_id.id)])
            if not stage_vals:
                stage.create({'order_id': self._origin.id,
                              'name': imports.stage_id.id,
                              'date': fields.Date.context_today(self)})
            else:
                raise exceptions.Warning(
                    _(u"No puede volver a una situación anterior"))

    # @api.multi
    # def _create_picking(self):
    #     StockPicking = self.env['stock.picking']
    #     for order in self:
    #         if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
    #             pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
    #             if not pickings:
    #                 res = order._prepare_picking()
    #                 picking = StockPicking.create(res)
    #             else:
    #                 picking = pickings[0]
    #             for l in order.order_line:
    #             #moves = order.order_line._create_stock_moves(picking)
    #                 move = l._create_stock_moves(picking)
    #                 move._action_confirm()
    #                 move._action_assign()
    #             #moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
    #             # seq = 0
    #             # for move in sorted(moves, key=lambda move: move.date_expected):
    #             #     seq += 5
    #             #     move.sequence = seq
    #             #moves._action_assign()
    #             #picking.message_post_with_view('mail.message_origin_link',
    #             #                               values={'self': picking, 'origin': order},
    #             #                               subtype_id=self.env.ref('mail.mt_note').id)
    #     return True

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_weight(self):
        self.total_weight = self.product_id.weight * self.product_qty

    @api.one
    @api.depends('product_id', 'product_qty')
    def _compute_total_volume(self):
        self.total_volume = self.product_id.volume * self.product_qty

    total_weight = fields.Float(
        compute=_compute_total_weight, string="Peso", store=True,
        digits_compute=dp.get_precision('Stock Weight'),
        help="Total Peso Kg.")

    total_volume = fields.Float(
        compute=_compute_total_volume, string='Volumen', store=True,
        help="Total Volumen m3.")

    partida = fields.Many2one("partida.arancelaria", "Partida Arancelaria")

    # @api.multi
    # def _create_stock_moves(self, picking):
    #     moves = self.env['stock.move']
    #     done = self.env['stock.move'].browse()
    #     for line in self:
    #         for val in line._prepare_stock_moves(picking):
    #             done = moves.create(val)
    #     return done

    # @api.onchange('product_id')
    # def onchange_product_id_toy(self):
    #     self.partida = self.product_id.partida


# class ProcurementOrder(models.Model):
#     _inherit = 'procurement.order'
#
#     @api.multi
#     def _prepare_purchase_order(self, partner):
#         result = super(ProcurementOrder, self)._prepare_purchase_order(partner)
#         if partner.country_id and self.company_id.country_id:
#             if partner.country_id.id != self.company_id.country_id.id:
#                 result['tipo_fac'] = '3'
#         return result