# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def _compute_ruex(self):
        for s in self:
            if s.partner_id:
                s.ruex = s.partner_id.ruex

    @api.multi
    def _inverse_ruex(self):
        for s in self:
            if s.partner_id:
                s.partner_id.ruex = s.ruex

    ruex = fields.Char('Ruex',  compute="_compute_ruex", inverse="_inverse_ruex")
