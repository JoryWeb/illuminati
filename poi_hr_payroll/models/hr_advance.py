from odoo import models, fields, api, _, tools
from datetime import date

class HrAdvanced(models.Model):
    _name = "hr.advance"
    _description = "Adelantados"

    @api.model
    def _get_journal(self):
        config_obj = self.env["hr.advance.config"]
        journal_id = False
        for c in config_obj.search([('active', '=', True)], limit=1):
            journal_id = c.journal_id
        return journal_id

    @api.model
    def _get_account_debit(self):
        config_obj = self.env["hr.advance.config"]
        account_debit = False
        for c in config_obj.search([('active', '=', True)], limit=1):
            account_debit = c.account_debit
        return account_debit

    @api.model
    def _get_account_credit(self):
        config_obj = self.env["hr.advance.config"]
        account_credit = False
        for c in config_obj.search([('active', '=', True)], limit=1):
            account_credit = c.account_credit
        return account_credit

    name = fields.Char('Descripcion', states={'draft': [('readonly', False)]}, required=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Empleado', readonly=True,  required=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', 'Contrato', readonly=True,  states={'draft': [('readonly', False)]}, required=True)


    note = fields.Text('Observaciones', readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float('Monto', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    date = fields.Date('Fecha', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    state = fields.Selection([
        ('draft','Borrador'),
        ('process','En Cola de Proceso'),
        ('cancel','Cancelado'),
        ('done','Realizado')
        ], string='Status', readonly=True, default='draft')
    state_p = fields.Boolean('Descontar en Nomina', readonly=True, default=True, help="Descuento en planilla", states={'draft': [('readonly', False)]})
    finiquito_id = fields.Many2one('hr.finiquito', 'Finiquito', readonly=True, states={'draft': [('readonly', False)]})
    payslip_id = fields.Many2one('hr.payslip', 'Nomina', readonly=True)
    company_id = fields.Many2one('res.company',  string='Compañia', related="employee_id.company_id", store=True, readonly=True)
    code = fields.Char('Codigo', readonly=True,  default="ADE")
    journal_id = fields.Many2one('account.journal', 'Diario Contable', default=_get_journal, readonly=True, states={'draft': [('readonly', False)]})
    account_debit = fields.Many2one('account.account', 'Cuenta Deudora', default=_get_account_debit, domain=[('deprecated', '=', False)], readonly=True, states={'draft': [('readonly', False)]})
    account_credit = fields.Many2one('account.account', 'Cuenta Acreedora', default=_get_account_credit, domain=[('deprecated', '=', False)], readonly=True, states={'draft': [('readonly', False)]})
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica', readonly=True, states={'draft': [('readonly', False)]})
    move_id = fields.Many2one('account.move', 'Asiento Contable', readonly=True)
    force_date = fields.Date('Fecha Forzada', help='Fecha Forzada de Contabilizacion', readonly=True, states={'draft': [('readonly', False)]})
    assess = fields.Boolean('Contabilizar', default=True, readonly=True, states={'draft': [('readonly', False)]})



    @api.onchange('contract_id')
    def _get_analytic_account(self):
        if self.contract_id.analytic_account_id and self.contract_id.analytic_account_id.id:
            self.analytic_account_id = self.contract_id.analytic_account_id.id
        else:
            self.analytic_account_id = False

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id.contract_id:
            self.contract_id = self.employee_id.contract_id.id
        else:
            self.contract_id = False


    @api.multi
    def process_adv(self):
        move_pool = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Payroll')

        for adv in self:
            date = self.date
            if self.force_date:
                date = self.force_date
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            default_partner_id = adv.employee_id.address_home_id.id
            name = _('Adelanto de %s') % (adv.employee_id.name)
            move = {
                'narration': name,
                'date': date,
                'ref': adv.name,
                'journal_id': adv.journal_id.id,
            }


            amt = False and -adv.amount or adv.amount
            if float_is_zero(amt, precision_digits=precision):
                continue
            partner_id = default_partner_id
            debit_account_id = adv.account_debit.id
            credit_account_id = adv.account_credit.id

            if debit_account_id:

                debit_line = (0, 0, {
                    'name': adv.name,
                    'date': date,
                    'partner_id': partner_id or False,
                    'account_id': debit_account_id,
                    'journal_id': adv.journal_id.id,
                    'debit': amt > 0.0 and amt or 0.0,
                    'credit': amt < 0.0 and -amt or 0.0,
                    'analytic_account_id': adv.analytic_account_id and adv.analytic_account_id.id or False,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            if credit_account_id:

                credit_line = (0, 0, {
                    'name': adv.name,
                    'date': date,
                    'partner_id': partner_id or False,
                    'account_id': credit_account_id,
                    'journal_id': adv.journal_id.id,
                    'debit': amt < 0.0 and -amt or 0.0,
                    'credit': amt > 0.0 and amt or 0.0,
                    'analytic_account_id': adv.analytic_account_id and adv.analytic_account_id.id or False,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
            move.update({'line_ids': line_ids})
            move_id = move_pool.create(move)
            self.write({'move_id': move_id.id})
            move_id.post()


    @api.multi
    def cancel_advance(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def hr_process_advance(self):
        if self.assess:
            self.process_adv()
        if not self.state_p:
            self.write({'state': 'process'})
            return self.hr_done_advance()
        return self.write({'state': 'process'})

    @api.multi
    def hr_done_advance(self):
        return self.write({'state': 'done'})

class HrAdvancedConfig(models.Model):
    _name = 'hr.advance.config'
    _description = 'Configuracion Contable Adelantos'
    _order = "date desc"
    _rec_name = "date"

    date = fields.Date('Fecha', default=fields.Date.today(), required=True)
    active = fields.Boolean('Activo', default=False)
    journal_id = fields.Many2one('account.journal', 'Diario Contable')
    account_debit = fields.Many2one('account.account', 'Cuenta Deudora', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Cuenta Acreedora',domain=[('deprecated', '=', False)])


class HrEmployee(models.Model):
    _description = 'Empleado'
    _inherit = 'hr.employee'

    advance_count = fields.Integer(compute="_advance_count", string="Adelantos")

    @api.multi
    def _advance_count(self):
        advance = self.env['hr.advance']
        for s in self:
            s.advance_count = advance.search_count([('employee_id', '=', s.id)])
