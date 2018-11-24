# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import formatLang


class account_bank_reconciliation_report(models.AbstractModel):
    _name = 'account.bank.reconciliation.report'
    _description = 'Bank reconciliation report'
    _inherit = "account.report"

    filter_date = {'date': '', 'filter': 'today'}

    #used to enumerate the 'layout' lines with a distinct ID
    line_number = 0

    def get_columns_name(self, options):
        return [
            {'name': ''},
            {'name': _("Date")},
            {'name': _("Reference")},
            {'name': _("Amount"), 'class': 'number'},
        ]

    def add_title_line(self, options, title, amount):
        self.line_number += 1
        return {
            'id': 'line_' + str(self.line_number),
            'name': title,
            'columns': [{'name': v} for v in [options['date']['date'], '', self.format_value(amount)]],
            'level': 0,
        }

    def add_subtitle_line(self, title, amount=None):
        self.line_number += 1
        return {
            'id': 'line_' + str(self.line_number),
            'name': title,
            'columns': [{'name': v} for v in ['', '', amount and self.format_value(amount) or '']],
            'level': 1,
        }

    def add_total_line(self, amount):
        self.line_number += 1
        return {
            'id': 'line_' + str(self.line_number),
            'name': '',
            'columns': [{'name': v} for v in ["", "", self.format_value(amount)]],
            'level': 2,
        }

    def add_bank_statement_line(self, line, amount):
        name = line.name
        return {
            'id': str(line.id),
            #'statement_id': line.statement_id.id,
            #'type': 'bank_statement_id',
            'caret_options': True,
            'name': len(name) >= 85 and name[0:80] + '...' or name,
            'columns': [{'name': v} for v in [line.date, line.ref, self.format_value(amount)]],
            'level': 1,
        }

    def print_pdf(self, options):
        options['active_id'] = self.env.context.get('active_id')
        return super(account_bank_reconciliation_report, self).print_pdf(options)

    def print_xlsx(self, options):
        options['active_id'] = self.env.context.get('active_id')
        return super(account_bank_reconciliation_report, self).print_xlsx(options)

    @api.model
    def get_lines(self, options, line_id=None):
        journal_id = self._context.get('active_id') or options.get('active_id')
        journal = self.env['account.journal'].browse(journal_id)
        lines = []
        #Start amount
        use_foreign_currency = bool(journal.currency_id)
        account_ids = list(set([journal.default_debit_account_id.id, journal.default_credit_account_id.id]))
        lines_already_accounted = self.env['account.move.line'].search([('account_id', 'in', account_ids),
                                                                        ('date', '<=', self.env.context['date_to']),
                                                                        ('company_id', 'in', self.env.context['company_ids'])])
        start_amount = sum([line.amount_currency if use_foreign_currency else line.balance for line in lines_already_accounted])
        lines.append(self.add_title_line(options, _("Current Balance in GL"), start_amount))

        # Un-reconcilied bank statement lines
        move_lines = self.env['account.move.line'].search([('move_id.journal_id', '=', journal_id),
                                                           '|', ('statement_line_id', '=', False), ('statement_line_id.date', '>', self.env.context['date_to']),
                                                           ('user_type_id.type', '=', 'liquidity'),
                                                           ('full_reconcile_id', '=', False),
                                                           ('date', '<=', self.env.context['date_to']),
                                                           ('company_id', 'in', self.env.context['company_ids'])])
        unrec_tot = 0
        if move_lines:
            tmp_lines = []
            for line in move_lines:
                self.line_number += 1
                tmp_lines.append({
                    'id': str(line.id),
                    #'move_id': line.move_id.id,
                    #'type': 'move_line_id',
                    #'action': line.get_model_id_and_name(),
                    'name': line.name,
                    'columns': [{'name': v} for v in [line.date, line.ref, self.format_value(line.balance)]],
                    'level': 1,
                })
                unrec_tot += line.amount_currency if use_foreign_currency else line.balance
            if unrec_tot > 0:
                title = _("Plus Unreconciled Payments")
            else:
                title = _("Minus Unreconciled Payments")
            lines.append(self.add_subtitle_line(title))
            lines += tmp_lines
            lines.append(self.add_total_line(unrec_tot))

        # Outstanding plus
        not_reconcile_plus = self.env['account.bank.statement.line'].search([('statement_id.journal_id', '=', journal_id),
                                                                             ('date', '<=', self.env.context['date_to']),
                                                                             ('journal_entry_ids', '=', False),
                                                                             ('amount', '>', 0),
                                                                             ('company_id', 'in', self.env.context['company_ids'])])
        outstanding_plus_tot = 0
        if not_reconcile_plus:
            lines.append(self.add_subtitle_line(_("Plus Unreconciled Statement Lines")))
            for line in not_reconcile_plus:
                lines.append(self.add_bank_statement_line(line, line.amount))
                outstanding_plus_tot += line.amount
            lines.append(self.add_total_line(outstanding_plus_tot))

        # Outstanding less
        not_reconcile_less = self.env['account.bank.statement.line'].search([('statement_id.journal_id', '=', journal_id),
                                                                             ('date', '<=', self.env.context['date_to']),
                                                                             ('journal_entry_ids', '=', False),
                                                                             ('amount', '<', 0),
                                                                             ('company_id', 'in', self.env.context['company_ids'])])
        outstanding_less_tot = 0
        if not_reconcile_less:
            lines.append(self.add_subtitle_line(_("Minus Unreconciled Statement Lines")))
            for line in not_reconcile_less:
                lines.append(self.add_bank_statement_line(line, line.amount))
                outstanding_less_tot += line.amount
            lines.append(self.add_total_line(outstanding_less_tot))

        # Final
        computed_stmt_balance = start_amount + outstanding_plus_tot + outstanding_less_tot + unrec_tot
        last_statement = self.env['account.bank.statement'].search([('journal_id', '=', journal_id),
                                       ('date', '<=', self.env.context['date_to']), ('company_id', 'in', self.env.context['company_ids'])], order="date desc, id desc", limit=1)
        real_last_stmt_balance = last_statement.balance_end
        if computed_stmt_balance != real_last_stmt_balance:
            if real_last_stmt_balance - computed_stmt_balance > 0:
                title = _("Plus Missing Statements")
            else:
                title = _("Minus Missing Statements")
            lines.append(self.add_subtitle_line(title, real_last_stmt_balance - computed_stmt_balance))
        lines.append(self.add_title_line(options, _("Equal Last Statement Balance"), real_last_stmt_balance))
        return lines

    @api.model
    def get_report_name(self):
        journal_id = self._context.get('active_id')
        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
            return _("Bank Reconciliation") + ': ' + journal.name
        return _("Bank Reconciliation")
