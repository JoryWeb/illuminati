import logging
from odoo import fields, models, api, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)

class Plate(models.Model):
    _name = 'plate.plate'
    _description = 'Tramite de Placas'

    name = fields.Char('Descripcion', default=lambda self: _('Nuevo'), readonly=True)
    from_contact = fields.Many2one('res.users', 'De:', readonly=True, states={'draft':[('readonly',False)]}, default=lambda self: (self.env.user and self.env.user.id) or self.env.user)
    seller_id = fields.Many2one('res.users', 'Vendedor', readonly=True, related="order_id.user_id")
    to = fields.Many2one('res.users', 'A:', readonly=True, states={'draft':[('readonly',False)]})
    amount = fields.Float('Importe', readonly=True, states={'draft':[('readonly',False)]})
    partner_id = fields.Many2one('res.partner', 'Cliente', related="order_id.partner_id", readonly=True)
    partner_id_c = fields.Many2one('res.partner', 'Cliente', compute="_compute_partner_id")
    lot_id = fields.Many2one('stock.production.lot', 'Chasis', compute="_compute_chasis", store=True, readonly=True)
    # year = fields.Many2one('anio.toyosa', u'Año', related="lot_id.anio_modelo", readonly=True)
    product_id = fields.Many2one('product.product', 'Producto', related="lot_id.product_id", readonly=True)
    order_id = fields.Many2one('sale.order', 'Cotizacion', required=True,  copy=False, readonly=True, states={'draft':[('readonly',False)]})
    warehouse_id = fields.Many2one('stock.warehouse', 'Almancen', related="order_id.warehouse_id", readonly=True)
    deadline = fields.Date('Fecha de Entrega', readonly=True, states={'draft':[('readonly',False)]})
    work_todo = fields.Char('Trabajo a Realizar', readonly=True, states={'draft':[('readonly',False)]})
    diprove = fields.Char('Certificado Diprove', readonly=True, states={'draft':[('readonly',False)]})
    customer_flag = fields.Boolean('Cargo Cliente', readonly=True, states={'draft':[('readonly',False)]})
    toyosa_flag = fields.Boolean('Cargo Toyosa', readonly=True, states={'draft':[('readonly',False)]})
    detail_id = fields.One2many('plate.detail', 'plate_id', 'Detalles', readonly=True, states={'draft':[('readonly',False)], 'send':[('readonly',False)] },)
    stage_id = fields.One2many('plate.stage', 'plate_id', 'Etapas', readonly=True, states={'draft':[('readonly',False)], 'send':[('readonly',False)] })
    state = fields.Selection(
        string="Estado",
        selection=[
                ('draft', 'Borrador'),
                ('send', 'Confirmado'),
                ('done', 'Hecho'),
        ], default='draft'
    )
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen', compute="_compute_warehouse_id")

    @api.multi
    @api.depends("order_id")
    def _compute_warehouse_id(self):
        for s in self:
            if s.order_id and s.order_id.partner_id:
                s.warehouse_id = s.order_id.warehouse_id.id

    @api.multi
    @api.depends("order_id")
    def _compute_partner_id(self):
        for s in self:
            if s.order_id and s.order_id.partner_id:
                s.partner_id_c = s.order_id.partner_id.id

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('plate.plate') or 'Nuevo'
        plate_id = super(Plate, self).create(vals)
        plate_id.order_id.plate_id = plate_id.id
        return plate_id

    @api.multi
    @api.depends("order_id")
    def _compute_chasis(self):
        for plate in self:
            if plate.order_id:
                for line in plate.order_id.order_line:
                    if line.lot_id:
                        plate.lot_id = line.lot_id.id
                        break

    @api.onchange("order_id")
    def _onchange_order_id(self):
        if self.order_id:
            stage_obj = self.env['plate.stage.stage']
            stage_ids = stage_obj.search([('load_on_create', '=', True)])
            stages = []
            for s in stage_ids:
                stages.append([0,0,{'stage': s.id}])
            self.stage_id = stages

    @api.multi
    def plate_done(self):
        self.state = 'done'

    @api.multi
    def plate_send(self):
        self.state = 'send'




class PlateDetail(models.Model):
    _name = 'plate.detail'
    _description = 'Detalle del tramite de placas'
    _rec_name = 'file_delivered'

    plate_id = fields.Many2one('plate.plate', 'Tramite de Placas')
    file_delivered = fields.Char('Documentos Entregados')
    note = fields.Char('Observaciones')

class PlateStage(models.Model):
    _name = 'plate.stage'
    _rec_name = 'stage' # optional
    _description = 'Etapas del tramite de placas'

    to = fields.Many2one('res.users', 'A:', related="plate_id.to")
    partner_id = fields.Many2one('res.partner', 'Cliente', related="plate_id.partner_id")
    plate_id = fields.Many2one('plate.plate', 'Tramite de Placas')
    date_start = fields.Date('Fecha de Inicio')
    date_end = fields.Date(u'Fecha de Finalización')
    stage = fields.Many2one('plate.stage.stage','Etapa')
    sequence = fields.Integer('Secuencia', related="stage.sequence")
    lot_id = fields.Many2one('stock.production.lot', 'Chasis', related="plate_id.lot_id")
    partner_id_c = fields.Many2one('res.partner', 'Cliente', compute="_compute_partner_id", store=True)

    @api.multi
    @api.depends("plate_id")
    def _compute_partner_id(self):
        for s in self:
            if s.plate_id and s.plate_id.order_id and s.plate_id.order_id.partner_id:
                s.partner_id_c = s.plate_id.order_id.partner_id.id


    @api.multi
    def action_view_plate(self):
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('poi_x_toyosa.plate_action2_form')
        form_view_id = imd.xmlid_to_res_id('poi_x_toyosa.plate_view_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if self.plate_id:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = self.plate_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

class PlateStageStage(models.Model):
    _name = 'plate.stage.stage'
    _description = 'Etapas del Tramite de Placas'
    _order = "load_on_create, sequence"

    name = fields.Char('Etapa')
    sequence = fields.Integer('Secuencia', default=0)
    load_on_create = fields.Boolean('Auto', default=False, help="Cuando se encuentra Marcado esta etapa sera automaticamente creada en el tramite de placas.")
