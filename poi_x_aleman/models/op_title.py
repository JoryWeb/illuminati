# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpTitle(models.Model):
    _name = 'op.title'

    name = fields.Char('Nombre', required=True)

