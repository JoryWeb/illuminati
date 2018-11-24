import logging
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class HrAfps(models.Model):
    _name = "hr.afps"
    _description = "Aseguradoras"

    name = fields.Char('Nombre')
    bank_account_id = fields.Many2one('res.partner.bank', 'Entidad Beneficiaria del Pago')
    note = fields.Char('Detalle', default="Aportes AFP")
