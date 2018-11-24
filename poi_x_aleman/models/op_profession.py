# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpProfession(models.Model):
    _name = 'op.profession'

    name = fields.Char("Nombre", required=True)

