# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.tools.misc import format_date


class report_account_aged_partner(models.AbstractModel):
    _name = "account.aged.partner"
    _description = "Aged Partner Balances"
    _inherit = 'account.report'

    filter_date = {'date': '', 'filter': 'today'}
    filter_unfold_all = False

    def get_columns_name(self, options):
        columns = [{}]
        columns += [{'name': v, 'class': 'number'} for v in [_("Not&nbsp;due&nbsp;on %s") % format_date(self.env, options['date']['date']), _("0&nbsp;-&nbsp;30"), _("30&nbsp;-&nbsp;60"), _("60&nbsp;-&nbsp;90"), _("90&nbsp;-&nbsp;120"), _("Older"), _("Total")]]
        return columns

    def get_templates(self):
        templates = super(report_account_aged_partner, self).get_templates()
        templates['main_template'] = 'account_reports.template_aged_partner_balance_report'
        try:
            self.env['ir.ui.view'].get_view_id('account_reports.template_aged_partner_balance_line_report')
            templates['line_template'] = 'account_reports.template_aged_partner_balance_line_report'
        except ValueError:
            pass
        return templates

    @api.model
    def get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        results, total, amls = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
        for values in results:
            if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                continue
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    caret_type = 'account.move'
                    if aml.invoice_id:
                        caret_type = 'account.invoice.in' if aml.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name if aml.move_id.name else '/',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [line['period'] == 6-i and self.format_value(sign * line['amount']) or '' for i in range(7)]],
                    }
                    lines.append(vals)
                vals = {
                    'id': values['partner_id'],
                    'class': 'o_account_reports_domain_total',
                    'name': _('Total '),
                    'parent_id': 'partner_%s' % (values['partner_id'],),
                    'columns': [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                }
                lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 'None',
                'columns': [{'name': self.format_value(sign * v)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines


class report_account_aged_receivable(models.AbstractModel):
    _name = "account.aged.receivable"
    _description = "Aged Receivable"
    _inherit = "account.aged.partner"

    def set_context(self, options):
        ctx = super(report_account_aged_receivable, self).set_context(options)
        ctx['account_type'] = 'receivable'
        return ctx

    def get_report_name(self):
        return _("Aged Receivable")

    def get_templates(self):
        templates = super(report_account_aged_receivable, self).get_templates()
        templates['main_template'] = 'account_reports.template_aged_receivable_report'
        templates['line_template'] = 'account_reports.line_template_aged_receivable_report'
        return templates


class report_account_aged_payable(models.AbstractModel):
    _name = "account.aged.payable"
    _description = "Aged Payable"
    _inherit = "account.aged.partner"

    def set_context(self, options):
        ctx = super(report_account_aged_payable, self).set_context(options)
        ctx['account_type'] = 'payable'
        ctx['aged_balance'] = True
        return ctx

    def get_report_name(self):
        return _("Aged Payable")

    def get_templates(self):
        templates = super(report_account_aged_payable, self).get_templates()
        templates['main_template'] = 'account_reports.template_aged_payable_report'
        templates['line_template'] = 'account_reports.line_template_aged_payable_report'
        return templates
