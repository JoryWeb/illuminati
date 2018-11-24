# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    country_id = fields.Many2one('res.country', string='Pais', related='partner_id.country_id', readonly=True)
    price_gross = fields.Float('Precio o Valor Bruto', default=0.00)
    seguro_local = fields.Float('Seguro hasta frontera', default=0.00)
    seguro_inter = fields.Float('Seguro internacional', default=0.00)
    transporte_local = fields.Float('Transporte hasta frontera', default=0.00)
    transporte_inter = fields.Float('Transporte internacional', default=0.00)
    flete_origen = fields.Float('Flete Origen', default=0.00)
    flete_destino = fields.Float('Flete Destino', default=0.00)
    otros = fields.Float('Otros', default=0.00)
    total_cif = fields.Float('Total Cif', default=0.00)

    origin_inc = fields.Char('Origen/Salida')
