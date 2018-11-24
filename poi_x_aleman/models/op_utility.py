# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning

class OpYear(models.Model):
    _name = "op.year"

    name = fields.Char('Año')


class OpMonth(models.Model):
    _name = "op.month"

    name = fields.Char('Mes')
