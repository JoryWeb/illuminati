# -*- coding: utf-8 -*-

from odoo import models, fields, api


class opFamily(models.Model):
    _name = 'op.family'

    name = fields.Char("Codigo de Familia", required=True)
    nit = fields.Char('NIT')
    social_reason = fields.Char('Razon Social')
    start_date = fields.Date('Fecha de Entrada')
    end_date = fields.Date('Fecha de Salida')

    parents_ids = fields.Many2many('op.parent.contact', ondelete='cascade')
    childs_ids = fields.Many2many('op.student', ondelete='cascade')

    notes = fields.Text('Notas')


