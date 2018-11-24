import logging
from odoo import api, fields, models
from odoo.exceptions import Warning, ValidationError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_wallet = fields.Boolean(string="Cartera", default=False)
