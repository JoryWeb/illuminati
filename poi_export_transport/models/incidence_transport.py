
from odoo import api, fields, models, _
class IncidenceTransportType(models.Model):
    _name = 'incidence.transport.type'
    name = fields.Char(string=u"Tipo")

class IncidenceTransport(models.Model):
    _name = 'incidence.transport'
    picking_id = fields.Many2one("stock.picking", string=u"Referencia Movimiento")
    date = fields.Date(string=u"Fecha")
    type = fields.Many2one("incidence.transport.type", string=u"Tipo incidencia")
    location_id = fields.Many2one("stock.location", string=u"Ubicación Origen")
    location_dest_id = fields.Many2one("stock.location", string=u"Ubicación Destino")
    fleet_id = fields.Many2one("fleet.vehicle", string=u"Referencia Camión")
    chofer_id = fields.Many2one("res.partner", u'Chofer')
    transportista_id = fields.Many2one("res.partner", u'Proveedor')
    total_qty = fields.Float(string=u"Cantidad Transportada")
