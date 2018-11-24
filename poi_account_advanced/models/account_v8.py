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

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval


class AccountSegment(models.Model):
    _name = 'account.segment'

    code = fields.Char('Code', size=12)
    name = fields.Char('Name', size=128, required=True)

class AccountSegmentRule(models.Model):
    _name = 'account.segment.rule'

    sequence = fields.Integer('Prioridad', required=True)
    field = fields.Selection([('product_id|product.product', 'Product'),
                              ('create_uid|res.users', 'User'),
                              ('partner_id|res.partner', 'Partner')], string="Criterio")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    @api.multi
    @api.depends('product_id', 'partner_id', 'create_uid')
    def _compute_segment(self):
        rule_ids = self.env['account.segment.rule'].sudo().search_read([], ['field'], order='sequence')
        if len(rule_ids) == 0:
            return True
        for mline in self:
            if mline.segment_origin_id:
                mline.segment_id = mline.segment_origin_id.id
                continue
            for criteria in rule_ids:
                f, o = criteria['field'].split('|')
                o_id = safe_eval('mline.' + f + '.id', {'mline':mline})
                if o_id:
                    o_read = self.env[o].browse([o_id])
                    seg_id = o_read and o_read[0] and o_read[0].segment_id and o_read[0].segment_id.id or False
                    if seg_id:
                        mline.segment_id = seg_id
                        break

    segment_id = fields.Many2one('account.segment', 'Segmento', ondelete='restrict', compute=_compute_segment, store=True)
    segment_origin_id = fields.Many2one('account.segment', 'Segmento Origen', ondelete='restrict')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def line_get_convert(self, line, part):
        """Ensures that a Segment inputed in the invoice line
            gets copied to the corresponding account move line when confirming
        """
        ret = super(AccountInvoice, self).line_get_convert(line, part)

        if 'invl_id' in line:
            line_o = self.env['account.invoice.line'].browse(line['invl_id'])
            if line_o.segment_id and line_o.segment_id.id:
                ret.update({'segment_id': line_o.segment_id.id, 'segment_origin_id': line_o.segment_id.id})

        return ret


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    segment_id = fields.Many2one('account.segment', 'Segmento', ondelete='restrict')

# THERE ARE NO PERIODS ANYMORE
#class AccountJournal(models.Model):
#    _inherit = 'account.journal'
#
#    blocked_period_ids = fields.Many2many('account.period','account_period_journal_block_rel', 'journal_id', 'period_id',string='Periodos a bloquear')
#

#class AccountPeriod(models.Model):
#    _inherit = "account.period"

#    blocked_journal_ids = fields.Many2many('account.journal','account_period_journal_block_rel', 'period_id', 'journal_id',string='Diarios a bloquear')
