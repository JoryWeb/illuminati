import logging
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    saldo_rciva = fields.Float(string="Saldo Rc-IVA", default=0)
