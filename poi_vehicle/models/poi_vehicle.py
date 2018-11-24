
from odoo import api, fields, models
from odoo import tools

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


class vehicle_state(models.Model):
    """
    Model for asset states.
    """
    _name = 'vehicle.state'
    _description = 'State of Vehicle'
    _order = "sequence"

    STATE_SCOPE_TEAM = [
        ('0', 'Finance'),
        ('1', 'Warehouse'),
        ('2', 'Manufacture'),
        ('3', 'Maintenance'),
        ('4', 'Accounting')
    ]

    name = fields.Char('State', size=64, required=True, translate=True)
    sequence = fields.Integer('Sequence', help="Used to order states.", default=1)
    state_color = fields.Selection(STATE_COLOR_SELECTION, 'State Color')
    team = fields.Selection(STATE_SCOPE_TEAM, 'Scope Team')

    def change_color(self):
        color = int(self.state_color) + 1
        if (color > 9): color = 0
        return self.write({'state_color': str(color)})


class vehicle_category(models.Model):
    _description = 'Vehicle Tags'
    _name = 'vehicle.category'

    name = fields.Char('Tag', required=True, translate=True)
    vehicle_ids = fields.Many2many('poi.vehicle', id1='category_id', id2='vehicle_id', string='Vehicle')


class poi_vehicle(models.Model):
    """
    Vehicle
    """
    _name = 'poi.vehicle'
    _description = 'Vehicle'
    _inherit = ['mail.thread']

    # def _read_group_state_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None,
    #                           team='3'):
    #     access_rights_uid = access_rights_uid or uid
    #     stage_obj = self.pool.get('vehicle.state')
    #     order = stage_obj._order
    #     # lame hack to allow reverting search, should just work in the trivial case
    #     if read_group_order == 'stage_id desc':
    #         order = "%s desc" % order
    #     # write the domain
    #     # - ('id', 'in', 'ids'): add columns that should be present
    #     # - OR ('team','=',team): add default columns that belongs team
    #     search_domain = []
    #     search_domain += ['|', ('team', '=', team)]
    #     search_domain += [('id', 'in', ids)]
    #     stage_ids = stage_obj._search(cr, uid, search_domain, order=order, access_rights_uid=access_rights_uid,
    #                                   context=context)
    #     result = stage_obj.name_get(cr, access_rights_uid, stage_ids, context=context)
    #     # restore order of the search
    #     result.sort(lambda x, y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))
    #     return result, {}

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):

        # perform search
        stage_ids = self.env['vehicle.state'].search([('state_color', '!=', '')])
        stg_id = []
        for st in stage_ids:
            stg_id.append(st.id)
        return stages.browse(stg_id)

    # def _read_group_finance_state_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None,
    #                                   context=None):
    #     return self._read_group_state_ids(cr, uid, ids, domain, read_group_order, access_rights_uid, context, '0')
    #
    # def _read_group_warehouse_state_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None,
    #                                     context=None):
    #     return self._read_group_state_ids(cr, uid, ids, domain, read_group_order, access_rights_uid, context, '1')
    #
    # def _read_group_manufacture_state_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None,
    #                                       context=None):
    #     return self._read_group_state_ids(cr, uid, ids, domain, read_group_order, access_rights_uid, context, '2')
    #
    # def _read_group_maintenance_state_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None,
    #                                       context=None):
    #     return self._read_group_state_ids(cr, uid, ids, domain, read_group_order, access_rights_uid, context, '3')

    CRITICALITY_SELECTION = [
        ('0', 'General'),
        ('1', 'Important'),
        ('2', 'Very important'),
        ('3', 'Critical')
    ]


    finance_state_id = fields.Many2one('vehicle.state', 'State', domain=[('team', '=', '0')])
    warehouse_state_id = fields.Many2one('vehicle.state', 'State', domain=[('team', '=', '1')])
    manufacture_state_id = fields.Many2one('vehicle.state', 'State', domain=[('team', '=', '2')])
    maintenance_state_id = fields.Many2one('vehicle.state', 'State', domain=[('team', '=', '3')], track_visibility='onchange', group_expand='_read_group_stage_ids')
    maintenance_state_color = fields.Selection(related='maintenance_state_id.state_color',
                                               selection=STATE_COLOR_SELECTION, string="Color", readonly=True)

    criticality = fields.Selection(CRITICALITY_SELECTION, 'Criticality')

    property_stock_vehicle = fields.Many2one(
        'stock.location', "Vehicle Location",
        company_dependent=True, domain=[('usage', 'like', 'asset')],
        help="This location will be used as the destination location for installed parts during asset life.")


    vehicle_number = fields.Char('Vehicle Number', size=64)
    model = fields.Char('Model', size=64)
    serial = fields.Char('Serial no.', size=64)
    manufacturer_id = fields.Many2one('res.partner', 'Manufacturer')
    start_date = fields.Date('Start Date')
    purchase_date = fields.Date('Purchase Date')
    warranty_start_date = fields.Date('Warranty Start')
    warranty_end_date = fields.Date('Warranty End')

    user_id = fields.Many2one('res.users', 'Assigned to', track_visibility='onchange')
    active = fields.Boolean('Active', default=True)
    image = fields.Binary("Image", attachment=True)
    image_small = fields.Binary("Small-sized image", attachment=True)
    image_medium = fields.Binary("Medium-sized image", attachment=True)
    name = fields.Char('Vehicle Placa', size=64, required=True, translate=True)
    category_ids = fields.Many2many('product.category', id1='vehicle_id', id2='category_id', string='Tags')
    texto = fields.Char(string=u"Texto")
    vendor_id = fields.Many2one('res.partner', string=u'Dueño Actual')
    chasis_id = fields.Many2one("stock.production.lot", string=u"Chasis")
    n_chasis = fields.Char("N° de Chasis")
    modelo = fields.Many2one("modelo.toyosa", "Modelo")
    anio_modelo = fields.Many2one("anio.toyosa", string=u"Año Modelo")
    anio_fabricacion = fields.Many2one("anio.toyosa", string=u"Año Fabricación")
    edicion = fields.Char("ED")
    colorinterno = fields.Many2one("color.interno", string="Color Interno")
    colorexterno = fields.Many2one("color.externo", string="Color Externo")
    marca = fields.Many2one("marca.toyosa", string=u"Marca")
    n_motor = fields.Char(u"N° Motor")
    n_llaves = fields.Char(u"N° Llave")
    cant_llaves = fields.Integer(u"Cant. Llaves")

    # _group_by_full = {
    #     'finance_state_id': _read_group_finance_state_ids,
    #     'warehouse_state_id': _read_group_warehouse_state_ids,
    #     'manufacture_state_id': _read_group_manufacture_state_ids,
    #     'maintenance_state_id': _read_group_maintenance_state_ids,
    # }

    _sql_constraints = [
        ('name_ref_uniq', 'unique (name)', 'Numero de Placa o Serie repetido'),
        ('n_chasis_ref_uniq', 'unique (n_chasis)', 'Numero de serie o chasis repetido'),
    ]

    @api.onchange('chasis_id')
    def onchange_chasis_id(self):
        if self.chasis_id:
            self.modelo = self.chasis_id.modelo.id
            self.anio_modelo = self.chasis_id.anio_modelo.id
            self.anio_fabricacion = self.chasis_id.anio_fabricacion.id
            self.edicion = self.chasis_id.edicion
            self.colorinterno = self.chasis_id.colorinterno.id
            self.colorexterno = self.chasis_id.colorexterno.id
            self.marca = self.chasis_id.marca.id
            self.n_motor = self.chasis_id.n_motor
            self.n_llaves = self.chasis_id.n_llaves
            self.cant_llaves = self.chasis_id.cant_llaves

    @api.onchange('chasis_id')
    def onchange_chasis_id(self):
        if self.chasis_id:
            self.modelo = self.chasis_id.modelo.id
            self.anio_modelo = self.chasis_id.anio_modelo.id
            self.anio_fabricacion = self.chasis_id.anio_fabricacion.id
            self.edicion = self.chasis_id.edicion
            self.colorinterno = self.chasis_id.colorinterno.id
            self.colorexterno = self.chasis_id.colorexterno.id
            self.marca = self.chasis_id.marca.id
            self.n_motor = self.chasis_id.n_motor
            self.n_llaves = self.chasis_id.n_llaves
            self.cant_llaves = self.chasis_id.cant_llaves

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name_exist = self.search([('name', '=', self.name)])
            if name_exist:
                self.name = ''
            else:
                self.name = self.name

    @api.onchange('n_chasis')
    def onchange_n_chasis(self):
        if self.name:
            name_exist = self.search([('n_chasis', '=', self.n_chasis)])
            if name_exist:
                self.n_chasis = ''
            else:
                self.n_chasis = self.n_chasis
    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        res = super(poi_vehicle, self).create(vals)
        vals_history = {
            'asset_id': res.id,
            'partner_id': res.vendor_id.id,
            'date_history': fields.Date.context_today(self),
        }
        self.env['poi.vehicle.history'].create(vals_history)
        return res

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        res = super(poi_vehicle, self).write(vals)
        if 'vendor_id' in vals:
            vals_history = {
                'asset_id': self.id,
                'partner_id': vals['vendor_id'],
                'date_history': fields.Date.context_today(self),
            }
            self.env['poi.vehicle.history'].create(vals_history)
        return res

class poi_vehicle_history(models.Model):
    _description = 'History Partners'
    _name = 'poi.vehicle.history'

    asset_id = fields.Many2one('poi.vehicle', string=u'Vehículo')
    partner_id = fields.Many2one('res.partner', string=u'Dueños')
    date_history = fields.Date(string=u'Fecha Registro Dueño')

