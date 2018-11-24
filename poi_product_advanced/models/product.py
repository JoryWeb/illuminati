

from odoo import models, fields, api, _


class AtributoNombre(models.Model):
    _name = 'atributo.nombre'
    name = fields.Char("Nombre")

class AtributoProduct(models.Model):
    _name = 'atributo.product'
    product_id = fields.Many2one("product.template", "Producto")
    name = fields.Many2one("atributo.nombre", string="Nombre")
    valor = fields.Char(string=u"Valor")

class ProductImage(models.Model):
    _name = 'product.image'
    _description = 'Product Image'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    image_alt = fields.Text(string='Image Label')
    image = fields.Binary(string='Image')
    image_small = fields.Binary(string='Small Image')
    image_url = fields.Char(string='Image URL')
    product_tmpl_id = fields.Many2one('product.template', 'Product',
                                      copy=False)
    product_variant_id = fields.Many2one('product.product', 'Product Variant',
                                         copy=False)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    atributo_line = fields.One2many('atributo.product', 'product_id', string="Atributos", copy=True)
    link_fabricator = fields.Char(u'Página web fabricante')
    link_video = fields.Char(u'Video demostración del Producto')
    images = fields.One2many('product.image', 'product_tmpl_id', 'Images')
    variant_bool = fields.Boolean(string='Show Variant Wise Images',
                                  help='Check if you like to show variant wise'
                                       ' images in WebSite', auto_join=True)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    images_variant = fields.One2many('product.image', 'product_variant_id',
                                     'Images')