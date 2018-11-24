
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ruex = fields.Char('RUEX')
    code_export = fields.Char('Codigo de Exportacion')
