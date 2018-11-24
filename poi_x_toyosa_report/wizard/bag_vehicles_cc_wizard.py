from odoo import models, fields, api
from datetime import date, datetime


class BagVehiclesCcWizard(models.TransientModel):
    _name = "bag.vehicles.cc.wizard"

    date_cut = fields.Date("Hasta", default=fields.Date.today(), required=True)
    currency_id = fields.Many2one('res.currency', 'Moneda', default=lambda self: self.env.user.company_id.currency_id_sec)

    @api.multi
    def action_view_report(self):
        domain = []
        # if self.date:
        #     domain.append(['date_invoice', '<=', self.date])

        return {
            'name': "Bolsa de Vehiculos C/C",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'bag.vehicles.cc.report',
            'type': 'ir.actions.act_window',
            'context': {
                'date_cut': self.date_cut,
                'currency_id': self.currency_id.id
            },
            'domain': domain,
        }
