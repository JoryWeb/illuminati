# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpRelationship(models.Model):
    _name = 'op.relationship'

    name = fields.Char('Nombre', required=True)

