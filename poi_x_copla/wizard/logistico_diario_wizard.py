# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time

from odoo import models, fields, api, _, tools
from datetime import datetime

class LogisticoDiarioWizard(models.TransientModel):
    """
    For Reporte kardex valorado
    """
    _name = "logistico.diario.wizard"
    _description = "Reporte Logistico Diario Wizard"

    @api.multi
    def open_table(self):
        data = self.read()[0]