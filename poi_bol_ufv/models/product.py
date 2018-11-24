# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.float_utils import float_round
from odoo.models import expression
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    ufv_value = fields.Boolean("Aplicar Valoración UFV")
    property_stock_account_output_ufv = fields.Many2one(
        'account.account', 'Cuenta UFV Inventarios',
        company_dependent=True, domain=[('deprecated', '=', False)],
        help="Contra cuenta de valoración de inventarios por lo general AITB")