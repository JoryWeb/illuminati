# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, tools
from datetime import datetime
from odoo.tools.misc import formatLang, format_date, ustr
from odoo.tools.translate import _
import time
from odoo.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
import math
import json

class AccountReportFollowupManager(models.Model):
    _inherit = 'account.report.manager'

    partner_id = fields.Many2one('res.partner')

class report_account_followup_report(models.AbstractModel):
    _name = "account.followup.report"
    _description = "Followup Report"
    _inherit = 'account.report'

    filter_partner_id = False

    def get_columns_name(self, options):
        headers = [{}, 
                {'name': _(' Date '), 'class': 'date', 'style': 'text-align:center;'}, 
                {'name': _(' Due Date '), 'class': 'date', 'style': 'text-align:center;'}, 
                {'name': _('Communication'), 'style': 'text-align:right;'}, 
                {'name': _(' Expected Date '), 'class': 'date'}, 
                {'name': _(' Excluded '), 'class': 'date'}, 
                {'name': _(' Total Due '), 'class': 'number', 'style': 'text-align:right;'}
                ]
        if self.env.context.get('print_mode'):
            headers = headers[:4] + headers[6:]
        return headers

    def get_lines(self, options, line_id=None):
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []
        lang_code = partner.lang or self.env.user.lang or 'en_US'

        lines = []
        res = {}
        today = datetime.today().strftime('%Y-%m-%d')
        line_num = 0
        for l in partner.unreconciled_aml_ids:
            if self.env.context.get('print_mode') and l.blocked:
                continue
            currency = l.currency_id or l.company_id.currency_id
            if currency not in res:
                res[currency] = []
            res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            aml_recs = sorted(aml_recs, key=lambda aml: aml.blocked)
            for aml in aml_recs:
                amount = aml.currency_id and aml.amount_residual_currency or aml.amount_residual
                date_due = format_date(self.env, aml.date_maturity or aml.date, lang_code=lang_code)
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_overdue:
                    date_due = {'name': date_due, 'class': 'color-red date'}
                if is_payment:
                    date_due = ''
                amount = formatLang(self.env, amount, currency_obj=currency)
                amount = amount.replace(' ', '&nbsp;') if self.env.context.get('mail') else amount
                line_num += 1
                columns = [format_date(self.env, aml.date, lang_code=lang_code), date_due, aml.invoice_id.name or aml.name, aml.expected_pay_date and aml.expected_pay_date +' '+ aml.internal_note or '', {'name': aml.blocked, 'blocked': aml.blocked}, amount]
                if self.env.context.get('print_mode'):
                    columns = columns[:3]+columns[5:]
                lines.append({
                    'id': aml.id,
                    'name': aml.move_id.name,
                    'caret_options': 'followup',
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'columns': [type(v) == dict and v or {'name': v} for v in columns],
                })
            totalXXX = formatLang(self.env, total, currency_obj=currency)
            totalXXX = totalXXX.replace(' ', '&nbsp;') if self.env.context.get('mail') else totalXXX
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': 'total',
                'unfoldable': False,
                'level': 0,
                'columns': [{'name': v} for v in ['']*(2 if self.env.context.get('print_mode') else 4) + [total >= 0 and _('Total Due') or '', totalXXX]],
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                total_issued = total_issued.replace(' ', '&nbsp;') if self.env.context.get('mail') else total_issued
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'level': 0,
                    'columns': [{'name': v} for v in ['']*(2 if self.env.context.get('print_mode') else 4) + [_('Total Overdue'), total_issued]],
                })
        return lines

    def open_partner_form(self, options, params):
        return {'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'res_id': int(params.get('activeId')),
                'views': [[False, 'form']],
                'target': 'current',
            }

    def get_default_summary(self, options):
        return self.env.user.company_id.overdue_msg or self.env['res.company'].default_get(['overdue_msg'])['overdue_msg']

    def get_report_manager(self, options):
        domain = [('report_name', '=', 'account.followup.report'), ('partner_id', '=', options.get('partner_id'))]
        selected_companies = []
        if options.get('multi_company'):
            selected_companies = [c['id'] for c in options['multi_company'] if c.get('selected')]
        if len(selected_companies) == 1:
            domain += [('company_id', '=', selected_companies[0])]
        existing_manager = self.env['account.report.manager'].search(domain, limit=1)
        if existing_manager and not self.env.context.get('keep_summary'):
            existing_manager.write({'summary': self.get_default_summary(options)})
        if not existing_manager:
            existing_manager = self.env['account.report.manager'].create({'report_name': 'account.followup.report', 
                                                                        'company_id': selected_companies and selected_companies[0] or False, 
                                                                        'partner_id': options.get('partner_id'), 
                                                                        'summary': self.get_default_summary(options)})
        return existing_manager

    @api.multi
    def get_html(self, options, line_id=None, additional_context=None):
        if additional_context == None:
            additional_context = {}
        partner = self.env['res.partner'].browse(options['partner_id'])
        additional_context['partner'] = partner
        additional_context['invoice_address_id'] = self.env['res.partner'].browse(partner.address_get(['invoice'])['invoice'])
        additional_context['today'] = fields.date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        if self.env.context.get('followup_line_id'):
            report_manager = self.get_report_manager(options)
            report = {'name': self.get_report_name(),
                    'summary': report_manager.summary,
                    'company_name': self.env.user.company_id.name,
                    'followup_line': self.env['account_followup.followup.line'].browse(self.env.context.get('followup_line_id')),}
            additional_context['report'] = report
        return super(report_account_followup_report, self).get_html(options, line_id=line_id, additional_context=additional_context)

    def get_pdf(self, options, minimal_layout=True):
        return super(report_account_followup_report, self.with_context(keep_summary=True)).get_pdf(options, minimal_layout=False)

    def get_report_name(self):
        return _('Followup Report')

    def get_reports_buttons(self):
        return []

    def get_report_value(self, partner, options):
        options['partner_id'] = partner.id
        return {'name': self.get_report_name(), 'summary': self.get_report_manager(options).summary, 'company_name': self.env.user.company_id.name}

    def get_templates(self):
        templates = super(report_account_followup_report, self).get_templates()
        templates['main_template'] = 'account_reports.template_followup_report'
        templates['line_template'] = 'account_reports.line_template_followup_report'
        if self.env.context.get('print_mode') and not self.env.context.get('mail'):
            templates['main_template'] = 'account_reports.report_followup_letter'
        return templates

    def get_history(self, partner):
        return self.env['mail.message'].search([('subtype_id', '=', self.env.ref('account_reports.followup_logged_action').id), ('id', 'in', partner.message_ids.ids)], limit=5)

    @api.model
    def change_next_action(self, partner_id, date, note):
        partner = self.env['res.partner'].browse(partner_id)
        partner.write({'payment_next_action': note, 'payment_next_action_date': date})
        msg = _('Next action date: ') + date + '.\n' + note
        partner.message_post(body=msg, subtype='account_reports.followup_logged_action')
        return True

    def get_post_message(self, options):
        return _('Sent a followup email')

    @api.model
    def send_email(self, options):
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        email = self.env['res.partner'].browse(partner.address_get(['invoice'])['invoice']).email
        if email and email.strip():
            body_html = self.with_context(print_mode=True, mail=True, keep_summary=True).get_html(options)
            msg = self.get_post_message(options)
            msg += '<br>' + body_html.decode('utf-8')
            msg_id = partner.message_post(body=msg, subtype='account_reports.followup_logged_action')
            email = self.env['mail.mail'].with_context(default_mail_message_id=msg_id).create({
                'subject': _('%s Payment Reminder') % (self.env.user.company_id.name) + ' - ' + partner.name,
                'body_html': append_content_to_html(body_html, self.env.user.signature, plaintext=False),
                'email_from': self.env.user.email or '',
                'email_to': email,
                'body': msg,
            })
            return True
        raise UserError(_('Could not send mail to partner because it does not have any email address defined'))

    def print_followup(self, options, params):
        partner_id = params.get('partner')
        options['partner_id'] = partner_id
        return {
                'type': 'ir_actions_account_report_download',
                'data': {'model': 'account.followup.report',
                         'options': json.dumps(options),
                         'output_format': 'pdf',
                         }
                }


class account_report_followup_all(models.AbstractModel):
    _name = "account.followup.report.all"
    _description = "A progress bar for followup reports"
    _inherit = 'account.followup.report'

    PAGER_SIZE = 15

    filter_type_followup = 'action' #all or actions (need of actions)
    filter_skipped_partners = []
    filter_partners_to_show = []
    filter_pager = 1
    filter_total_pager = 1
    filter_progressbar = [0,0,0]

    def get_options(self, previous_options):
        options = super(account_report_followup_all, self).get_options(previous_options)
        options = self.compute_pages(options)
        return options

    def get_templates(self):
        templates = super(report_account_followup_report, self).get_templates()
        if self.env.context.get('print_mode') and not self.env.context.get('mail'):
            templates['main_template'] = 'account_reports.report_followup_letter'
        elif self.env.context.get('print_mode'):
            templates['main_template'] = 'account_reports.template_followup_report'
        else:
            templates['main_template'] = 'account_reports.report_followup_all'
            
        templates['line_template'] = 'account_reports.line_template_followup_report'
        templates['search_template'] = 'account_reports.followup_search_template'
        return templates

    def get_lines(self, options, line_id=None):
        lines = []
        if self.env.context.get('print_mode'):
            return super(account_report_followup_all, self).get_lines(options, line_id=line_id)
        for partner_id in options.get('partners_to_show'):
            options['partner_id'] = partner_id
            lines.append(super(account_report_followup_all, self).get_lines(options, line_id=line_id))
        return lines

    def get_partners_in_need_of_action(self, options):
        overdue_only = options.get('type_followup') == 'all'
        return self.env['res.partner'].get_partners_in_need_of_action(overdue_only=overdue_only)

    def compute_pages(self, options):
        partner_in_need_of_action = self.get_partners_in_need_of_action(options)
        partner_in_need_of_action = partner_in_need_of_action.sorted(key=lambda x: x.name or '')
        skipped_partners = self.env['res.partner'].browse(options.get('skipped_partners'))
        total_partners_to_do = (partner_in_need_of_action - skipped_partners).ids
        options['total_pager'] = int(1+ (len(total_partners_to_do)/self.PAGER_SIZE))
        max_index = min(len(total_partners_to_do), options['pager']*self.PAGER_SIZE)
        if options.get('pager') > (options['total_pager']):
            options['pager'] = options['total_pager']
        options['partners_to_show'] = total_partners_to_do[(options['pager']-1)*self.PAGER_SIZE:max_index]
        options['progressbar'][1] = len(total_partners_to_do)
        options['progressbar'][2] = int(100 * options['progressbar'][0] / (options['progressbar'][1] or 1))
        return options

    @api.multi
    def get_report_informations(self, options):
        informations = super(account_report_followup_all, self).get_report_informations(options)
        # build table of manager_id, partner_id
        map_partner_manager = {}
        options = informations['options']
        for partner_id in options.get('partners_to_show'):
            options['partner_id'] = partner_id
            map_partner_manager[partner_id] = self.with_context(keep_summary=True).get_report_manager(options).id
        informations['map_partner_manager'] = map_partner_manager
        return informations
