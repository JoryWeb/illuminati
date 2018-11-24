#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from odoo import api, models, fields, _, tools
from odoo.osv import expression

class AccountMoveSequenceWizard(models.TransientModel):
    _name = "account.move.sequence.wizard"
    _description = 'Wizard Alternative Name on Moves'

    only_selected = fields.Boolean('Only Selected')
    journal_id = fields.Many2one('account.journal', string="Journal")
    partner_id = fields.Many2one('res.partner', string="Partner")
    analytic_account_tag_id = fields.Many2one('account.analytic.tag','Analytic Account Tag')
    analytic_account_id = fields.Many2one('account.analytic.account', "Analytic Account")
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    start_number = fields.Integer('Start Number', default=1)
    prefix = fields.Char("Prefix", default="")
    suffix = fields.Char("Suffix", default="")
    padding = fields.Char("Padding", default=0)


    @api.multi
    def apply_sequence(self):

        ### THIS FUNCTION GETS ALL THE CHILD TAGS
        def get_tag_child_ids(tag_ids):
            tag_obj = self.env['account.analytic.tag']
            res = []
            for atag in tag_obj.browse(tag_ids):
                for ctag in atag.child_ids:
                    res.append(ctag.id)
                    res += get_tag_child_ids([ctag.id])
            return res

        active_ids = self.env.context.get("active_ids")
        account_move_obj = self.env['account.move']
        account_moves = []
        start_number = 1
        prefix = ""
        suffix = ""
        if not self.suffix:
            self.suffix = ""
        if not self.prefix:
            self.prefix = ""


        for data in self:
            if data.only_selected:
                account_moves = account_move_obj.search([('id','in', active_ids)], order="date")
            else:
                report_domain = []
                if data.journal_id:
                    domain = [('journal_id','>=',data.journal_id.id)]
                    report_domain = expression.AND([domain] + [report_domain])
                if data.partner_id:
                    domain = [('partner_id','>=',data.partner_id.id)]
                    report_domain = expression.AND([domain] + [report_domain])
                if data.analytic_account_id:
                    domain = [('analytic_account_id', '=', data.analytic_account_id.id)]
                    report_domain = expression.AND([domain] + [report_domain])
                if data.analytic_account_tag_id:
                    atag_ids = get_tag_child_ids([data.analytic_account_tag_id.id])
                    analytic_account_ids = self.env['account.analytic.account'].search([('tag_ids', 'in', atag_ids)])
                    if analytic_account_ids:
                        domain = [('analytic_account_id', 'in', analytic_account_ids.ids)]
                        report_domain = expression.AND([domain] + [report_domain])
                if data.date_from:
                    domain = [('date','>=',data.date_from)]
                    report_domain = expression.AND([domain] + [report_domain])
                if data.date_to:
                    domain = [('date','<=',data.date_to)]
                    report_domain = expression.AND([domain] + [report_domain])

                account_moves = account_move_obj.search(report_domain, order="date")
            if data.start_number:
                start_number = data.start_number
            prefix = (data.prefix and str(data.prefix)) or prefix
            suffix = (data.prefix and str(data.suffix)) or suffix
            padding = data.padding

        for move in account_moves:

            new_name = prefix+'%%0%sd' % padding  % start_number+suffix
            move.write({'folio': new_name})

            start_number+=1

        model_data_id = self.env['ir.model.data']._get_id('account', 'view_move_tree')
        res_id = self.env['ir.model.data'].browse(model_data_id).res_id
        return {
            'name': _('Asientos Contables'),
            'domain': [('id','in',account_moves.ids)],
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'account.move',
            'view_id': res_id,
            'context': {},
            'type': 'ir.actions.act_window'
        }
