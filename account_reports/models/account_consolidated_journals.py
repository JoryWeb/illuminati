# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _


class report_account_consolidated_journal(models.AbstractModel):
    _name = "account.consolidated.journal"
    _description = "Consolidated Journals Report"
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_year'}
    filter_all_entries = False
    filter_journals = True
    filter_unfold_all = False

    @api.model
    def get_options(self, previous_options=None):
        options = super(report_account_consolidated_journal, self).get_options(previous_options=previous_options)
        # We do not want multi company for this report
        if options.get('multi_company'):
            options.pop('multi_company')
        return options

    def get_report_name(self):
        return _("Consolidated Journals")

    def get_columns_name(self, options):
        columns = [{'name': _('Journal Name (Code)')}, {'name': _('Debit'), 'class': 'number'}, {'name': _('Credit'), 'class': 'number'}, {'name': _('Balance'), 'class': 'number'}]
        return columns

    def get_sum(self, value, field, results):
        sum_debit = self.format_value(sum([int(r['debit']) for r in results if r[field] == value]))
        sum_credit = self.format_value(sum([int(r['credit']) for r in results if r[field] == value]))
        sum_balance = self.format_value(sum([int(r['balance']) for r in results if r[field] == value]))
        return [sum_debit, sum_credit, sum_balance]

    def get_total(self, current_journal, results):
        return {
                'id': 'total_%s' % (current_journal,),
                'name': _('Total'),
                'class': 'o_account_reports_domain_total',
                'columns': [{'name': v} for v in self.get_sum(current_journal, 'journal_id', results)],
                'parent_id': current_journal,
            }

    def get_main_line(self, options, current_journal, results, record):
        return {
                'id': current_journal,
                'name': '%s (%s)' % (record['name'], record['code']),
                'level': 2,
                'columns': [{'name': n} for n in self.get_sum(current_journal, 'journal_id', results)],
                'unfoldable': True,
                'unfolded': True if current_journal in options.get('unfolded_lines') else False,
            }

    def get_line_total_per_month(self, options, current_company, results):
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        lines = []
        lines.append({
                    'id': 'Total_all_%s' % (current_company),
                    'name': _('Total'),
                    'class': 'total',
                    'level': 1,
                    'columns': [{'name': n} for n in self.get_sum(current_company, 'company_id', results)]
        })
        # get range of date for company_id
        dates = []
        for record in results:
            date = '%s-%s' % (record['yyyy'], record['month'])
            if date not in dates:
                dates.append(date)
        if dates:
            lines.append({'id': 'Detail_%s' % (current_company),
                        'name': _('Details per month'),
                        'level': 1,
                        'columns': [{},{},{}]
                        })
            for date in sorted(dates):
                year, month = date.split('-')
                sum_debit = self.format_value(sum([int(r['debit']) for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]))
                sum_credit = self.format_value(sum([int(r['credit']) for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]))
                sum_balance = self.format_value(sum([int(r['balance']) for r in results if (r['month'] == month and r['yyyy'] == year) and r['company_id'] == current_company]))
                vals = {
                        'id': 'Total_month_%s_%s' % (date, current_company),
                        'name': convert_date('%s-01' % (date), {'format': 'MMM YYYY'}),
                        'level': 2,
                        'columns': [{'name': v} for v in [sum_debit, sum_credit, sum_balance]]
                }
                lines.append(vals)
        return lines

    @api.model
    def get_lines(self, options, line_id=None):
        lines = []
        convert_date = self.env['ir.qweb.field.date'].value_to_html
        select = """SELECT to_char("account_move_line".date, 'MM') as month, to_char("account_move_line".date, 'YYYY') as yyyy,
                COALESCE(SUM("account_move_line".balance), 0) as balance,
               COALESCE(SUM("account_move_line".debit), 0) as debit,
               COALESCE(SUM("account_move_line".credit), 0) as credit,
               j.id as journal_id, j.name, j.code, j.company_id FROM %s, account_journal j, res_company c WHERE %s AND "account_move_line".journal_id = j.id
               GROUP BY month, yyyy, j.id, j.company_id order by j.id, yyyy, month, j.company_id
        """
        tables, where_clause, where_params = self.env['account.move.line'].with_context(strict_range=True)._query_get()
        if line_id:
            where_clause += ' AND j.id = %s'
            where_params += [str(line_id)]
        select = select % (tables, where_clause)
        self.env.cr.execute(select, where_params)
        results = self.env.cr.dictfetchall()
        if not results:
            return lines
        current_journal = results[0]['journal_id']
        lines.append(self.get_main_line(options, current_journal, results, results[0]))
        for values in results:
            if values['journal_id'] != current_journal:
                # We are on a new journal, so add a total line before that and create a new line unfoldable for the next journal
                if (current_journal in options.get('unfolded_lines')):
                    lines.append(self.get_total(current_journal, results))
                current_journal = values['journal_id']
                lines.append(self.get_main_line(options, current_journal, results, values))
            # If we need to unfold the line
            if (values['journal_id'] in options.get('unfolded_lines')):
                vals = {
                    'id': 'journal_%s_%s_%s' % (values['journal_id'],values['month'],values['yyyy']),
                    'name': convert_date('%s-%s-01' % (values['yyyy'], values['month']), {'format': 'MMM YYYY'}),
                    'caret_options': True,
                    'level': 4,
                    'parent_id': values['journal_id'],
                    'columns': [{'name': n} for n in [self.format_value(values['debit']), self.format_value(values['credit']), self.format_value(values['balance'])]],
                }
                lines.append(vals)
        if (values['journal_id'] in options.get('unfolded_lines')):
            lines.append(self.get_total(current_journal, results))
        if not line_id:
            lines.extend(self.get_line_total_per_month(options, values['company_id'], results))
        return lines
