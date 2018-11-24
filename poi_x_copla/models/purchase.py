
from odoo import api, fields, models, osv, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    fleet_id = fields.Many2one("fleet.vehicle", u'Placa')
    chofer_id = fields.Many2one("res.partner", u'Conductor')
    transportista_id = fields.Many2one("res.partner", u'Propietario')
    payment_partner_id = fields.Many2one("res.partner", u'Pagar a')

    @api.onchange('fleet_id')
    def _onchange_fleet_id(self):
        if self.fleet_id:
            self.chofer_id = self.fleet_id.driver_id.id
            self.transportista_id = self.fleet_id.owner_id.id