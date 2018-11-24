# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpSubject(models.Model):
    _inherit = 'op.subject'

    german_name = fields.Char('Nombre en Aleman', required=True)
    matter_type = fields.Selection(
        [('obligatoria', 'Obligatoria'), ('electiva', 'Electiva')],
        'Tipo de Materia', default="", required=True)
    type = fields.Selection(
        [('teorica', 'Teorica'), ('practica', 'Practica'), ('ambos', 'Ambos'), ('otro', 'Otro')],
        'Tipo de Materia', default="", required=True)

