# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpTypeScholarship(models.Model):
    _name = 'op.type.scholarship'

    name = fields.Char("Nombre", required=True)
    discount = fields.Integer('Descuento')
    total_discount = fields.Integer('Descuento Total')
    first_pension_applies = fields.Boolean('Aplica Primera Pension')
    regular_pension_applies = fields.Boolean('Aplica Pension Regular')
    active = fields.Boolean('Activo')

