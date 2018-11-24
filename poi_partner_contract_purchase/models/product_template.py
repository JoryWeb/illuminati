# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, SUPERUSER_ID
class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    purchase_method = fields.Selection([
        ('purchase', 'Sobre Cantidades Entregadas'),
        ('receive', 'Sobre Cantidades Recibidas'),
        ('contract', 'Sobre Contrato de Compra'),
        ], string="Control facturas compra", default="receive")