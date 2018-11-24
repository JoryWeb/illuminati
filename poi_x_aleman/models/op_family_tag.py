# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpFamilyTag(models.Model):
    _name = 'op.family.tag'

    name = fields.Char('Nombre', required=True)
    color = fields.Char(string="Color", help="Choose your color")
