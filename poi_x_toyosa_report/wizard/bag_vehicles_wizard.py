from odoo import models, fields, api
from datetime import date, datetime


class BagVehiclesWizard(models.TransientModel):
    _name = "bag.vehicles.wizard"

    pricelist_id = fields.Many2one('product.pricelist', "Lista de Precios", required=True)

    @api.multi
    def action_view_report(self):
        domain = []
        # if self.date:
        #     domain.append(['date_invoice', '<=', self.date])

        return {
            'name': "Bolsa de Vehiculos",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'bag.vehicles.report',
            'type': 'ir.actions.act_window',
            'context': {
                'pricelist_id': self.pricelist_id and self.pricelist_id.id,
            },
            'domain': domain,
        }
