import logging
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

class AccountExpensesRendition(models.Model):
    _inherit  = 'account.expenses.rendition'

    hr = fields.Boolean('Recursos Humanos')
