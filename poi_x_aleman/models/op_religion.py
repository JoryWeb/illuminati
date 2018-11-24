# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpReligion(models.Model):
    _name = 'op.religion'

    name = fields.Char('Nombre', required=True)

