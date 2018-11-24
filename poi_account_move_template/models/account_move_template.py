
import functools
import re
from odoo import models, fields, api, _, exceptions
from odoo.tools.safe_eval import safe_eval



class AccountMoveTemplate(models.Model):
    _name = 'account.move.template'
    _description = 'Account Move Template'

    @api.model
    def _company_get(self):
        return self.env['res.company']._company_default_get(object='account.move.template')

    name = fields.Char(required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, change_default=True,
                                 default=_company_get, )
    template_line_ids = fields.One2many(comodel_name='account.move.template.line', inverse_name='template_id',
                                        string='Template Lines')
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    autopost = fields.Boolean("Post Generated Asset")

    #FUNCTIONS

    @api.multi
    def _input_lines(self):
        count = 0
        for line in self.template_line_ids:
            if line.type != 'computed':
                count += 1
        return count

    @api.multi
    def _get_template_line(self, line_number):
        for line in self.template_line_ids:
            if line.sequence == line_number:
                return line
        return False

    @api.multi
    def _generate_empty_lines(self):
        lines = {}
        for line in self.template_line_ids:
            lines[line.sequence] = None
        return lines

    @api.multi
    def lines(self, line_number, computed_lines=None):
        if computed_lines is None:
            computed_lines = {}
        if computed_lines[line_number] is not None:
            return computed_lines[line_number]
        line = self._get_template_line(line_number)
        if re.match(r'L\( *' + str(line_number) + r' *\)', line.python_code):
            raise exceptions.Warning(
                _('Line %s can\'t refer to itself') % str(line_number)
            )
        try:
            recurse_lines = functools.partial(self.lines, computed_lines=computed_lines)
            computed_lines[line_number] = safe_eval(
                line.python_code.replace('L', 'recurse_lines'),
                locals_dict={'recurse_lines': recurse_lines}
            )
        except KeyError:
            raise exceptions.Warning(
                _('Code "%s" refers to non existing line') % line.python_code)
        return computed_lines[line_number]

    @api.multi
    def compute_lines(self, input_lines):
        # input_lines: dictionary in the form {line_number: line_amount}
        # returns all the lines (included input lines)
        # in the form {line_number: line_amount}
        if len(input_lines) != self._input_lines():
            raise exceptions.Warning(
                _('Inconsistency between input lines and '
                  'filled lines for template %s') % self.name
            )
        computed_lines = self._generate_empty_lines()
        computed_lines.update(input_lines)
        for line_number in computed_lines:
            computed_lines[line_number] = self.lines(
                line_number, computed_lines)
        return computed_lines


class AccountMoveTemplateLine(models.Model):
    _name = 'account.move.template.line'
    _description = 'Account Move Template Line'

    name = fields.Char(required=True)
    sequence = fields.Integer(string='Sequence', required=True)
    type = fields.Selection([('computed', 'Computed'),
                             ('input', 'User input'),
                             ('fixed', 'Fixed Value'),
                             ('percentage', 'Percentage')], string='Type', required=True,
                            default='input')
    percentage_value = fields.Float("Percentage Value")
    fixed_amount = fields.Float("Fixed Amount")
    python_code = fields.Text(string='Python Code')
    account_id = fields.Many2one(comodel_name='account.account', string='Account', required=True, ondelete="cascade")
    move_line_type = fields.Selection([('cr', 'Credit'), ('dr', 'Debit')], string='Move Line Type', required=True)
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account',
                                          ondelete="cascade")
    template_id = fields.Many2one(comodel_name='account.move.template', string='Template')

    _sql_constraints = [
        ('sequence_template_uniq', 'unique (template_id,sequence)',
         'The sequence of the line must be unique per template !')
    ]
