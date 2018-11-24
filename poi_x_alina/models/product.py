##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _
import time
import pytz
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class AlmacenamientoData(models.Model):
    _name = 'almacenamiento.data'
    product_id = fields.Many2one("product.template", "Producto")
    name = fields.Char(string="Nombre")
    estante = fields.Char(string=u"Estante")
    fila = fields.Char(string=u"Fila")
    caja = fields.Char(string=u"Caja")
    location_id = fields.Many2one("stock.location", string=u"Ubicación", domain=[('usage', '=', 'internal')])


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    almacenamiento_line = fields.One2many('almacenamiento.data', 'product_id', string="Almacenamiento", copy=True,
                                          help="Utilizar esta información para averiguar en que Estante, fila y caja debe ir el producto ")

    # @api.multi
    # def write(self, vals):
    #     cadena = "%s,%s" % ('product.template', self.id)
    #     fecha = datetime.utcnow() - timedelta(seconds=10)
    #     values = {
    #         cadena: fecha.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    #         }
    #     self = self.with_context(__last_update=values)
    #     return super(ProductTemplate, self).write(vals)
