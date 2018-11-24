
from odoo import models, fields, api, exceptions, _
import time


class WizardSelectMoveTemplate(models.TransientModel):
    _name = "wizard.select.move.template"

    @api.one
    @api.depends('template_id')
    def _compute_has_percentage(self):
        percentage = False
        for line in self.template_id.template_line_ids:
            if line.type == "percentage":
                percentage = True
                break
        self.has_percentage = percentage

    @api.one
    @api.depends('line_ids')
    def _compute_has_input_lines(self):
        if self.line_ids:
            self.has_input_lines = True
        else:
            self.has_input_lines = False

    @api.one
    @api.depends('computed_line_ids')
    def _compute_has_computed_lines(self):
        if self.computed_line_ids:
            self.has_computed_lines = True
        else:
            self.has_computed_lines = False


    template_id = fields.Many2one(comodel_name='account.move.template', string='Move Template', required=True)
    partner_id = fields.Many2one(comodel_name='res.partner',string='Partner')
    has_percentage = fields.Boolean("Has Percentage Line", compute=_compute_has_percentage)
    amount_to_apply = fields.Float("Amount to apply on percentage")
    has_input_lines = fields.Boolean("Has input lines", compute=_compute_has_input_lines)
    line_ids = fields.One2many(comodel_name='wizard.select.move.template.line',inverse_name='template_id',string='Lines')
    has_computed_lines = fields.Boolean("Has computed lines", compute=_compute_has_computed_lines)
    computed_line_ids = fields.One2many(comodel_name='wizard.computed.move.template.line',inverse_name='template_id',string='Computed Lines')
    state = fields.Selection([('template_selected', 'Template selected')],string='State')

    @api.onchange('amount_to_apply')
    def onchange_amount_to_apply(self):
        for line in self.computed_line_ids:
            if line.template_line_id.type == 'percentage':
                line.amount = self.amount_to_apply * line.template_line_id.percentage_value / 100

    @api.onchange('line_ids')
    def onchange_line_ids(self):
        input_lines = {}
        for template_line in self.line_ids:
            input_lines[template_line.sequence] = template_line.amount
        for computed_line in self.computed_line_ids:
            if computed_line.template_line_id.type != 'computed':
                input_lines[computed_line.sequence] = computed_line.amount

        computed_lines = self.template_id.compute_lines(input_lines)
        for line in self.computed_line_ids:
            if line.template_line_id.type == 'computed':
                line.amount = computed_lines[line.sequence]


    @api.multi
    def check_zero_lines(self):
        if not self.line_ids:
            return True
        for template_line in self.line_ids:
            if template_line.amount:
                return True
        return False

    @api.multi
    def load_lines(self):
        self.ensure_one()
        template = self.template_id
        for line in template.template_line_ids:
            if line.type == 'input':
                self.env['wizard.select.move.template.line'].create({
                    'template_id': self.id,
                    'sequence': line.sequence,
                    'name': line.name,
                    'amount': 0.0,
                    'account_id': line.account_id.id,
                    'move_line_type': line.move_line_type,
                    'template_line_id': line.id,
                })
            elif line.type == 'fixed':
                self.env['wizard.computed.move.template.line'].create({
                    'template_id': self.id,
                    'sequence': line.sequence,
                    'name': line.name,
                    'amount': line.fixed_amount,
                    'account_id': line.account_id.id,
                    'move_line_type': line.move_line_type,
                    'template_line_id': line.id,
                })
            else:
                self.env['wizard.computed.move.template.line'].create({
                    'template_id': self.id,
                    'sequence': line.sequence,
                    'name': line.name,
                    'amount': 0.0,
                    'account_id': line.account_id.id,
                    'move_line_type': line.move_line_type,
                    'template_line_id': line.id,
                })

        #Disabled for a while... We need to be computed when percentage is present
        #if not self.line_ids:
        #    return self.load_template()
        self.state = 'template_selected'

        view_rec = self.env['ir.model.data'].get_object_reference('poi_account_move_template', 'wizard_select_template')
        view_id = view_rec and view_rec[1] or False

        return {
            'view_type': 'form',
            'view_id': [view_id],
            'view_mode': 'form',
            'res_model': 'wizard.select.move.template',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def load_template(self):
        self.ensure_one()

        if not self.check_zero_lines():
            raise exceptions.Warning(
                _('At least one amount has to be non-zero!')
            )
        input_lines = {}
        for template_line in self.line_ids:
            input_lines[template_line.sequence] = template_line.amount
        for computed_line in self.computed_line_ids:
            input_lines[computed_line.sequence] = computed_line.amount

        #computed_lines = self.template_id.compute_lines(input_lines)
        computed_lines = input_lines # Let's not compute here

        move = self._make_move()

        moves = {}
        for line in self.template_id.template_line_ids:
            self._make_move_line(line, computed_lines, move,self.partner_id.id)

        if self.template_id.autopost:
            move.post()

        return {
            'domain': "[('id','=', " + str(move.id) + ")]",
            'name': 'Entries',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.multi
    def _make_move(self):
        self.ensure_one()
        move = self.env['account.move'].create({'ref': self.template_id.name,
                                                'journal_id': self.template_id.journal_id.id,
                                                'partner_id': self.partner_id.id,
                                                })
        return move

    @api.model
    def _make_move_line(self, line, computed_lines, move, partner_id):

        ctx = self.env.context.copy()
        ctx['check_move_validity'] = False

        account_move_line_model = self.env['account.move.line']
        analytic_account_id = False
        if line.analytic_account_id:
            analytic_account_id = line.analytic_account_id.id
        vals = {
            'name': line.name,
            'move_id': move.id,
            'journal_id': move.journal_id.id,
            'analytic_account_id': analytic_account_id,
            'account_id': line.account_id.id,
            'date': time.strftime('%Y-%m-%d'),
            'credit': 0.0,
            'debit': 0.0,
            'partner_id': partner_id,
        }
        if line.move_line_type == 'cr':
            vals['credit'] = computed_lines[line.sequence]
        if line.move_line_type == 'dr':
            vals['debit'] = computed_lines[line.sequence]
        id_line = account_move_line_model.with_context(ctx).create(vals)
        return id_line


class WizardSelectMoveTemplateLine(models.TransientModel):
    _description = 'Template Lines'
    _name = "wizard.select.move.template.line"

    template_id = fields.Many2one(comodel_name='wizard.select.move.template',string='Wizard Template')
    template_line_id = fields.Many2one(comodel_name='account.move.template.line', string='Template Line')
    sequence = fields.Integer(string='Number', required=True)
    name = fields.Char(required=True, readonly=True)
    account_id = fields.Many2one(comodel_name='account.account',string='Account',required=True,readonly=True)
    move_line_type = fields.Selection([('cr', 'Credit'), ('dr', 'Debit')],string='Move Line Type',required=True,readonly=True)
    amount = fields.Float(required=True)


class WizardComputedMoveTemplateLine(models.TransientModel):
    _description = 'Computed Template Lines'
    _name = "wizard.computed.move.template.line"

    template_id = fields.Many2one(comodel_name='wizard.select.move.template',string='Wizard Template')
    template_line_id = fields.Many2one(comodel_name='account.move.template.line',string='Template Line')
    sequence = fields.Integer(string='Number', required=True)
    name = fields.Char(required=True, readonly=True)
    account_id = fields.Many2one(comodel_name='account.account',string='Account',required=True,readonly=True)
    move_line_type = fields.Selection([('cr', 'Credit'), ('dr', 'Debit')],string='Move Line Type',required=True,readonly=True)
    amount = fields.Float(required=True, readonly=True)