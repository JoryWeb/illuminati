# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ProductoTemplate(models.Model):
    _inherit = 'product.template'

    nandina = fields.Char(u'Código NANDINA')
