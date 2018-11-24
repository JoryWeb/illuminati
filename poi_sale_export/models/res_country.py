# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ResCountry(models.Model):
    _inherit = 'res.country'

    name_code_export = fields.Char('Nombre Codigo Exportacion')
