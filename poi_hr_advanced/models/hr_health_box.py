import logging
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class HrHealthBox(models.Model):
    _name = "hr.health.box"
    _description = "Cajas de Salud"

    name = fields.Char('Cajas de Salud')
