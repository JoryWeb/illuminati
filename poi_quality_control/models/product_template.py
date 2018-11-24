##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    qc_triggers = fields.One2many(
        comodel_name="qc.trigger.product_template_line",
        inverse_name="product_template",
        string="Quality control triggers")

    senasag = fields.Char(string="Registro Sanitario", help="Registro sanitario asignado por SENASAG")
    description_conservation = fields.Text(string="Instrucciones para su conservación", help="Definir las instrucciones de conservación para el producto")