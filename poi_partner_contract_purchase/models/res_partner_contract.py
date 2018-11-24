##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, exceptions, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    contract_ids = fields.One2many('res.partner.contract', 'partner_id', 'Contracts associated')

CONTRACT_TYPES = [('draft', 'Borrador'),
                  ('in_review', 'En Vista'),
                  ('valid', 'Valido'),
                  ('completed', 'Completado'),
                  ('canceled', 'Cancelado'),
                  ('expired', 'Expirado')]

class ResPartnerContract(models.Model):
    _name = 'res.partner.contract'
    _description = 'Contracts related to Partner'
    _inherit = ['mail.thread']

    _track = {
        'state': {
            'contract.mt_contract_in_review': lambda self, cr, uid, obj, ctx=None: obj.state == 'in_review',
            'contract.mt_contract_valid': lambda self, cr, uid, obj, ctx=None: obj.state == 'valid',
            'contract.mt_contract_completed': lambda self, cr, uid, obj, ctx=None: obj.state == 'completed',
            'contract.mt_contract_canceled': lambda self, cr, uid, obj, ctx=None: obj.state == 'canceled',
            'contract.mt_contract_expired': lambda self, cr, uid, obj, ctx=None: obj.state == 'expired',
        },
    }

    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    date_start = fields.Date('Date Start', required=True)
    date_end = fields.Date('Date End', required=True)
    contract_number = fields.Char('Contract Number', size=64, required=True)
    contract_amount = fields.Float('Contract Amount', default=0.0, required=True)
    type = fields.Selection([('sale', 'Sale'),('purchase','Purchase')], string='Contract Type', required=True)
    state = fields.Selection(CONTRACT_TYPES, string='State', default='draft', required=True)
    contract_id = fields.Many2one('res.partner.contract', 'Contract', required=True, ondelete="cascade", select=True, auto_join=True)

    @api.model
    def default_get(self, fields):
        res = super(ResPartnerContract, self).default_get(fields)
        res.update({'type': 'purchase'})
        return res

    _rec_name = 'contract_number'
