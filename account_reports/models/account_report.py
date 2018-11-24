# Part of Odoo. See LICENSE file for full copyright and licensing details.
import calendar
import copy
import json
import io
import logging
import lxml.html

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    # TODO saas-17: remove the try/except to directly import from misc
    import xlsxwriter

from odoo import models, fields, api, _
from datetime import timedelta, datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, pycompat
from babel.dates import get_quarter_names
from odoo.tools.misc import formatLang, format_date
from odoo.tools import config
from odoo.addons.web.controllers.main import clean_action
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class AccountReportManager(models.Model):
    _name = 'account.report.manager'
    _description = 'manage summary and footnotes of reports'

    # must work with multi-company, in case of multi company, no company_id defined
    report_name = fields.Char(required=True, help='name of the model of the report')
    summary = fields.Char()
    footnotes_ids = fields.One2many('account.report.footnote', 'manager_id')
    company_id = fields.Many2one('res.company')
    financial_report_id = fields.Many2one('account.financial.html.report')

    def add_footnote(self, text, line):
        return self.env['account.report.footnote'].create({'line': line, 'text': text, 'manager_id': self.id})

class AccountReportFootnote(models.Model):
    _name = 'account.report.footnote'
    _description = 'Footnote for reports'

    text = fields.Char()
    line = fields.Char(index=True)
    manager_id = fields.Many2one('account.report.manager')

class AccountReport(models.AbstractModel):
    _name = 'account.report'

    filter_date = None
    filter_cash_basis = None
    filter_all_entries = None
    filter_comparison = None
    filter_journals = None
    filter_analytic = None
    filter_unfold_all = None
    filter_hierarchy = None

    def _build_options(self, previous_options=None):
        if not previous_options:
            previous_options = {}
        options = {}
        filter_list = [attr for attr in dir(self) if attr.startswith('filter_') and len(attr) > 7 and not callable(getattr(self, attr))]
        for element in filter_list:
            filter_name = element[7:]
            options[filter_name] = getattr(self, element)

        group_multi_company = self.env['ir.model.data'].xmlid_to_object('base.group_multi_company')
        if self.env.user.id in group_multi_company.users.ids:
            # We have a user with multi-company
            options['multi_company'] = [{'id': c.id, 'name': c.name, 'selected': True if c.id == self.env.user.company_id.id else False} for c in self.env.user.company_ids]
        if options.get('journals'):
            options['journals'] = self.get_journals()

        options['unfolded_lines'] = []
        # Merge old options with default from this report
        for key, value in options.items():
            if key in previous_options and value is not None and previous_options[key] is not None:
                # special case handler for date and comparison as from one report to another, they can have either a date range or single date
                if key == 'date' or key == 'comparison':
                    if key == 'comparison':
                        options[key]['number_period'] = previous_options[key]['number_period']
                    options[key]['filter'] = 'custom'
                    if previous_options[key].get('filter', 'custom') != 'custom':
                        # just copy filter and let the system compute the correct date from it
                        options[key]['filter'] = previous_options[key]['filter']
                    elif value.get('date_from') is not None and not previous_options[key].get('date_from'):
                        company_fiscalyear_dates = self.env.user.company_id.compute_fiscalyear_dates(datetime.strptime(previous_options[key]['date'], DEFAULT_SERVER_DATE_FORMAT))
                        options[key]['date_from'] = company_fiscalyear_dates['date_from'].strftime(DEFAULT_SERVER_DATE_FORMAT)
                        options[key]['date_to'] = previous_options[key]['date']
                    elif value.get('date') is not None and not previous_options[key].get('date'):
                        options[key]['date'] = previous_options[key]['date_to']
                    else:
                        options[key] = previous_options[key]
                else:
                    options[key] = previous_options[key]
        return options

    @api.model
    def get_options(self, previous_options=None):
        # Be sure that user has group analytic if a report tries to display analytic
        if self.filter_analytic:
            self.filter_analytic = self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids and True or None
            self.filter_analytic_tags = [] if self.filter_analytic else None
            self.filter_analytic_accounts = [] if self.filter_analytic else None

        return self._build_options(previous_options)

    #TO BE OVERWRITTEN
    def get_columns_name(self, options):
        return []

    #TO BE OVERWRITTEN
    def get_lines(self, options, line_id=None):
        return []

    #TO BE OVERWRITTEN
    def get_templates(self):
        return {
                'main_template': 'account_reports.main_template',
                'line_template': 'account_reports.line_template',
                'footnotes_template': 'account_reports.footnotes_template',
                'search_template': 'account_reports.search_template',
        }

    #TO BE OVERWRITTEN
    def get_report_name(self):
        return _('General Report')

    def get_report_filename(self, options):
        """The name that will be used for the file when downloading pdf,xlsx,..."""
        return self.get_report_name().lower().replace(' ', '_')

    def execute_action(self, options, params=None):
        action_id = int(params.get('actionId'))
        action = self.env['ir.actions.actions'].browse([action_id])
        action_type = action.type
        action = self.env[action.type].browse([action_id])
        action_read = action.read()[0]
        if action_type == 'ir.actions.client':
            # Check if we are opening another report and if yes, pass options and ignore_session
            if action.tag == 'account_report':
                options['unfolded_lines'] = []
                options['unfold_all'] = False
                another_report_context = safe_eval(action_read['context'])
                another_report = self.browse(another_report_context['id'])
                if not self.date_range and another_report.date_range:
                    # Don't propagate the filter if current report is date based while the targetted
                    # report is date_range based, because the semantic is not the same:
                    # 'End of Following Month' in BS != 'Last Month' in P&L (it has to go from 1st day of fiscalyear)
                    options['date'].pop('filter')
                action_read.update({'options': options, 'ignore_session': 'read'})
        if params.get('id'):
            # Add the id of the account.financial.html.report.line in the action's context
            context = action_read.get('context') and safe_eval(action_read['context']) or {}
            context.setdefault('active_id', int(params['id']))
            action_read['context'] = context
        return action_read

    @api.multi
    def open_document(self, options, params=None):
        if not params:
            params = {}
        ctx = self.env.context.copy()
        ctx.pop('id', '')
        aml_id = params.get('id')
        document = params.get('object', 'account.move')
        if aml_id:
            aml = self.env['account.move.line'].browse(aml_id)
            view_name = 'view_move_form'
            res_id = aml.move_id.id
            if document == 'account.invoice' and aml.invoice_id.id:
                res_id = aml.invoice_id.id
                if aml.invoice_id.type in ('in_refund', 'in_invoice'):
                    view_name = 'invoice_supplier_form'
                elif aml.invoice_id.type in ('out_refund', 'out_invoice'):
                    view_name = 'invoice_form'
            elif document == 'account.payment' and aml.payment_id.id:
                view_name = 'view_account_payment_form'
                res_id = aml.payment_id.id
            view_id = self.env['ir.model.data'].get_object_reference('account', view_name)[1]
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'tree',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'res_model': document,
                'view_id': view_id,
                'res_id': res_id,
                'context': ctx,
            }

    def open_tax(self, options, params=None):
        active_id = int(str(params.get('id')).split('_')[0])
        domain = [('date', '>=', options.get('date').get('date_from')), ('date', '<=', options.get('date').get('date_to')),
                  '|', ('tax_ids', 'in', [active_id]), ('tax_line_id', 'in', [active_id])]
        if not options.get('all_entries'):
            domain.append(('move_id.state', '=', 'posted'))
        action = self.env.ref('account.action_move_line_select_tax_audit').read()[0]
        ctx = self.env.context.copy()
        ctx.update({'active_id': active_id,})
        action = clean_action(action)
        action['domain'] = domain
        action['context'] = ctx
        return action

    def view_too_many(self, options, params=None):
        model, active_id = params.get('actionId').split(',')
        ctx = self.env.context.copy()
        if model == 'account':
            action = self.env.ref('account.action_move_line_select').read()[0]
            ctx.update({
                'search_default_account_id': [int(active_id)],
                'active_id': int(active_id),
                })
        if model == 'partner':
            action = self.env.ref('account.action_move_line_select_by_partner').read()[0]
            ctx.update({
                'search_default_partner_id': [int(active_id)],
                'active_id': int(active_id),
                })
        action = clean_action(action)
        action['context'] = ctx
        return action

    @api.multi
    def open_general_ledger(self, options, params=None):
        if not params:
            params = {}
        ctx = self.env.context.copy()
        ctx.pop('id', '')
        action = self.env.ref('account_reports.action_account_report_general_ledger').read()[0]
        options['unfolded_lines'] = ['account_%s' % (params.get('id', ''),)]
        options['unfold_all'] = False
        ctx.update({'model': 'account.general.ledger'})
        action.update({'options': options, 'context': ctx, 'ignore_session': 'read'})
        return action

    def open_journal_items(self, options, params):
        action = self.env.ref('account.action_move_line_select').read()[0]
        action = clean_action(action)
        ctx = self.env.context.copy()

        if params and 'id' in params:
            active_id = params['id']
            ctx.update({
                    'search_default_account_id': [active_id],
            })
            action['context'] = ctx
        return action

    def reverse(self, values):
        """Utility method used to reverse a list, this method is used during template generation in order to reverse periods for example"""
        if type(values) != list:
            return values
        else:
            inv_values = copy.deepcopy(values)
            inv_values.reverse()
        return inv_values

    def set_context(self, options):
        """This method will set information inside the context based on the options dict as some options need to be in context for the query_get method defined in account_move_line"""
        ctx = self.env.context.copy()
        if options.get('cash_basis'):
            ctx['cash_basis'] = True
        if options.get('date') and options['date'].get('date_from'):
            ctx['date_from'] = options['date']['date_from']
        if options.get('date'):
            ctx['date_to'] = options['date'].get('date_to') or options['date'].get('date')
        if options.get('all_entries') is not None:
            ctx['state'] = options.get('all_entries') and 'all' or 'posted'
        if options.get('journals'):
            ctx['journal_ids'] = [j.get('id') for j in options.get('journals') if j.get('selected')]
        company_ids = []
        if options.get('multi_company'):
            company_ids = [c.get('id') for c in options['multi_company'] if c.get('selected')]
            company_ids = company_ids if len(company_ids) > 0 else [c.get('id') for c in options['multi_company']]
        ctx['company_ids'] = len(company_ids) > 0 and company_ids or [self.env.user.company_id.id]
        if options.get('analytic_accounts'):
            ctx['analytic_account_ids'] = self.env['account.analytic.account'].browse([int(acc) for acc in options['analytic_accounts']])
        if options.get('analytic_tags'):
            ctx['analytic_tag_ids'] = self.env['account.analytic.tag'].browse([int(t) for t in options['analytic_tags']])
        return ctx

    @api.multi
    def get_report_informations(self, options):
        '''
        return a dictionary of informations that will be needed by the js widget, manager_id, footnotes, html of report and searchview, ...
        '''
        options = self.get_options(options)
        # apply date and date_comparison filter
        options = self.apply_date_filter(options)
        options = self.apply_cmp_filter(options)

        searchview_dict = {'options': options, 'context': self.env.context}
        # Check if report needs analytic
        if options.get('analytic') is not None:
            searchview_dict['analytic_accounts'] = self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids and [(t.id, t.name) for t in self.env['account.analytic.account'].search([])] or False
            searchview_dict['analytic_tags'] = self.env.user.id in self.env.ref('analytic.group_analytic_accounting').users.ids and [(t.id, t.name) for t in self.env['account.analytic.tag'].search([])] or False
        report_manager = self.get_report_manager(options)
        info = {'options': options,
                'context': self.env.context,
                'report_manager_id': report_manager.id,
                'footnotes': [{'id': f.id, 'line': f.line, 'text': f.text} for f in report_manager.footnotes_ids],
                'buttons': self.get_reports_buttons(),
                'main_html': self.get_html(options),
                'searchview_html': self.env['ir.ui.view'].render_template(self.get_templates().get('search_template', 'account_report.search_template'), values=searchview_dict),
                }
        return info

    def create_hierarchy(self, lines):
        """This method is called when the option 'hiearchy' is enabled on a report.
        It receives the lines (as computed by get_lines()) in argument, and will add
        a hiearchy in those lines by using the account.group of accounts. If not set,
        it will fallback on creating a hierarchy based on the account's code first 3
        digits.
        """
        AccountAccount = self.env['account.account']
        hierarchy_list = {}
        current_position = 0

        for line in lines:
            columns = line.get('columns', [{}])
            is_grouped_by_account = line.get('caret_options') == 'account.account'
            account_id = AccountAccount.browse(line.get('id')) if is_grouped_by_account else AccountAccount
            group_id = account_id.group_id
            if group_id:
                group_prefix = group_id.code_prefix
                group_name = group_id.name
                group_key = group_id
            else:
                group_name = ''
                group_prefix = account_id.code and account_id.code[0:3] or False
                group_key = group_prefix

            current_group_level = line.get('caret_options') == 'account.account' and 4 or line.get('level', 4)
            while group_key:
                #create hierarchy leaves if needed
                if group_key not in hierarchy_list:
                    current_group_level -= 1
                    hierarchy_list[group_key] = {
                        'position': (current_position, current_group_level),  # will be used to insert at the good place
                        'values': {
                            'id': 'hierarchy_%s_%s' % (current_position, current_group_level),
                            'name': '%s %s' % (group_prefix, group_name) if group_prefix else group_name,
                            'unfoldable': False,
                            'unfolded': True,
                            'parent_id': line.get('parent_id'),  # to make these fold when the original parent gets folded
                            'level': current_group_level,
                            'columns': [0 for l in range(len(columns))],
                        }
                    }

                #sum line values in hierarchy leaves
                hierarchy_list[group_key]['values']['columns'] = [sum(x) for x in pycompat.izip(hierarchy_list[group_key]['values']['columns'], [c['no_format_name'] for c in columns])]

                #loop on
                if account_id.group_id:
                    group_key = group_key.parent_id
                    group_prefix = group_key.code_prefix
                    group_name = group_key.name
                else:
                    group_prefix = group_prefix[:-1]
                    group_name = ''
                    group_key = group_prefix

            #count the number of lines passed
            current_position += 1

        #build the final list that will be return
        already_inserted = 0
        for key in sorted(hierarchy_list, key=lambda x:hierarchy_list[x]['position']):
            value = hierarchy_list[key]
            value['values']['columns'] = [{'name': self.format_value(v)} for v in value['values']['columns']]
            lines.insert(value['position'][0] + already_inserted, value['values'])
            already_inserted += 1
        return lines

    @api.multi
    def get_html(self, options, line_id=None, additional_context=None):
        '''
        return the html value of report, or html value of unfolded line
        * if line_id is set, the template used will be the line_template
        otherwise it uses the main_template. Reason is for efficiency, when unfolding a line in the report
        we don't want to reload all lines, just get the one we unfolded.
        '''
        templates = self.get_templates()
        report_manager = self.get_report_manager(options)
        report = {'name': self.get_report_name(),
                'summary': report_manager.summary,
                'company_name': self.env.user.company_id.name,}
        lines = self.with_context(self.set_context(options)).get_lines(options, line_id=line_id)

        if options.get('hierarchy'):
            lines = self.create_hierarchy(lines)

        footnotes_to_render = []
        if self.env.context.get('print_mode', False):
            # we are in print mode, so compute footnote number and include them in lines values, otherwise, let the js compute the number correctly as
            # we don't know all the visible lines.
            footnotes = dict([(str(f.line), f) for f in report_manager.footnotes_ids])
            number = 0
            for line in lines:
                f = footnotes.get(str(line.get('id')))
                if f:
                    number += 1
                    line['footnote'] = str(number)
                    footnotes_to_render.append({'id': f.id, 'number': number, 'text': f.text})

        rcontext = {'report': report,
                    'lines': {'columns_header': self.get_columns_name(options), 'lines': lines},
                    'options': options,
                    'context': self.env.context,
                    'model': self,
                }
        if additional_context and type(additional_context) == dict:
            rcontext.update(additional_context)
        render_template = templates.get('main_template', 'account_reports.main_template')
        if line_id is not None:
            render_template = templates.get('line_template', 'account_reports.line_template')
        html = self.env['ir.ui.view'].render_template(
            render_template,
            values=dict(rcontext),
        )
        if self.env.context.get('print_mode', False):
            for k,v in self.replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>', self.get_html_footnotes(footnotes_to_render))
        return html

    @api.multi
    def get_html_footnotes(self, footnotes):
        template = self.get_templates().get('footnotes_template', 'account_reports.footnotes_template')
        rcontext = {'footnotes': footnotes, 'context': self.env.context}
        html = self.env['ir.ui.view'].render_template(template, values=dict(rcontext))
        return html

    def get_reports_buttons(self):
        return [{'name': _('Print Preview'), 'action': 'print_pdf'}, {'name': _('Export (XLSX)'), 'action': 'print_xlsx'}]

    def get_report_manager(self, options):
        domain = [('report_name', '=', self._name)]
        domain = (domain + [('financial_report_id', '=', self.id)]) if 'id' in dir(self) else domain
        selected_companies = []
        if options.get('multi_company'):
            selected_companies = [c['id'] for c in options['multi_company'] if c.get('selected')]
        if len(selected_companies) == 1:
            domain += [('company_id', '=', selected_companies[0])]
        existing_manager = self.env['account.report.manager'].search(domain, limit=1)
        if not existing_manager:
            existing_manager = self.env['account.report.manager'].create({'report_name': self._name, 'company_id': selected_companies and selected_companies[0] or False, 'financial_report_id': self.id if 'id' in dir(self) else False})
        return existing_manager

    def _get_filter_journals(self):
        return self.env['account.journal'].search([('company_id', 'in', self.env.user.company_ids.ids or [self.env.user.company_id.id])], order="company_id, name")

    def get_journals(self):
        journals_read = self._get_filter_journals()
        journals = []
        previous_company = False
        for c in journals_read:
            if c.company_id != previous_company:
                journals.append({'id': 'divider', 'name': c.company_id.name})
                previous_company = c.company_id
            journals.append({'id': c.id, 'name': c.name, 'code': c.code, 'type': c.type, 'selected': False})
        return journals

    def format_value(self, value, currency=False):
        if self.env.context.get('no_format'):
            return value
        currency_id = currency or self.env.user.company_id.currency_id
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
            value = abs(value)
        res = formatLang(self.env, value, currency_obj=currency_id)
        return res

    def format_date(self, dt_to, dt_from, options, dt_filter='date'):
        # previously get_full_date_names
        options_filter = options[dt_filter].get('filter', '')
        if isinstance(dt_to, pycompat.string_types):
            dt_to = datetime.strptime(dt_to, DEFAULT_SERVER_DATE_FORMAT)
        if dt_from and isinstance(dt_from, pycompat.string_types):
            dt_from = datetime.strptime(dt_from, DEFAULT_SERVER_DATE_FORMAT)
        if 'month' in options_filter:
            return format_date(self.env, dt_to.strftime(DEFAULT_SERVER_DATE_FORMAT), date_format='MMM YYYY')
        if 'quarter' in options_filter:
            quarter = (dt_to.month - 1) // 3 + 1
            return ('%s %s') % (get_quarter_names('abbreviated', locale=self._context.get('lang') or 'en_US')[quarter], dt_to.year)
        if 'year' in options_filter:
            if self.env.user.company_id.fiscalyear_last_day == 31 and self.env.user.company_id.fiscalyear_last_month == 12:
                return dt_to.strftime('%Y')
            else:
                return '%s - %s' % ((dt_to.year - 1), dt_to.year)
        if not dt_from:
            return _('As of %s') % (format_date(self.env, dt_to.strftime(DEFAULT_SERVER_DATE_FORMAT)),)
        return _('From %s <br/> to  %s') % (format_date(self.env, dt_from.strftime(DEFAULT_SERVER_DATE_FORMAT)), format_date(self.env, dt_to.strftime(DEFAULT_SERVER_DATE_FORMAT)))

    def apply_date_filter(self, options):
        if not options.get('date'):
            return options
        options_filter = options['date'].get('filter')
        if not options_filter:
            return options
        today = date.today()
        dt_from = options['date'].get('date_from') is not None and today or False
        if options_filter == 'custom':
            dt_from = options['date'].get('date_from', False)
            dt_to = options['date'].get('date_to', False) or options['date'].get('date', False)
            options['date']['string'] = self.format_date(dt_to, dt_from, options)
            return options
        if options_filter == 'today':
            company_fiscalyear_dates = self.env.user.company_id.compute_fiscalyear_dates(datetime.now())
            dt_from = dt_from and company_fiscalyear_dates['date_from'] or False
            dt_to = today
        elif options_filter == 'this_month':
            dt_from = dt_from and today.replace(day=1) or False
            dt_to = (today.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        elif options_filter == 'this_quarter':
            quarter = (today.month - 1) // 3 + 1
            dt_to = (today.replace(month=quarter * 3, day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            dt_from = dt_from and dt_to.replace(day=1, month=dt_to.month - 2, year=dt_to.year) or False
        elif options_filter == 'this_year':
            company_fiscalyear_dates = self.env.user.company_id.compute_fiscalyear_dates(datetime.now())
            dt_from = dt_from and company_fiscalyear_dates['date_from'] or False
            dt_to = company_fiscalyear_dates['date_to']
        elif options_filter == 'last_month':
            dt_to = today.replace(day=1) - timedelta(days=1)
            dt_from = dt_from and dt_to.replace(day=1) or False
        elif options_filter == 'last_quarter':
            quarter = (today.month - 1) // 3 + 1
            quarter = quarter - 1 if quarter > 1 else 4
            dt_to = (today.replace(month=quarter * 3, day=1, year=today.year if quarter != 4 else today.year - 1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            dt_from = dt_from and dt_to.replace(day=1, month=dt_to.month - 2, year=dt_to.year) or False
        elif options_filter == 'last_year':
            company_fiscalyear_dates = self.env.user.company_id.compute_fiscalyear_dates(datetime.now().replace(year=today.year - 1))
            dt_from = dt_from and company_fiscalyear_dates['date_from'] or False
            dt_to = company_fiscalyear_dates['date_to']
        if dt_from:
            options['date']['date_from'] = dt_from.strftime(DEFAULT_SERVER_DATE_FORMAT)
            options['date']['date_to'] = dt_to.strftime(DEFAULT_SERVER_DATE_FORMAT)
        else:
            options['date']['date'] = dt_to.strftime(DEFAULT_SERVER_DATE_FORMAT)
        options['date']['string'] = self.format_date(dt_to, dt_from, options)
        return options

    def apply_cmp_filter(self, options):
        if not options.get('comparison'):
            return options
        options['comparison']['periods'] = []
        cmp_filter = options['comparison'].get('filter')
        if not cmp_filter:
            return options
        if cmp_filter == 'no_comparison':
            if options['comparison'].get('date_from') != None:
                options['comparison']['date_from'] = ""
                options['comparison']['date_to'] = ""
            else:
                options['comparison']['date'] = ""
            options['comparison']['string'] = _('No comparison')
            return options
        elif cmp_filter == 'custom':
            date_from = options['comparison'].get('date_from')
            date_to = options['comparison'].get('date_to') or options['comparison'].get('date')
            display_value = self.format_date(date_to, date_from, options, dt_filter='comparison')
            if date_from:
                vals = {'date_from': date_from, 'date_to': date_to, 'string': display_value}
            else:
                vals = {'date': date_to, 'string': display_value}
            options['comparison']['periods'] = [vals]
            return options
        else:
            dt_from = False
            options_filter = options['date'].get('filter','')
            if options['date'].get('date_from'):
                dt_from = datetime.strptime(options['date'].get('date_from'), "%Y-%m-%d")
            dt_to = options['date'].get('date_to') or options['date'].get('date')
            dt_to = datetime.strptime(dt_to, "%Y-%m-%d")
            display_value = False
            for index in range(0, options['comparison'].get('number_period', 1)):
                if cmp_filter == 'same_last_year' or options_filter in ('this_year', 'last_year'):
                    ly = lambda d: d - timedelta(days=366 if calendar.isleap(d.year) else 365)
                    if dt_from:
                        dt_from = ly(dt_from)
                    dt_to = ly(dt_to)
                elif cmp_filter == 'previous_period':
                    if options_filter in ('this_month', 'last_month', 'today'):
                        dt_from = dt_from and (dt_from - timedelta(days=1)).replace(day=1) or dt_from
                        dt_to = dt_to.replace(day=1) - timedelta(days=1)
                    elif options_filter in ('this_quarter', 'last_quarter'):
                        dt_to = dt_to.replace(month=(dt_to.month + 10) % 12, day=1) - timedelta(days=1)
                        dt_from = dt_from and dt_from.replace(month=dt_to.month - 2, year=dt_to.year) or dt_from
                    elif options_filter == 'custom':
                        if not dt_from:
                            dt_to = dt_to.replace(day=1) - timedelta(days=1)
                        else:
                            previous_dt_to = dt_to
                            dt_to = dt_from - timedelta(days=1)
                            dt_from = dt_from - timedelta(days=(previous_dt_to - dt_from).days + 1)
                display_value = self.format_date(dt_to, dt_from, options)

                if dt_from:
                    vals = {'date_from': dt_from.strftime(DEFAULT_SERVER_DATE_FORMAT), 'date_to': dt_to.strftime(DEFAULT_SERVER_DATE_FORMAT), 'string': display_value}
                else:
                    vals = {'date': dt_to.strftime(DEFAULT_SERVER_DATE_FORMAT), 'string': display_value}
                options['comparison']['periods'].append(vals)
        if len(options['comparison'].get('periods', [])) > 0:
            for k, v in options['comparison']['periods'][0].items():
                if k in ('date', 'date_from', 'date_to', 'string'):
                    options['comparison'][k] = v
        return options

    def print_pdf(self, options):
        return {
                'type': 'ir_actions_account_report_download',
                'data': {'model': self.env.context.get('model'),
                         'options': json.dumps(options),
                         'output_format': 'pdf',
                         'financial_id': self.env.context.get('id'),
                         }
                }

    def replace_class(self):
        """When printing pdf, we sometime want to remove/add/replace class for the report to look a bit different on paper
        this method is used for this, it will replace occurence of value key by the dict value in the generated pdf
        """
        return {b'o_account_reports_no_print': b'', b'table-responsive': b'', b'<a': b'<span', b'</a>': b'</span>'}

    def get_pdf(self, options, minimal_layout=True):
        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.user.company_id,
        }

        body = self.env['ir.ui.view'].render_template(
            "account_reports.print_template",
            values=dict(rcontext),
        )
        body_html = self.with_context(print_mode=True).get_html(options)

        body = body.replace(b'<body class="o_account_reports_body_print">', b'<body class="o_account_reports_body_print">' + body_html)
        if minimal_layout:
            header = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
            footer = ''
            spec_paperformat_args = {'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            header = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=header))
        else:
            rcontext.update({
                    'css': '',
                    'o': self.env.user,
                    'res_company': self.env.user.company_id,
                })
            header = self.env['ir.actions.report'].render_template("web.external_layout", values=rcontext)
            header = header.decode('utf-8') # Ensure that headers and footer are correctly encoded
            spec_paperformat_args = {}
            # parse header as new header contains header, body and footer
            try:
                root = lxml.html.fromstring(header)
                match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

                for node in root.xpath(match_klass.format('header')):
                    headers = lxml.html.tostring(node)
                    headers = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=headers))

                for node in root.xpath(match_klass.format('footer')):
                    footer = lxml.html.tostring(node)
                    footer = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=footer))

            except lxml.etree.XMLSyntaxError:
                headers = header
                footer = ''
            header = headers

        landscape = False
        if len(self.with_context(print_mode=True).get_columns_name(options)) > 5:
            landscape = True

        return self.env['ir.actions.report']._run_wkhtmltopdf(
            [body],
            header=header, footer=footer,
            landscape=landscape,
            specific_paperformat_args=spec_paperformat_args
        )

    def print_xlsx(self, options):
        return {
                'type': 'ir_actions_account_report_download',
                'data': {'model': self.env.context.get('model'),
                         'options': json.dumps(options),
                         'output_format': 'xlsx',
                         'financial_id': self.env.context.get('id'),
                         }
                }

    def get_xlsx(self, options, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self.get_report_name()[:31])

        def_style = workbook.add_format({'font_name': 'Arial'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'pattern': 1, 'font_color': '#FFFFFF'})
        level_0_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'left': 2, 'pattern': 1, 'font_color': '#FFFFFF'})
        level_0_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'right': 2, 'pattern': 1, 'font_color': '#FFFFFF'})
        level_1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2})
        level_1_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'left': 2})
        level_1_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'right': 2})
        level_2_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2})
        level_2_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2, 'left': 2})
        level_2_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2, 'right': 2})
        level_3_style = def_style
        level_3_style_left = workbook.add_format({'font_name': 'Arial', 'left': 2})
        level_3_style_right = workbook.add_format({'font_name': 'Arial', 'right': 2})
        domain_style = workbook.add_format({'font_name': 'Arial', 'italic': True})
        domain_style_left = workbook.add_format({'font_name': 'Arial', 'italic': True, 'left': 2})
        domain_style_right = workbook.add_format({'font_name': 'Arial', 'italic': True, 'right': 2})
        upper_line_style = workbook.add_format({'font_name': 'Arial', 'top': 2})

        sheet.set_column(0, 0, 15) #  Set the first column width to 15

        sheet.write(0, 0, '', title_style)

        y_offset = 0
        # if self.get_report_obj().get_name() == 'coa' and self.get_special_date_line_names():
        #     sheet.write(y_offset, 0, '', title_style)
        #     sheet.write(y_offset, 1, '', title_style)
        #     x = 2
        #     for column in self.with_context(is_xls=True).get_special_date_line_names():
        #         sheet.write(y_offset, x, column, title_style)
        #         sheet.write(y_offset, x+1, '', title_style)
        #         x += 2
        #     sheet.write(y_offset, x, '', title_style)
        #     y_offset += 1

        x = 0
        for column in self.get_columns_name(options):
            sheet.write(y_offset, x, column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' '), title_style)
            x += 1
        y_offset += 1
        ctx = self.set_context(options)
        ctx.update({'no_format':True, 'print_mode':True})
        lines = self.with_context(ctx).get_lines(options)

        if options.get('hierarchy'):
            lines = self.create_hierarchy(lines)

        if lines:
            max_width = max([len(l['columns']) for l in lines])

        for y in range(0, len(lines)):
            if lines[y].get('level') == 0:
                for x in range(0, len(lines[y]['columns']) + 1):
                    sheet.write(y + y_offset, x, None, upper_line_style)
                y_offset += 1
                style_left = level_0_style_left
                style_right = level_0_style_right
                style = level_0_style
            elif lines[y].get('level') == 1:
                for x in range(0, len(lines[y]['columns']) + 1):
                    sheet.write(y + y_offset, x, None, upper_line_style)
                y_offset += 1
                style_left = level_1_style_left
                style_right = level_1_style_right
                style = level_1_style
            elif lines[y].get('level') == 2:
                style_left = level_2_style_left
                style_right = level_2_style_right
                style = level_2_style
            elif lines[y].get('level') == 3:
                style_left = level_3_style_left
                style_right = level_3_style_right
                style = level_3_style
            # elif lines[y].get('type') != 'line':
            #     style_left = domain_style_left
            #     style_right = domain_style_right
            #     style = domain_style
            else:
                style = def_style
                style_left = def_style
                style_right = def_style
            sheet.write(y + y_offset, 0, lines[y]['name'], style_left)
            for x in range(1, max_width - len(lines[y]['columns']) + 1):
                sheet.write(y + y_offset, x, None, style)
            for x in range(1, len(lines[y]['columns']) + 1):
                # if isinstance(lines[y]['columns'][x - 1], tuple):
                    # lines[y]['columns'][x - 1] = lines[y]['columns'][x - 1][0]
                if x < len(lines[y]['columns']):
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, lines[y]['columns'][x - 1].get('name', ''), style)
                else:
                    sheet.write(y + y_offset, x + lines[y].get('colspan', 1) - 1, lines[y]['columns'][x - 1].get('name', ''), style_right)
            if 'total' in lines[y].get('class', '') or lines[y].get('level') == 0:
                for x in range(len(lines[0]['columns']) + 1):
                    sheet.write(y + 1 + y_offset, x, None, upper_line_style)
                y_offset += 1
        if lines:
            for x in range(max_width + 1):
                sheet.write(len(lines) + y_offset, x, None, upper_line_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def print_xml(self, options):
        return {
                'type': 'ir_actions_account_report_download',
                'data': {'model': self.env.context.get('model'),
                         'options': json.dumps(options),
                         'output_format': 'xml',
                         'financial_id': self.env.context.get('id'),
                         }
                }

    def get_xml(self, options):
        return False

    def print_txt(self, options):
        return {
                'type': 'ir_actions_account_report_download',
                'data': {'model': self.env.context.get('model'),
                         'options': json.dumps(options),
                         'output_format': 'txt',
                         'financial_id': self.env.context.get('id'),
                         }
                }

    def get_txt(self, options):
        return False
