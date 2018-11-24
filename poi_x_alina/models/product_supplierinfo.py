##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _

class ProductSupplierinfoDispo(models.Model):
    _name = "product.supplierinfo.dispo"
    name = fields.Char("Disponibiliada")

class ProductSupplierinfoCumpli(models.Model):
    _name = "product.supplierinfo.cumpli"
    name = fields.Char("Cumplimiento")

class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    calidad = fields.Selection([
        ('optima', 'Optima'),
        ('regular', 'Regular'),
        ('mala', 'Mala'),
    ], required=False, default='optima',
        help="Definir una calidad del proveedor para el producto y precio que provee")
    disponibilidad = fields.Many2one("product.supplierinfo.dispo", string=u"Disponibilidad")
    cumplimiento = fields.Many2one("product.supplierinfo.cumpli", string=u"Cumplimiento")
