# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from datetime import datetime, timedelta
from odoo.addons.web.controllers.main import clean_action
from odoo.tools import float_is_zero

class report_account_general_ledger(models.AbstractModel):
    _name = "account.general.ledger"
    _description = "General Ledger Report"
    _inherit = "account.report"

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_cash_basis = False
    filter_all_entries = False
    filter_journals = True
    filter_analytic = True
    filter_unfold_all = False

    def get_templates(self):
        templates = super(report_account_general_ledger, self).get_templates()
        templates['main_template'] = 'account_reports.template_general_ledger_report'
        templates['line_template'] = 'account_reports.line_template_general_ledger_report'
        return templates

    def get_columns_name(self, options):
        return [{'name': ''},
                {'name': _("Date"), 'class': 'date'},
                {'name': _("Communication")},
                {'name': _("Partner")},
                {'name': _("Currency"), 'class': 'number'},
                {'name': _("Debit"), 'class': 'number'},
                {'name': _("Credit"), 'class': 'number'},
                {'name': _("Balance"), 'class': 'number'}]

    def _get_with_statement(self, user_types, domain=None):
        """ This function allow to define a WITH statement as prologue to the usual queries returned by query_get().
            It is useful if you need to shadow a table entirely and let the query_get work normally although you're
            fetching rows from your temporary table (built in the WITH statement) instead of the regular tables.

            @returns: the WITH statement to prepend to the sql query and the parameters used in that WITH statement
            @rtype: tuple(char, list)
        """
        sql = ''
        params = []

        #Cash basis option
        #-----------------
        #In cash basis, we need to show amount on income/expense accounts, but only when they're paid AND under the payment date in the reporting, so
        #we have to make a complex query to join aml from the invoice (for the account), aml from the payments (for the date) and partial reconciliation
        #(for the reconciled amount).
        if self.env.context.get('cash_basis'):
            if not user_types:
                return sql, params
            #we use query_get() to filter out unrelevant journal items to have a shadowed table as small as possible
            tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=domain)
            sql = """WITH account_move_line AS (
              SELECT \"account_move_line\".id, \"account_move_line\".date, \"account_move_line\".name, \"account_move_line\".debit_cash_basis, \"account_move_line\".credit_cash_basis, \"account_move_line\".move_id, \"account_move_line\".account_id, \"account_move_line\".journal_id, \"account_move_line\".balance_cash_basis, \"account_move_line\".amount_residual, \"account_move_line\".partner_id, \"account_move_line\".reconciled, \"account_move_line\".company_id, \"account_move_line\".company_currency_id, \"account_move_line\".amount_currency, \"account_move_line\".balance, \"account_move_line\".user_type_id, \"account_move_line\".analytic_account_id
               FROM """ + tables + """
               WHERE (\"account_move_line\".journal_id IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                 OR \"account_move_line\".move_id NOT IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s))
                 AND """ + where_clause + """
              UNION ALL
              (
               WITH payment_table AS (
                 SELECT aml.move_id, \"account_move_line\".date, CASE WHEN aml.balance = 0 THEN 0 ELSE part.amount / ABS(am.amount) END as matched_percentage
                   FROM account_partial_reconcile part LEFT JOIN account_move_line aml ON aml.id = part.debit_move_id LEFT JOIN account_move am ON aml.move_id = am.id,""" + tables + """
                   WHERE part.credit_move_id = "account_move_line".id
                    AND "account_move_line".user_type_id IN %s
                    AND """ + where_clause + """
                 UNION ALL
                 SELECT aml.move_id, \"account_move_line\".date, CASE WHEN aml.balance = 0 THEN 0 ELSE part.amount / ABS(am.amount) END as matched_percentage
                   FROM account_partial_reconcile part LEFT JOIN account_move_line aml ON aml.id = part.credit_move_id LEFT JOIN account_move am ON aml.move_id = am.id,""" + tables + """
                   WHERE part.debit_move_id = "account_move_line".id
                    AND "account_move_line".user_type_id IN %s
                    AND """ + where_clause + """
               )
               SELECT aml.id, ref.date, aml.name,
                 CASE WHEN aml.debit > 0 THEN ref.matched_percentage * aml.debit ELSE 0 END AS debit_cash_basis,
                 CASE WHEN aml.credit > 0 THEN ref.matched_percentage * aml.credit ELSE 0 END AS credit_cash_basis,
                 aml.move_id, aml.account_id, aml.journal_id,
                 ref.matched_percentage * aml.balance AS balance_cash_basis,
                 aml.amount_residual, aml.partner_id, aml.reconciled, aml.company_id, aml.company_currency_id, aml.amount_currency, aml.balance, aml.user_type_id, aml.analytic_account_id
                FROM account_move_line aml
                RIGHT JOIN payment_table ref ON aml.move_id = ref.move_id
                WHERE journal_id NOT IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                  AND aml.move_id IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s)
              )
            ) """
            params = [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)]
        return sql, params

    def do_query_unaffected_earnings(self, options, line_id):
        ''' Compute the sum of ending balances for all accounts that are of a type that does not bring forward the balance in new fiscal years.
            This is needed to balance the trial balance and the general ledger reports (to have total credit = total debit)
        '''

        select = '''
        SELECT COALESCE(SUM("account_move_line".balance), 0),
               COALESCE(SUM("account_move_line".amount_currency), 0),
               COALESCE(SUM("account_move_line".debit), 0),
               COALESCE(SUM("account_move_line".credit), 0)'''
        if options.get('cash_basis'):
            select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        select += " FROM %s WHERE %s"
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types, domain=[('user_type_id.include_initial_balance', '=', False)])
        tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=[('user_type_id.include_initial_balance', '=', False)])
        query = select % (tables, where_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        res = self.env.cr.fetchone()
        return {'balance': res[0], 'amount_currency': res[1], 'debit': res[2], 'credit': res[3]}

    def _do_query(self, options, line_id, group_by_account=True, limit=False):
        if group_by_account:
            select = "SELECT \"account_move_line\".account_id"
            select += ',COALESCE(SUM(\"account_move_line\".debit-\"account_move_line\".credit), 0),SUM(\"account_move_line\".amount_currency),SUM(\"account_move_line\".debit),SUM(\"account_move_line\".credit)'
            if options.get('cash_basis'):
                select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        else:
            select = "SELECT \"account_move_line\".id"
        sql = "%s FROM %s WHERE %s%s"
        if group_by_account:
            sql +=  "GROUP BY \"account_move_line\".account_id"
        else:
            sql += " GROUP BY \"account_move_line\".id"
            sql += " ORDER BY MAX(\"account_move_line\".date),\"account_move_line\".id"
            if limit and isinstance(limit, int):
                sql += " LIMIT " + str(limit)
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types)
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        line_clause = line_id and ' AND \"account_move_line\".account_id = ' + str(line_id) or ''
        query = sql % (select, tables, where_clause, line_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        return results

    def do_query(self, options, line_id):
        results = self._do_query(options, line_id, group_by_account=True, limit=False)
        used_currency = self.env.user.company_id.currency_id
        compute_table = {
            a.id: a.company_id.currency_id.compute
            for a in self.env['account.account'].browse([k[0] for k in results])
        }
        results = dict([(
            k[0], {
                'balance': compute_table[k[0]](k[1], used_currency) if k[0] in compute_table else k[1],
                'amount_currency': k[2],
                'debit': compute_table[k[0]](k[3], used_currency) if k[0] in compute_table else k[3],
                'credit': compute_table[k[0]](k[4], used_currency) if k[0] in compute_table else k[4],
            }
        ) for k in results])
        return results

    def group_by_account_id(self, options, line_id):
        accounts = {}
        results = self.do_query(options, line_id)
        initial_bal_date_to = datetime.strptime(self.env.context['date_from_aml'], "%Y-%m-%d") + timedelta(days=-1)
        initial_bal_results = self.with_context(date_to=initial_bal_date_to.strftime('%Y-%m-%d')).do_query(options, line_id)
        unaffected_earnings_xml_ref = self.env.ref('account.data_unaffected_earnings')
        unaffected_earnings_line = True  # used to make sure that we add the unaffected earning initial balance only once
        if unaffected_earnings_xml_ref:
            #compute the benefit/loss of last year to add in the initial balance of the current year earnings account
            last_day_previous_fy = self.env.user.company_id.compute_fiscalyear_dates(datetime.strptime(self.env.context['date_from_aml'], "%Y-%m-%d"))['date_from'] + timedelta(days=-1)
            unaffected_earnings_results = self.with_context(date_to=last_day_previous_fy.strftime('%Y-%m-%d'), date_from=False).do_query_unaffected_earnings(options, line_id)
            unaffected_earnings_line = False
        context = self.env.context
        base_domain = [('date', '<=', context['date_to']), ('company_id', 'in', context['company_ids'])]
        if context.get('journal_ids'):
            base_domain.append(('journal_id', 'in', context['journal_ids']))
        if context['date_from_aml']:
            base_domain.append(('date', '>=', context['date_from_aml']))
        if context['state'] == 'posted':
            base_domain.append(('move_id.state', '=', 'posted'))
        if context.get('account_tag_ids'):
            base_domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]
        if context.get('analytic_tag_ids'):
            base_domain += ['|', ('analytic_account_id.tag_ids', 'in', context['analytic_tag_ids'].ids), ('analytic_tag_ids', 'in', context['analytic_tag_ids'].ids)]
        if context.get('analytic_account_ids'):
            base_domain += [('analytic_account_id', 'in', context['analytic_account_ids'].ids)]
        for account_id, result in results.items():
            domain = list(base_domain)  # copying the base domain
            domain.append(('account_id', '=', account_id))
            account = self.env['account.account'].browse(account_id)
            accounts[account] = result
            accounts[account]['initial_bal'] = initial_bal_results.get(account.id, {'balance': 0, 'amount_currency': 0, 'debit': 0, 'credit': 0})
            if account.user_type_id.id == self.env.ref('account.data_unaffected_earnings').id and not unaffected_earnings_line:
                #add the benefit/loss of previous fiscal year to the first unaffected earnings account found.
                unaffected_earnings_line = True
                for field in ['balance', 'debit', 'credit']:
                    accounts[account]['initial_bal'][field] += unaffected_earnings_results[field]
                    accounts[account][field] += unaffected_earnings_results[field]
            #use query_get + with statement instead of a search in order to work in cash basis too
            aml_ctx = {}
            if context.get('date_from_aml'):
                aml_ctx = {
                    'strict_range': True,
                    'date_from': context['date_from_aml'],
                }
            aml_ids = self.with_context(**aml_ctx)._do_query(options, account_id, group_by_account=False)
            aml_ids = [x[0] for x in aml_ids]
            accounts[account]['lines'] = self.env['account.move.line'].browse(aml_ids)
        #if the unaffected earnings account wasn't in the selection yet: add it manually
        user_currency = self.env.user.company_id.currency_id
        if not unaffected_earnings_line and not float_is_zero(unaffected_earnings_results['balance'], precision_digits=user_currency.decimal_places):
            #search an unaffected earnings account
            unaffected_earnings_account = self.env['account.account'].search([
                ('user_type_id', '=', self.env.ref('account.data_unaffected_earnings').id), ('company_id', 'in', self.env.context.get('company_ids', []))
            ], limit=1)
            if unaffected_earnings_account and (not line_id or unaffected_earnings_account.id == line_id):
                accounts[unaffected_earnings_account[0]] = unaffected_earnings_results
                accounts[unaffected_earnings_account[0]]['initial_bal'] = unaffected_earnings_results
                accounts[unaffected_earnings_account[0]]['lines'] = []
        return accounts

    def _get_taxes(self, journal):
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        query = """
            SELECT rel.account_tax_id, SUM("account_move_line".balance) AS base_amount
            FROM account_move_line_account_tax_rel rel, """ + tables + """
            WHERE "account_move_line".id = rel.account_move_line_id
                AND """ + where_clause + """
           GROUP BY rel.account_tax_id"""
        self.env.cr.execute(query, where_params)
        ids = []
        base_amounts = {}
        for row in self.env.cr.fetchall():
            ids.append(row[0])
            base_amounts[row[0]] = row[1]

        res = {}
        for tax in self.env['account.tax'].browse(ids):
            self.env.cr.execute('SELECT sum(debit - credit) FROM ' + tables + ' '
                ' WHERE ' + where_clause + ' AND tax_line_id = %s', where_params + [tax.id])
            res[tax] = {
                'base_amount': base_amounts[tax.id],
                'tax_amount': self.env.cr.fetchone()[0] or 0.0,
            }
            if journal.get('type') == 'sale':
                #sales operation are credits
                res[tax]['base_amount'] = res[tax]['base_amount'] * -1
                res[tax]['tax_amount'] = res[tax]['tax_amount'] * -1
        return res

    def _get_journal_total(self):
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        self.env.cr.execute('SELECT COALESCE(SUM(debit), 0) as debit, COALESCE(SUM(credit), 0) as credit, COALESCE(SUM(debit-credit), 0) as balance FROM ' + tables + ' '
                        'WHERE ' + where_clause + ' ', where_params)
        return self.env.cr.dictfetchone()

    @api.model
    def get_lines(self, options, line_id=None):
        lines = []
        context = self.env.context
        company_id = self.env.user.company_id
        dt_from = options['date'].get('date_from')
        line_id = line_id and int(line_id.split('_')[1]) or None
        aml_lines = []
        # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
        grouped_accounts = self.with_context(date_from_aml=dt_from, date_from=dt_from and company_id.compute_fiscalyear_dates(datetime.strptime(dt_from, "%Y-%m-%d"))['date_from'] or None).group_by_account_id(options, line_id)
        sorted_accounts = sorted(grouped_accounts, key=lambda a: a.code)
        unfold_all = context.get('print_mode') and len(options.get('unfolded_lines')) == 0
        for account in sorted_accounts:
            debit = grouped_accounts[account]['debit']
            credit = grouped_accounts[account]['credit']
            balance = grouped_accounts[account]['balance']
            amount_currency = '' if not account.currency_id else self.format_value(grouped_accounts[account]['amount_currency'], currency=account.currency_id)
            lines.append({
                'id': 'account_%s' % (account.id,),
                'name': account.code + " " + account.name,
                'columns': [{'name': v} for v in [amount_currency, self.format_value(debit), self.format_value(credit), self.format_value(balance)]],
                'level': 2,
                'unfoldable': True,
                'unfolded': 'account_%s' % (account.id,) in options.get('unfolded_lines') or unfold_all,
                'colspan': 4,
            })
            if 'account_%s' % (account.id,) in options.get('unfolded_lines') or unfold_all:
                initial_debit = grouped_accounts[account]['initial_bal']['debit']
                initial_credit = grouped_accounts[account]['initial_bal']['credit']
                initial_balance = grouped_accounts[account]['initial_bal']['balance']
                initial_currency = '' if not account.currency_id else self.format_value(grouped_accounts[account]['initial_bal']['amount_currency'], currency=account.currency_id)
                domain_lines = [{
                    'id': 'initial_%s' % (account.id,),
                    'class': 'o_account_reports_initial_balance',
                    'name': _('Initial Balance'),
                    'parent_id': 'account_%s' % (account.id,),
                    'columns': [{'name': v} for v in ['', '', '', initial_currency, self.format_value(initial_debit), self.format_value(initial_credit), self.format_value(initial_balance)]],
                }]
                progress = initial_balance
                amls = amls_all = grouped_accounts[account]['lines']
                too_many = False
                if len(amls) > 80 and not context.get('print_mode'):
                    amls = amls[:80]
                    too_many = True
                used_currency = self.env.user.company_id.currency_id
                for line in amls:
                    if options.get('cash_basis'):
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    line_debit = line.company_id.currency_id.compute(line_debit, used_currency)
                    line_credit = line.company_id.currency_id.compute(line_credit, used_currency)
                    progress = progress + line_debit - line_credit
                    currency = "" if not line.currency_id else self.with_context(no_format=False).format_value(line.amount_currency, currency=line.currency_id)
                    name = []
                    name = line.name and line.name or ''
                    if line.ref:
                        name = name and name + ' - ' + line.ref or line.ref
                    if len(name) > 35 and not self.env.context.get('no_format'):
                        name = name[:32] + "..."
                    partner_name = line.partner_id.name
                    if partner_name and len(partner_name) > 35  and not self.env.context.get('no_format'):
                        partner_name = partner_name[:32] + "..."
                    caret_type = 'account.move'
                    if line.invoice_id:
                        caret_type = 'account.invoice.in' if line.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                    elif line.payment_id:
                        caret_type = 'account.payment'
                    line_value = {
                        'id': line.id,
                        'caret_options': caret_type,
                        'parent_id': 'account_%s' % (account.id,),
                        'name': line.move_id.name if line.move_id.name else '/',
                        'columns': [{'name': v} for v in [format_date(self.env, line.date), name, partner_name, currency,
                                    line_debit != 0 and self.format_value(line_debit) or '',
                                    line_credit != 0 and self.format_value(line_credit) or '',
                                    self.format_value(progress)]],
                        'level': 4,
                    }
                    aml_lines.append(line.id)
                    domain_lines.append(line_value)
                domain_lines.append({
                    'id': 'total_' + str(account.id),
                    'class': 'o_account_reports_domain_total',
                    'parent_id': 'account_%s' % (account.id,),
                    'name': _('Total '),
                    'columns': [{'name': v} for v in ['', '', '', amount_currency, self.format_value(debit), self.format_value(credit), self.format_value(balance)]],
                })
                if too_many:
                    domain_lines.append({
                        'id': 'too_many' + str(account.id),
                        'parent_id': 'account_%s' % (account.id,),
                        'name': _('There are more than 80 items in this list, click here to see all of them'),
                        'colspan': 7,
                        'columns': [{}],
                        'action': 'view_too_many',
                        'action_id': 'account,%s' % (account.id,),
                    })
                lines += domain_lines

        journals = [j for j in options.get('journals') if j.get('selected')]
        if len(journals) == 1 and journals[0].get('type') in ['sale', 'purchase'] and not line_id:
            total = self._get_journal_total()
            lines.append({
                'id': 0,
                'class': 'total',
                'name': _('Total'),
                'columns': [{'name': v} for v in ['', '', '', '', self.format_value(total['debit']), self.format_value(total['credit']), self.format_value(total['balance'])]],
                'level': 1,
                'unfoldable': False,
                'unfolded': False,
            })
            lines.append({
                'id': 0,
                'name': _('Tax Declaration'),
                'columns': [{'name': v} for v in ['', '', '', '', '', '', '']],
                'level': 1,
                'unfoldable': False,
                'unfolded': False,
            })
            lines.append({
                'id': 0,
                'name': _('Name'),
                'columns': [{'name': v} for v in ['', '', '', '', _('Base Amount'), _('Tax Amount'), '']],
                'level': 2,
                'unfoldable': False,
                'unfolded': False,
            })
            for tax, values in self._get_taxes(journals[0]).items():
                lines.append({
                    'id': '%s_tax' % (tax.id,),
                    'name': tax.name + ' (' + str(tax.amount) + ')',
                    'caret_options': 'account.tax',
                    'unfoldable': False,
                    'columns': [{'name': v} for v in ['', '', '', '', values['base_amount'], values['tax_amount'], '']],
                    'level': 4,
                })

        if self.env.context.get('aml_only', False):
            return aml_lines
        return lines

    @api.model
    def get_report_name(self):
        return _("General Ledger")

    def view_all_journal_items(self, options, params):
        if params.get('id'):
            params['id'] = int(params.get('id').split('_')[1])
        return self.env['account.report'].open_journal_items(options, params)
