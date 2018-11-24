# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import timedelta


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    payment_next_action = fields.Text('Next Action', copy=False, company_dependent=True,
                                      help="Note regarding the next action.")
    payment_next_action_date = fields.Date('Next Action Date', copy=False, company_dependent=True,
                                           help="The date before which no action should be taken.")
    unreconciled_aml_ids = fields.One2many('account.move.line', 'partner_id', domain=[('reconciled', '=', False),
                                           ('account_id.deprecated', '=', False), ('account_id.internal_type', '=', 'receivable')])

    partner_ledger_label = fields.Char(compute='_compute_partner_ledger_label', help='The label to display on partner ledger button, in form view')

    @api.depends('supplier', 'customer')
    def _compute_partner_ledger_label(self):
        for record in self:
            if record.supplier == record.customer:
                record.partner_ledger_label = _('Partner Ledger')
            elif record.supplier:
                record.partner_ledger_label = _('Supplier Ledger')
            else:
                record.partner_ledger_label = _('Customer Ledger')

    def get_partners_in_need_of_action(self, overdue_only=False):
        result = []
        today = fields.Date.context_today(self)
        partners = self.search([('payment_next_action_date', '>', today)])
        domain = partners.with_context(exclude_given_ids=True).get_followup_lines_domain(today, overdue_only=overdue_only, only_unblocked=True)
        query = self.env['account.move.line']._where_calc(domain)
        tables, where_clause, where_params = query.get_sql()
        sql = """SELECT "account_move_line".partner_id
                 FROM %s
                 WHERE %s GROUP BY "account_move_line".partner_id"""
        query = sql % (tables, where_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        for res in results:
            if res[0]:
                result.append(res[0])
        return self.browse(result)

    def get_followup_lines_domain(self, date, overdue_only=False, only_unblocked=False):
        domain = super(ResPartner, self).get_followup_lines_domain(date, overdue_only=overdue_only, only_unblocked=only_unblocked)
        overdue_domain = ['|', '&', ('date_maturity', '!=', False), ('date_maturity', '<=', date), '&', ('date_maturity', '=', False), ('date', '<=', date)]
        if not overdue_only:
            domain += ['|', '&', ('next_action_date', '=', False)] + overdue_domain + ['&', ('next_action_date', '!=', False), ('next_action_date', '<=', date)]
        return domain

    @api.multi
    def update_next_action(self, batch=False):
        """Updates the next_action_date of the right account move lines"""
        today = fields.datetime.now()
        next_action_date = today + timedelta(days=self.env.user.company_id.days_between_two_followups)
        next_action_date = next_action_date.strftime('%Y-%m-%d')
        today = fields.Date.context_today(self)
        domain = self.get_followup_lines_domain(today)
        aml = self.env['account.move.line'].search(domain)
        aml.write({'next_action_date': next_action_date})
        if batch:
            return self.env['res.partner']
        return

    @api.multi
    def open_action_followup(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({
            'model': 'account.followup.report',
            'lang': self.lang,
        })
        return {
                'name': _("Overdue Payments for %s") % self.display_name,
                'type': 'ir.actions.client',
                'tag': 'account_report_followup',
                'context': ctx,
                'options': {'partner_id': self.id},
            }

    def open_partner_ledger(self):
        return {'type': 'ir.actions.client',
            'name': _('Partner Ledger'),
            'tag': 'account_report',
            'options': {'partner_id': self.id},
            'ignore_session': 'both',
            'context': "{'model':'account.partner.ledger'}"}

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification',
                     subtype=None, parent_id=False, attachments=None,
                     content_subtype='html', **kwargs):
        # A reply to a followup logged note should be of the same subtype, so that it will be
        # displayed in the history of the followup letter as well.
        if parent_id:
            parent = self.env['mail.message'].browse(parent_id)
            followup_subtype = self.env.ref('account_reports.followup_logged_action')
            if subtype and parent.subtype_id == followup_subtype:
                subtype = 'account_reports.followup_logged_action'

        return super(ResPartner, self).message_post(
                body=body, subject=subject, message_type=message_type, subtype=subtype,
                parent_id=parent_id, attachments=attachments, content_subtype=content_subtype,
                **kwargs)
