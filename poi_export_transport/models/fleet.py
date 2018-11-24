##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import models, api, fields

class FleetVehicleTipe(models.Model):
    _name = 'fleet.vehicle.type'
    name = fields.Char(string="Nombre Tipo")

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    fleet_type = fields.Selection(string='Tipo Transporte',
                                    selection=[('externo', 'Externo'), ('interno', 'Interno')])
    owner_id = fields.Many2one("res.partner", string=u"Propietario")
    type_id = fields.Many2one("fleet.vehicle.type", string=u"Tipo")
    chasis = fields.Char(string=u"Chasis")
    cod_barras = fields.Char(string=u"Código de Barras")
    capacity = fields.Float(string=u"Capacidad")
    date_inspection = fields.Date(string=u"Fecha última inspección")
    tramo = fields.Selection([
        ('nacional', 'Nacional'),
        ('internacional', 'Internacional'),
        ('ambos', 'Ambos')
    ], string=u'Tramo', default='nacional', help='Seleccione el tipo de tramo')

    route_id = fields.Many2one('stock.location.route', string='Ruta', domain=[('sale_selectable', '=', True)],
                               ondelete='restrict')
    poliza = fields.Char(string=u"Póliza de seguros")
    datos_poliza = fields.Char(string=u"Datos de póliza de seguros")
    exp_poliza = fields.Date(string=u"Expiración del seguro")
    proveedor_poliza = fields.Many2one("res.partner", string=u"Proveedor de seguro")
    days_exp = fields.Integer(string=u"Dias para expirar")
    note = fields.Text(string=u"Nota interna")
    motor = fields.Char(string=u"Motor")