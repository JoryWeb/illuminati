import logging
from openerp import fields, models, api, _
from openerp.exceptions import Warning, ValidationError
from lxml import etree
import math

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Categorias Avanzadas para Productos'

    name1 = fields.Many2one('product.category.items','Division')
    name2 = fields.Many2one('product.category.items','Fabrica')
    name3 = fields.Many2one('product.category.items','Mundo')
    name4 = fields.Many2one('product.category.items','Tipo')
    name5 = fields.Many2one('product.category.items','Sub-Tipo')
    name6 = fields.Many2one('product.category.items','Linea')
    name7 = fields.Many2one('product.category.items','Modelo')
    name8 = fields.Many2one('product.category.items','Descripcion')


class ProductCategoryItems(models.Model):
    _name = 'product.category.items'
    _description = 'Items de las Categorias Avanzadas para Productos'

    name = fields.Char('Nombre')