import logging
from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    """Adds last name and first name; name becomes a stored function field."""
    _inherit = 'crm.lead'

    traffic_id = fields.Many2one('crm.traffic', 'Trafico de Clientes')
