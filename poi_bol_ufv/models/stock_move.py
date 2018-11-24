# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'
    ufv_cost_value = fields.Float('Costo adicionales UFV')