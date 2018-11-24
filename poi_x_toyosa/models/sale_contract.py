import logging
from odoo import fields, models, api, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)

class SaleContract(models.Model):
    _name = 'sale.contract'
    _description = 'Contratos de ventas'

    name = fields.Char('Descripcion')
    report_id = fields.Many2one('ir.actions.report', 'Reporte')
    clause = fields.Html(string=u"Claúsulas del Contrato")
