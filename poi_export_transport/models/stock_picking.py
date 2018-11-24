
from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    date_carguio = fields.Date(u'Fecha Carguío')
    date_salida = fields.Date(u'Fecha Salida')
    fleet_id = fields.Many2one("fleet.vehicle", u'Placa')
    chofer_id = fields.Many2one("res.partner", u'Chofer')
    transportista_id = fields.Many2one("res.partner", u'Transportista')

    @api.onchange('fleet_id')
    def _onchange_fleet_id(self):
        if self.fleet_id:
            self.chofer_id = self.fleet_id.driver_id.id
            self.transportista_id = self.fleet_id.owner_id.id

    @api.multi
    def return_action_to_open(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('poi_transport_export', xml_id)
            res.update(
                context=dict(self.env.context,
                             default_picking_id=self.id,
                             default_location_id=self.location_id.id,
                             default_location_dest_id=self.location_dest_id.id,
                             default_total_qty=self.weight_exp,
                             default_chofer_id=self.chofer_id.id,
                             default_transportista_id=self.transportista_id.id,
                             default_fleet_id=self.fleet_id.id,
                             group_by=False),
                domain=[('picking_id', '=', self.id)]
            )
            return res
        return False