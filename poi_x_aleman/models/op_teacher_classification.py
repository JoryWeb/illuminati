# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpTeacherClassification(models.Model):
    _name = 'op.teacher.classification'

    name = fields.Char('Nombre', required=True)

