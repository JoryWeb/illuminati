# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.osv import expression

def split_list(a_list):
    half = len(a_list)/2
    return a_list[:half], a_list[half:]

class ReportAccountFinancialReport(models.Model):
    _name = "account.financial.html.report"
    _description = "Account Report"

    name = fields.Char(translate=True)
    debit_credit = fields.Boolean('Show Credit and Debit Columns')
    line_ids = fields.One2many('account.financial.html.report.line', 'financial_report_id', string='Lines')
    report_type = fields.Selection([('date_range', 'Based on date ranges'),
                                    ('date_range_extended', "Based on date ranges with 'older' and 'total' columns and last 3 months"),
                                    ('no_date_range', 'Based on a single date'),
                                    ('date_range_cash', 'Bases on date ranges and cash basis method')],
                                   string='Analysis Periods', default=False, required=True,
                                   help='For report like the balance sheet that do not work with date ranges')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self._context.get('company_id', self.env.user.company_id))
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id, required=True)
    second_currency_id = fields.Many2one('res.currency', string='Second Currency')
    menuitem_created = fields.Boolean("Menu Has Been Created", default=False)
    parent_id = fields.Many2one('ir.ui.menu', 'Menu Padre')
    client_action_id = fields.Many2one('ir.actions.client', 'Client Action', ondelete='cascade')
    menu_id = fields.Many2one('ir.ui.menu', 'Menu', ondelete='cascade')

    display_segments = fields.Boolean("Display Segments Filter")
    display_analytic = fields.Boolean("Display Analytic Filter")
    display_analytic_tags = fields.Boolean("Display Analytic Tags")

    @api.one
    def create_action_and_menu(self):
        """
            This function will create the action client and the menu.
        """
        if not self.menuitem_created:
            client_action = self.env['ir.actions.client'].create({
                'name': self.get_title(),
                'tag': 'account_report_generic',
                'context': {
                    'url': '/poi_account_reports/output_format/financial_report/' + str(self.id),
                    'model': 'account.financial.html.report',
                    'id': self.id,
                },
            })
            menu = self.env['ir.ui.menu'].create({
                'name': self.get_title(),
                'parent_id': self.parent_id and self.parent_id.id or self.env['ir.model.data'].xmlid_to_res_id('account.menu_finance_reports'),
                'action': 'ir.actions.client,%s' % (client_action.id,),
            })
            self.write({'menuitem_created': True,
                        'menu_id': menu.id,
                        'client_action_id': client_action.id})

    @api.multi
    def get_lines(self, context_id, line_id=None):
        if isinstance(context_id, int):
            context_id = self.env['account.financial.html.report.context'].browse(context_id)
        line_obj = self.line_ids
        if line_id:
            line_obj = self.env['account.financial.html.report.line'].search([('id', '=', line_id)])
        if context_id.comparison:
            line_obj = line_obj.with_context(periods=context_id.get_cmp_periods())
        used_currency = self.env.user.company_id.currency_id
        linesDicts = [{} for _ in context_id.get_periods()]
        res = line_obj.with_context(
            state=context_id.all_entries and 'all' or 'posted',
            all_accounts = context_id.all_accounts,
            cash_basis=self.report_type == 'date_range_cash' or context_id.cash_basis,
            strict_range=self.report_type == 'date_range_extended',
            aged_balance=self.report_type == 'date_range_extended',
            company_ids=context_id.company_ids.ids,
            segment_ids=context_id.segment_ids.ids,
            analytic_ids=context_id.analytic_ids.ids,
            analytic_tag_ids=context_id.analytic_tag_ids.ids,
            context=context_id,
            display_segments=self.display_segments,
            display_analytic=self.display_analytic,
            display_analytic_tags=self.display_analytic_tags
        ).get_lines(self, context_id, linesDicts)
        return res

    def get_title(self):
        return self.name

    def get_name(self):
        return 'financial_report'

    @api.multi
    def get_report_type(self):
        return self.report_type

    def get_template(self):
        return 'poi_account_reports.report_financial'


class AccountFinancialReportLine(models.Model):
    _name = "account.financial.html.report.line"
    _description = "Account Report Line"
    _order = "sequence"

    name = fields.Char('Section Name', translate=True)
    code = fields.Char('Code')
    financial_report_id = fields.Many2one('account.financial.html.report', 'Financial Report')
    parent_id = fields.Many2one('account.financial.html.report.line', string='Parent')
    children_ids = fields.One2many('account.financial.html.report.line', 'parent_id', string='Children')
    sequence = fields.Integer()

    domain = fields.Char(default=None)
    formulas = fields.Char()
    groupby = fields.Char("Group by", default=False)
    figure_type = fields.Selection([('float', 'Float'), ('percents', 'Percents'), ('no_unit', 'No Unit')],
                                   'Type', default='float', required=True)
    green_on_positive = fields.Boolean('Is growth good when positive', default=True)
    level = fields.Integer(required=True)
    special_date_changer = fields.Selection([('from_beginning', 'From the beginning'), ('to_beginning_of_period', 'At the beginning of the period'), ('normal', 'Use given dates'), ('strict_range', 'Force given dates for all accounts and account types')], default='normal')
    show_domain = fields.Selection([('always', 'Always'), ('never', 'Never'), ('foldable', 'Foldable')], default='foldable')
    hide_if_zero = fields.Boolean(default=False)
    action_id = fields.Many2one('ir.actions.actions')

    @api.multi
    def report_move_lines_action(self):
        #Esta funcion busca las líneas de movimiento... al parecer
        domain = safe_eval(self.domain)
        if 'date_from' in self.env.context.get('context', {}):
            if self.env.context['context'].get('date_from'):
                domain = expression.AND([domain, [('date', '>=', self.env.context['context']['date_from'])]])
            if self.env.context['context'].get('date_to'):
                domain = expression.AND([domain, [('date', '<=', self.env.context['context']['date_to'])]])
            if self.env.context['context'].get('state', 'all') == 'posted':
                domain = expression.AND([domain, [('move_id.state', '=', 'posted')]])
            if self.env.context['context'].get('company_ids'):
                domain = expression.AND([domain, [('company_id', 'in', self.env.context['context']['company_ids'])]])

            #ANALYTICS
            if self.env.context['context'].get('analytic_ids'):
                domain = expression.AND([domain, [('analytic_account_id', 'in', self.env.context['context']['analytic_ids'])]])
            if self.env.context['context'].get('segment_ids'):
                domain = expression.AND([domain, [('segment_id', 'in', self.env.context['context']['segment_ids'])]])
            if self.env.context['context'].get('analytic_tag_ids'):
                domain = expression.AND([domain, [('segment_id', 'in', self.env.context['context']['segment_ids'])]])
        return {'type': 'ir.actions.act_window',
                'name': 'Journal Items (%s)' % self.name,
                'res_model': 'account.move.line',
                'view_mode': 'tree,form',
                'domain': domain,
                }

    @api.one
    @api.constrains('groupby')
    def _check_same_journal(self):
        if self.groupby and self.groupby not in self.env['account.move.line']._columns:
            raise ValidationError("Groupby should be a journal item field")

    def _get_sum(self, field_names=None):

        ### THIS FUNCTION GETS ALL THE CHILD TAGS
        def get_tag_child_ids(tag_ids):
            tag_obj = self.env['account.analytic.tag']
            res = []
            for atag in tag_obj.browse(tag_ids):
                if atag.child_ids:
                    for ctag in atag.child_ids:
                        res.append(ctag.id)
                        res += get_tag_child_ids([ctag.id])
                else:
                    res.append(atag.id)
            return res

        ''' Returns the sum of the amls in the domain '''
        if not field_names:
            field_names = ['debit', 'credit', 'balance', 'amount_residual']
        res = dict((fn, 0.0) for fn in field_names)
        if self.domain:
            line_domain = safe_eval(self.domain)
            if self.env.context.get('analytic_ids'):
                line_domain = expression.AND([line_domain,[('analytic_account_id','in', self.env.context.get('analytic_ids'))]])

            if self.env.context.get('segment_ids'):
                line_domain = expression.AND([line_domain,[('segment_id','in', self.env.context.get('segment_ids'))]])

            if self.env.context.get('analytic_tag_ids'):
                atag_ids = get_tag_child_ids(self.env.context.get('analytic_tag_ids'))
                analytic_account_ids = self.env['account.analytic.account'].search([('tag_ids','in',atag_ids)])
                if analytic_account_ids:
                    line_domain = expression.AND([line_domain,[('analytic_account_id','in', analytic_account_ids.ids)]])

            amls = self.env['account.move.line'].search(line_domain)

            compute = amls._compute_fields(field_names, group_by=self.groupby)
            for aml in amls:
                if compute.get(aml.id):
                    for field in field_names:
                        res[field] += compute[aml.id][field]
        return res

    @api.one
    def get_balance(self, linesDict, field_names=None):
        if not field_names:
            field_names = ['debit', 'credit', 'balance']
        res = dict((fn, 0.0) for fn in field_names)
        c = FormulaContext(self.env['account.financial.html.report.line'], linesDict, self)
        if self.formulas:
            for f in self.formulas.split(';'):
                [field, formula] = f.split('=')
                field = field.strip()
                if field in field_names:
                    try:
                        res[field] = safe_eval(formula, c, nocopy=True)
                    except ValueError as err:
                        if 'division by zero' in err.args[0]:
                            res[field] = 0
                        else:
                            raise err
        return res

    def _format(self, value, currency_id=False):
        if self.env.context.get('no_format'):
            return value
        if self.figure_type == 'float':
            if not currency_id:
                currency_id = self.env.user.company_id.currency_id
            if currency_id.is_zero(value):
                # don't print -0.0 in reports
                value = abs(value)
            return formatLang(self.env, value, currency_obj=currency_id)
        if self.figure_type == 'percents':
            return str(round(value * 100, 1)) + '%'
        return round(value, 1)

    def _get_gb_name(self, gb_id):
        if self.groupby == 'account_id':
            return self.env['account.account'].browse(gb_id).name_get()[0][1]
        if self.groupby == 'user_type_id':
            return self.env['account.account.type'].browse(gb_id).name
        if self.groupby == 'partner_id':
            return self.env['res.partner'].browse(gb_id).name
        if self.groupby == 'analytic_account_id':
            return self.env['account.analytic.account'].browse(gb_id).display_name
        if self.groupby == 'segment_id':
            return self.env['account.segment'].browse(gb_id).display_name
        return str(gb_id)

    def _build_cmp(self, balance, comp):
        if comp != 0:
            res = round((balance - comp) / comp * 100, 1)
            if (res > 0) != self.green_on_positive:
                return (str(res) + '%', 'color: red;')
            else:
                return (str(res) + '%', 'color: green;')
        else:
            return 'n/a'

    def _split_formulas(self):
        result = {}
        if self.formulas:
            for f in self.formulas.split(';'):
                [column, formula] = f.split('=')
                column = column.strip()
                result.update({column: formula})
        return result

    def _eval_formula(self, financial_report, debit_credit, context, linesDict):

        # First approach... Let's add the currency here:
        currency_id = financial_report.currency_id or False
        second_currency_id = financial_report.second_currency_id or False
        if currency_id:
            principal_rate = currency_id.rate / self.env.user.company_id.currency_id.rate
        else:
            raise ValidationError(_('The principal currency is not set'))
        if second_currency_id:
            second_rate = second_currency_id.rate / self.env.user.company_id.currency_id.rate


        debit_credit = debit_credit and financial_report.debit_credit
        formulas = self._split_formulas()
        if self.code and self.code in linesDict:
            res = linesDict[self.code]
        else:
            res = FormulaLine(self, linesDict=linesDict)
        vals = {}
        vals['balance'] = res.balance * principal_rate

        if second_currency_id:
            vals['second_balance'] = res.balance * second_rate

        if debit_credit:
            vals['credit'] = res.credit * principal_rate
            vals['debit'] = res.debit * principal_rate

        if second_currency_id and debit_credit:
            vals['second_credit'] = res.credit * second_rate
            vals['second_debit'] = res.debit * second_rate

        results = {}
        if self.domain and self.groupby and self.show_domain != 'never':
            aml_obj = self.env['account.move.line']
            tables, where_clause, where_params = aml_obj._query_get(domain=self.domain)
            params = []

            if self.env.context.get('analytic_ids'):
                analytics_text = ""
                for cai in self.env.context.get('analytic_ids'):
                    if analytics_text == "":
                        analytics_text = str(cai)
                    else:
                        analytics_text += "," + str(cai)
                where_clause += " AND account_move_line.analytic_account_id IN (%s)" % analytics_text

            if self.env.context.get('segment_ids'):
                segments_text = ""
                for csi in self.env.context.get('segment_ids'):
                    if segments_text == "":
                        segments_text = str(csi)
                    else:
                        segments_text += "," + str(csi)
                where_clause += " AND segment_id IN (%s)" % segments_text

            groupby = self.groupby or 'id'
            select = ',COALESCE(SUM(\"account_move_line\".debit-\"account_move_line\".credit), 0),SUM(\"account_move_line\".amount_residual)'
            if financial_report.debit_credit and debit_credit:
                select += ',SUM(\"account_move_line\".debit),SUM(\"account_move_line\".credit)'
            if self.env.context.get('cash_basis'):
                select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
            sql = "SELECT \"account_move_line\"." + groupby + select + " FROM " + tables + " WHERE " + where_clause + " GROUP BY \"account_move_line\".company_currency_id,\"account_move_line\"." + groupby

            params += where_params
            self.env.cr.execute(sql, params)
            results = self.env.cr.fetchall()
            if not second_currency_id:
                if financial_report.debit_credit and debit_credit:
                    results = dict([(k[0], {'balance': k[1] * principal_rate, 'amount_residual': k[2] * principal_rate, 'debit': k[3] * principal_rate, 'credit': k[4] * principal_rate}) for k in results])
                else:
                    results = dict([(k[0], {'balance': k[1] * principal_rate, 'amount_residual': k[2] * principal_rate}) for k in results])
            else:
                if financial_report.debit_credit and debit_credit:
                    results = dict([(k[0], {'balance': k[1] * principal_rate,
                                            'amount_residual': k[2] * principal_rate,
                                            'debit': k[3] * principal_rate,
                                            'credit': k[4] * principal_rate,
                                            'second_balance': k[1] * second_rate,
                                            'second_amount_residual': k[2] * second_rate,
                                            'second_debit': k[3] * second_rate,
                                            'second_credit': k[4] * second_rate
                                            }) for k in results])
                else:
                    results = dict([(k[0], {'balance': k[1] * principal_rate,
                                            'amount_residual': k[2] * principal_rate,
                                            'second_balance': k[1] * second_rate,
                                            'second_amount_residual': k[2] * second_rate,
                                            }) for k in results])

            #TODO ADD results dict for accounts with no.... data

            c = FormulaContext(self.env['account.financial.html.report.line'], linesDict, only_sum=True)
            if formulas:
                for key in results:
                    c['sum'] = FormulaLine(results[key], type='not_computed')
                    c['sum_if_pos'] = FormulaLine(results[key]['balance'] >= 0.0 and results[key] or {'balance': 0.0}, type='not_computed')
                    c['sum_if_neg'] = FormulaLine(results[key]['balance'] <= 0.0 and results[key] or {'balance': 0.0}, type='not_computed')
                    for col, formula in formulas.items():
                        if col in results[key]:
                            results[key][col] = safe_eval(formula, c, nocopy=True)
            if not context.all_accounts:
                to_del = []
                for key in results:
                    if self.env.user.company_id.currency_id.is_zero(results[key]['balance']):
                        to_del.append(key)
                for key in to_del:
                    del results[key]

        results.update({'line': vals})
        return results

    def _put_columns_together(self, data, domain_ids):
        res = dict((domain_id, []) for domain_id in domain_ids)
        for period in data:
            debit_credit = False
            if 'debit' in period['line']:
                debit_credit = True
            for domain_id in domain_ids:
                if debit_credit:
                    res[domain_id].append(period.get(domain_id, {'debit': 0})['debit'])
                    res[domain_id].append(period.get(domain_id, {'credit': 0})['credit'])
                res[domain_id].append(period.get(domain_id, {'balance': 0})['balance'])
        if self.env.context.get('context').report_id.second_currency_id:
            for period in data:
                debit_credit = False
                if 'debit' in period['line']:
                    debit_credit = True
                for domain_id in domain_ids:
                    if debit_credit:
                        res[domain_id].append(period.get(domain_id, {'second_debit': 0})['second_debit'])
                        res[domain_id].append(period.get(domain_id, {'second_credit': 0})['second_credit'])
                    res[domain_id].append(period.get(domain_id, {'second_balance': 0})['second_balance'])
        return res

    def _divide_line(self, line):
        line1 = {
            'id': line['id'],
            'name': line['name'],
            'type': 'line',
            'level': line['level'],
            'footnotes': line['footnotes'],
            'columns': [''] * len(line['columns']),
            'unfoldable': line['unfoldable'],
            'unfolded': line['unfolded'],
        }
        line2 = {
            'id': line['id'],
            'name': _('Total') + ' ' + line['name'],
            'type': 'total',
            'level': line['level'] + 1,
            'footnotes': self.env.context['context']._get_footnotes('total', line['id']),
            'columns': line['columns'],
            'unfoldable': False,
        }
        return [line1, line2]

    def _resolve_line(self, line):
        line1 = {
            'id': line['id'],
            'name': line['name'],
            'type': 'line',
            'level': line['level'],
            'footnotes': line['footnotes'],
            'columns': line['columns'],
            'unfoldable': line['unfoldable'],
            'unfolded': line['unfolded'],
        }
        return line1

    @api.multi
    def get_lines(self, financial_report, context, linesDicts):
        # Esta función grafica todo, en teoría debe dar todo ordenado
        # First approach... Let's add the currency here:
        currency_id = financial_report.currency_id or False
        second_currency_id = financial_report.second_currency_id or False
        if currency_id:
            principal_rate = currency_id.rate / self.env.user.company_id.currency_id.rate
        else:
            raise ValidationError(_('The principal currency is not set'))
        if second_currency_id:
            second_rate = second_currency_id.rate / self.env.user.company_id.currency_id.rate

        final_result_table = []
        comparison_table = context.get_periods()
        # build comparison table

        for line in self:
            res = []
            debit_credit = len(comparison_table) == 1
            domain_ids = {'line'}
            k = 0
            for period in comparison_table:
                period_from = period[0]
                period_to = period[1]
                strict_range = False
                if line.special_date_changer == 'from_beginning':
                    period_from = False
                if line.special_date_changer == 'to_beginning_of_period':
                    date_tmp = datetime.strptime(period[0], "%Y-%m-%d") - relativedelta(days=1)
                    period_to = date_tmp.strftime('%Y-%m-%d')
                    period_from = False
                if line.special_date_changer == 'strict_range':
                    strict_range = True
                r = line.with_context(date_from=period_from, date_to=period_to, strict_range=strict_range)._eval_formula(financial_report, debit_credit, context, linesDicts[k])
                debit_credit = False
                res.append(r)
                domain_ids.update(set(r.keys()))
                k += 1

            res = self._put_columns_together(res, domain_ids)
            if line.hide_if_zero and sum([k == 0 and [True] or [] for k in res['line']], []):
                continue

            # Post-processing ; creating line dictionary, building comparison, computing total for extended, formatting
            vals = {
                'id': line.id,
                'name': line.name,
                'type': 'line',
                'level': line.level,
                'footnotes': context._get_footnotes('line', line.id),
                'columns': res['line'],
                'unfoldable': len(domain_ids) > 1 and line.show_domain != 'always',
                'unfolded': line in context.unfolded_lines or line.show_domain == 'always',
            }
            if line.action_id:
                vals['action_id'] = line.action_id.id
            domain_ids.remove('line')
            lines = [vals]
            groupby = line.groupby or 'aml'
            if line in context.unfolded_lines or line.show_domain == 'always':
                if line.groupby == 'partner_id' or line.groupby == 'account_id':
                    domain_ids = sorted(list(domain_ids), key=lambda k: line._get_gb_name(k))
                for domain_id in domain_ids:
                    name = line._get_gb_name(domain_id)
                    vals = {
                        'id': domain_id,
                        'name': name and len(name) >= 45 and name[0:40] + '...' or name,
                        'level': 1,
                        'type': groupby,
                        'footnotes': context._get_footnotes(groupby, domain_id),
                        'columns': res[domain_id],
                    }
                    lines.append(vals)
                if domain_ids:
                    lines.append({
                        'id': line.id,
                        'name': _('Total') + ' ' + line.name,
                        'type': 'o_account_reports_domain_total',
                        'level': 1,
                        'footnotes': context._get_footnotes('o_account_reports_domain_total', line.id),
                        'columns': list(lines[0]['columns']),
                    })

            for vals in lines:
                if financial_report.report_type == 'date_range_extended':
                    vals['columns'].append(sum(vals['columns']))
                if len(comparison_table) == 2:
                    vals['columns'].append(line._build_cmp(vals['columns'][0], vals['columns'][1]))
                    for i in [0, 1]:
                        vals['columns'][i] = line._format(vals['columns'][i], currency_id)
                else:
                    if not second_currency_id:
                        vals['columns'] = map(line._format, vals['columns'], currency_id)
                    else:
                        principal_columns, secondary_columns = split_list(vals['columns'])
                        principal_columns = [line._format(x, currency_id) for x in principal_columns]
                        secondary_columns = [line._format(x, second_currency_id) for x in secondary_columns]
                        vals['columns'] = principal_columns + secondary_columns

                if not line.formulas:
                    vals['columns'] = ['' for k in vals['columns']]

            if len(lines) == 1:
                new_lines = line.children_ids.get_lines(financial_report, context, linesDicts)
                if new_lines and line.level > 0 and line.formulas:
                    #divided_lines = self._divide_line(lines[0])
                    #result = [divided_lines[0]] + new_lines + [divided_lines[1]]
                    result = [self._resolve_line(lines[0])] + new_lines
                else:
                    result = []
                    if line.level > 0:
                        result += lines
                    result += new_lines
                    if line.level <= 0:
                        result = lines + result #Here we are trying to put level 0 on top
            else:
                result = lines
            final_result_table += result

        return final_result_table


class AccountFinancialReportXMLExport(models.AbstractModel):
    _name = "account.financial.html.report.xml.export"
    _description = "All the xml exports available for the financial reports"

    @api.model
    def is_xml_export_available(self, report_obj):
        return False

    def check(self, report_name, report_id=None):
        return True

    def do_xml_export(self, context_id):
        return ''


class FormulaLine(object):
    def __init__(self, obj, type='balance', linesDict=None):
        if linesDict is None:
            linesDict = {}

        fields = dict((fn, 0.0) for fn in ['debit', 'credit', 'balance'])
        if type == 'balance':
            fields = obj.get_balance(linesDict)[0]
            linesDict[obj.code] = self
        elif type in ['sum', 'sum_if_pos', 'sum_if_neg']:
            if type == 'sum_if_neg':
                obj = obj.with_context(sum_if_neg=True)
            if type == 'sum_if_pos':
                obj = obj.with_context(sum_if_pos=True)
            if obj._name == 'account.financial.html.report.line':
                fields = obj._get_sum()
                self.amount_residual = fields['amount_residual']
            elif obj._name == 'account.move.line':
                self.amount_residual = 0.0
                field_names = ['debit', 'credit', 'balance', 'amount_residual']
                res = obj._compute_fields(field_names)
                if res.get(obj.id):
                    for field in field_names:
                        fields[field] = res[obj.id][field]
                    self.amount_residual = fields['amount_residual']
        elif type == 'not_computed':
            for field in fields:
                fields[field] = obj.get(field, 0)
            self.amount_residual = obj.get('amount_residual', 0)
        elif type == 'null':
            self.amount_residual = 0.0

        if type not in ('not_computed','null'):
            alt_obj = obj
            while alt_obj.parent_id:
                alt_obj = alt_obj.parent_id

        #NOTE FOR FUTURE DEVELOPMENTS: We couldn't add currencies here because some formulas are not related to report.
        #So we don't know which of them are in right currency... This will only handle base_currency...
        #Let's evaluate to put the conversion on other function
        self.balance = fields['balance']
        self.credit = fields['credit']
        self.debit = fields['debit']

class FormulaContext(dict):
    def __init__(self, reportLineObj, linesDict, curObj=None, only_sum=False, *data):
        self.reportLineObj = reportLineObj
        self.curObj = curObj
        self.linesDict = linesDict
        self.only_sum = only_sum
        return super(FormulaContext, self).__init__(data)

    def __getitem__(self, item):
        if self.only_sum and item not in ['sum', 'sum_if_pos', 'sum_if_neg']:
            return FormulaLine(self.curObj, type='null')
        if self.get(item):
            return super(FormulaContext, self).__getitem__(item)
        if self.linesDict.get(item):
            return self.linesDict[item]
        if item == 'sum':
            res = FormulaLine(self.curObj, type='sum')
            self['sum'] = res
            return res
        if item == 'sum_if_pos':
            res = FormulaLine(self.curObj, type='sum_if_pos')
            self['sum_if_pos'] = res
            return res
        if item == 'sum_if_neg':
            res = FormulaLine(self.curObj, type='sum_if_neg')
            self['sum_if_neg'] = res
            return res
        if item == 'NDays':
            d1 = datetime.strptime(self.curObj.env.context['date_from'], "%Y-%m-%d")
            d2 = datetime.strptime(self.curObj.env.context['date_to'], "%Y-%m-%d")
            res = (d2 - d1).days
            self['NDays'] = res
            return res
        line_id = self.reportLineObj.search([('code', '=', item)], limit=1)
        if line_id:
            res = FormulaLine(line_id, linesDict=self.linesDict)
            self.linesDict[item] = res
            return res
        return super(FormulaContext, self).__getitem__(item)


class AccountFinancialReportContext(models.TransientModel):
    _name = "account.financial.html.report.context"
    _description = "A particular context for a financial report"
    _inherit = "account.report.context.common"

    def get_report_obj(self):
        return self.report_id

    fold_field = 'unfolded_lines'
    report_id = fields.Many2one('account.financial.html.report', 'Linked financial report', help='Only if financial report')
    unfolded_lines = fields.Many2many('account.financial.html.report.line', 'context_to_line', string='Unfolded lines')

    @api.model
    def create(self, vals):
        force_fy = False
        if 'force_fy' in vals:
            del vals['force_fy']
            force_fy = True
        res = super(AccountFinancialReportContext, self).create(vals)
        if force_fy:
            dates = self.env.user.company_id.compute_fiscalyear_dates(datetime.today())
            res.write({
                'date_from': dates['date_from'],
                'date_to': dates['date_to'],
                'date_filter': 'this_year'
            })
        return res

    def get_balance_date(self):
        if self.report_id.report_type == 'no_date_range':
            return self.get_full_date_names(self.date_to)
        return self.get_full_date_names(self.date_to, self.date_from)

    def get_columns_names(self):
        columns = []
        if self.report_id.report_type == 'date_range_extended':
            columns += [_('Non-issued')]
        if self.report_id.debit_credit and not self.comparison:
            columns += [_('Debit'), _('Credit')]
        columns += [self.get_balance_date()]
        if self.comparison:
            if self.periods_number == 1 or self.date_filter_cmp == 'custom':
                columns += [self.get_cmp_date(), '%']
            else:
                columns += self.get_cmp_periods(display=True)
        if self.report_id.report_type == 'date_range_extended':
            columns += [_('Older'), _('Total')]
        if self.report_id.second_currency_id:
            sum_columns = []

            actual_columns = columns
            # 1st. Let's update the current columns with Currency
            for act_col in actual_columns:
                act_col = act_col + " (%s)" % self.report_id.currency_id.symbol
                sum_columns.append(act_col)

            new_columns = columns
            # 2nd. Let's create the new columns for new currencies
            for new_col in new_columns:
                new_col = new_col + " (%s)" % self.report_id.second_currency_id.symbol
                sum_columns.append(new_col)
            columns = sum_columns

        return columns

    @api.multi
    def get_columns_types(self):
        types = []
        if self.report_id.report_type == 'date_range_extended':
            types += ['number']
        if self.report_id.debit_credit and not self.comparison:
            types += ['number', 'number']
        types += ['number']
        if self.comparison:
            if self.periods_number == 1 or self.date_filter_cmp == 'custom':
                types += ['number', 'number']
            else:
                types += (['number'] * self.periods_number)
        if self.report_id.report_type == 'date_range_extended':
            types += ['number', 'number']

        #Si tiene 2 monedas, duplicamos todo
        if self.report_id.second_currency_id:
            types = types + types

        return types