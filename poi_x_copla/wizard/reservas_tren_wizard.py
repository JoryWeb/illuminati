# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time

from odoo import models, fields, api, _, tools
from datetime import datetime


class ReservaTrenWizard(models.TransientModel):
    """
    For Reporte kardex valorado
    """
    _name = "reserva.tren.wizard"
    _description = "Reporte reserva de tren Wizard"

    picking_id = fields.Many2one('stock.picking', string=u'Albarán', required=True)

    @api.multi
    def open_table(self):
        data = self.read()[0]

        if data['picking_id']:
            picking_id = str(data['picking_id'][0])
        self.env['reservas.tren'].init(picking_id=picking_id)
        context_report = {}
        domain_report = []

        model_data_id = self.env['ir.model.data']._get_id('poi_x_copla', 'reservas_tren_tree')
        res_id = self.env['ir.model.data'].browse(model_data_id).res_id
        return {
            'name': _('Reporte tren'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'reservas.tren',
            'view_id': res_id,
            'context': context_report,
            'type': 'ir.actions.act_window'
        }


class SolicitudDevolucionImpositivaWizard(models.TransientModel):
    """
    For Reporte kardex valorado
    """
    _name = "solicitud.devolucion.impositiva.wizard"
    _description = "Reporte solicitud devolucion impositiva Wizard"


