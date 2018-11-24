# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api, tools

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    civil_state = fields.Selection([
    							('single', 'Soletero(a)'),
                                ('married', 'Casado(a)'),
                                ('widowed', 'Viudo(a)'),
                                ('divorced', 'Divorciado(a)'),
                                ('other', 'Otro')
                               ], string="Estado Civil")

    partner_recommend_id = fields.Many2one('res.partner', 'Recomendado Por')
    family_ids = fields.One2many('res.partner.family', 'partner_id', string="Familia")


class ResPartnerFamily(models.Model):
	_name = "res.partner.family"

	partner_id = fields.Many2one('res.partner', 'Cliente')
	name = fields.Char('Nombre')
	ci = fields.Char('C.I.')
	date_born = fields.Date('Fecha de Nacimiento')
	ocupation = fields.Char('Ocupacion')
