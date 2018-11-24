# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from datetime import datetime

from odoo.tools import pycompat


class report_account_coa(models.AbstractModel):
    _name = "account.coa.report"
    _description = "Chart of Account Report"
    _inherit = "account.general.ledger"

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_comparison = {'date_from': '', 'date_to': '', 'filter': 'no_comparison', 'number_period': 1}
    filter_cash_basis = False
    filter_all_entries = False
    filter_hierarchy = False
    filter_unfold_all = None

    def get_templates(self):
        templates = super(report_account_coa, self).get_templates()
        templates['main_template'] = 'account_reports.template_coa_report'
        return templates

    def get_columns_name(self, options):
        columns = [
            {'name': ''},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
        ]
        if options.get('comparison') and options['comparison'].get('periods'):
            columns += [
                {'name': _('Debit'), 'class': 'number'},
                {'name': _('Credit'), 'class': 'number'},
            ] * len(options['comparison']['periods'])
        return columns + [
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
        ]

    def _post_process(self, grouped_accounts, initial_balances, options, comparison_table):
        lines = []
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        title_index = ''
        sorted_accounts = sorted(grouped_accounts, key=lambda a: a.code)
        zero_value = ''
        sum_columns = [0,0,0,0]
        for period in range(len(comparison_table)):
            sum_columns += [0, 0]
        for account in sorted_accounts:
            #skip accounts with all periods = 0 and no initial balance
            non_zero = False
            for p in range(len(comparison_table)):
                if not company_id.currency_id.is_zero(grouped_accounts[account][p]['balance']) or not company_id.currency_id.is_zero(initial_balances.get(account, 0)):
                    non_zero = True
            if not non_zero:
                continue

            initial_balance = initial_balances.get(account, 0.0)
            sum_columns[0] += initial_balance if initial_balance > 0 else 0
            sum_columns[1] += -initial_balance if initial_balance < 0 else 0
            cols = [
                {'name': initial_balance > 0 and self.format_value(initial_balance) or zero_value, 'no_format_name': initial_balance > 0 and initial_balance or 0},
                {'name': initial_balance < 0 and self.format_value(-initial_balance) or zero_value, 'no_format_name': initial_balance < 0 and abs(initial_balance) or 0},
            ]
            total_periods = 0
            for period in range(len(comparison_table)):
                amount = grouped_accounts[account][period]['balance']
                total_periods += amount
                cols += [{'name': amount > 0 and self.format_value(amount) or zero_value, 'no_format_name': amount > 0 and amount or 0},
                         {'name': amount < 0 and self.format_value(-amount) or zero_value, 'no_format_name': amount < 0 and abs(amount) or 0}]
                p_indice = period * 2 if period > 1 else 3
                p_indice = 1 if period == 0 else p_indice
                sum_columns[(p_indice) + 1] += amount if amount > 0 else 0
                sum_columns[(p_indice) + 2] += -amount if amount < 0 else 0

            total_amount = initial_balance + total_periods
            sum_columns[-2] += total_amount if total_amount > 0 else 0
            sum_columns[-1] += -total_amount if total_amount < 0 else 0
            cols += [
                {'name': total_amount > 0 and self.format_value(total_amount) or zero_value, 'no_format_name': total_amount > 0 and total_amount or 0},
                {'name': total_amount < 0 and self.format_value(-total_amount) or zero_value, 'no_format_name': total_amount < 0 and abs(total_amount) or 0},
                ]
            lines.append({
                'id': account.id,
                'name': account.code + " " + account.name,
                'columns': cols,
                'unfoldable': False,
                'caret_options': 'account.account',
            })
        lines.append({
             'id': 'grouped_accounts_total',
             'name': _('Total'),
             'class': 'o_account_reports_domain_total',
             'columns': [{'name': self.format_value(v)} for v in sum_columns],
             'level': 0,
        })
        return lines

    @api.model
    def get_lines(self, options, line_id=None):
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        grouped_accounts = {}
        initial_balances = {}
        comparison_table = [options.get('date')]
        comparison_table += options.get('comparison') and options['comparison'].get('periods') or []

        #get the balance of accounts for each period
        period_number = 0
        for period in reversed(comparison_table):
            res = self.with_context(date_from_aml=period['date_from'], date_to=period['date_to'], date_from=period['date_from'] and company_id.compute_fiscalyear_dates(datetime.strptime(period['date_from'], "%Y-%m-%d"))['date_from'] or None).group_by_account_id(options, line_id)  # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
            if period_number == 0:
                initial_balances = dict([(k, res[k]['initial_bal']['balance']) for k in res])
            for account in res:
                if account not in grouped_accounts:
                    grouped_accounts[account] = [{'balance': 0, 'debit': 0, 'credit': 0} for p in comparison_table]
                grouped_accounts[account][period_number]['balance'] = res[account]['balance'] - res[account]['initial_bal']['balance']
                grouped_accounts[account][period_number]['debit'] = res[account]['debit'] - res[account]['initial_bal']['debit']
                grouped_accounts[account][period_number]['credit'] = res[account]['credit'] - res[account]['initial_bal']['credit']
            period_number += 1

        #build the report
        lines = self._post_process(grouped_accounts, initial_balances, options, comparison_table)
        return lines

    @api.model
    def get_report_name(self):
        return _("Trial Balance")
