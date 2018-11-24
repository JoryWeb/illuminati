from odoo import models, fields, api
from datetime import date, datetime


class WalletWizard(models.TransientModel):
    _name = "wallet.wizard"

    date = fields.Date('Hasta', default=fields.Date.today(), help="Seleciona todas las Facturas hasta la fecha indicada.", required=True)
    # date_cut = fields.Date('Fecha de Corte', default=fields.Date.today(), help="La Fecha de Corte simula la fecha historica de esas Facturas.")
    warehouse_id = fields.Many2one('stock.warehouse', 'Sucursal/Almacen')
    agency_id = fields.Many2one('res.agency', 'Regional/Agencia')
    partner_id = fields.Many2one('res.partner', 'Cliente')


    @api.multi
    def action_view_report(self):
        wallet_obj = self.env['wallet.report']
        domain = []
        if self.date:
            domain.append(['date_invoice', '<=', self.date])
        if self.warehouse_id and self.warehouse_id.id:
            domain.append(['warehouse_id', '=', self.warehouse_id.id])
        if self.agency_id and self.agency_id.id:
            domain.append(['agency_id', '=', self.agency_id.id])
        if self.partner_id and self.partner_id.id:
            domain.append(['partner_id', '=', self.partner_id.id])

        return {
            'name': "Reporte de Cartera",
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'wallet.report',
            'type': 'ir.actions.act_window',
            'context': {
                'date': self.date,
                'date_cut': self.date,
            },
            'domain': domain,
        }
