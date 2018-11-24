from odoo import models, fields, api, _, tools
import odoo.addons.decimal_precision as dp
from datetime import date
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    @api.depends('line_ids')
    def _get_rciva(self):
        for s in self:
            for line in s.details_by_salary_rule_category:
                if line.code == 'RCIVA_T':
                    s.rciva = line.amount

    @api.multi
    @api.depends('input_line_ids', 'line_ids')
    def _get_form110(self):
        for s in self:
            for input in s.input_line_ids:
                if input.code == 'F110':
                    s.credit_form110 = input.amount


    @api.multi
    def _compute_ufv(self):
        currency_ids = self.env['res.currency'].search([('name', '=', 'UF2')], limit=1)
        if currency_ids:
            currency_id = currency_ids[0]
            rate_ids = self.env['res.currency.rate'].search([('currency_id', '=', currency_id.id)], limit=2, order="name asc")
            for s in self:
                if rate_ids:
                    self.previous_ufv = rate_ids[0].rate
                    self.current_ufv = rate_ids[1].rate

    @api.multi
    @api.depends('employee_id')
    def _get_saldo(self):
        for s in self:
            if s.employee_id:
                s.saldo = s.employee_id.saldo_rciva


    saldo = fields.Float('Saldo Mes Anterior', readonly=True, compute="_get_saldo", store=True, default=0, states={'draft': [('readonly', False)]})
    saldo_next_month = fields.Float('Saldo Siguiente Mes',  readonly=True, default=0, states={'draft': [('readonly', False)]})
    current_saldo = fields.Float('Saldo Actual', readonly=True, default=0, states={'draft': [('readonly', False)]})
    credit_form110 = fields.Float('Credito Fiscal Form.110', readonly=True, compute="_get_form110", default=0, states={'draft': [('readonly', False)]})
    rciva = fields.Float('Rc-Iva',  readonly=True, compute="_get_rciva", store=True, default=0, states={'draft': [('readonly', False)]})
    rciva_current = fields.Float('Impuesto del Periodo',  readonly=True,  default=0, states={'draft': [('readonly', False)]})
    previous_ufv = fields.Float('UFV Anterior',  readonly=True, compute="_compute_ufv", digits=dp.get_precision('UFV HR'))
    current_ufv = fields.Float('UFV Actual',  readonly=True, compute="_compute_ufv", digits=dp.get_precision('UFV HR'))
    spent_credit = fields.Float('Credito Gastado', readonly=True, compute="_get_spen_credit", store=True, default=0, states={'draft': [('readonly', False)]})

    total_hours = fields.Float('Total Horas', compute="_get_hours", store=True)
    amount_pay_hours = fields.Float('Total a Pagar', compute="_get_amount_pay", store=True)




    @api.multi
    def compute_sheet(self):
        new_xtra_hours = []
        # xtra_hours = self._get_hours_extra()
        # for ex in xtra_hours:
        #     flag = False
        #     for extra in self.extra_hours_line_ids:
        #         if extra.extra_line_id.id == ex['extra_line_id']:
        #             if not extra.freeze:
        #                 extra.hours = ex['hours']
        #                 extra.amount_pay = ex['amount_pay']
        #             flag = True
        #     if not flag:
        #         new_xtra_hours.append(ex)
        # if new_xtra_hours:
        #     self.extra_hours_line_ids = new_xtra_hours
        self._get_saldo()

        contract_ids = self.get_contract(self.employee_id, self.date_from, self.date_to)
        contracts = self.env['hr.contract'].browse(contract_ids)
        new_wk_days = []
        worked_days = self.get_worked_day_lines(contracts, self.date_from, self.date_to)


        for wd in worked_days:
            flag = False
            for wls in self.worked_days_line_ids:
                if wls.code == wd['code']:
                    wls.number_of_days = wd['number_of_days']
                    wls.number_of_hours = wd['number_of_hours']
                    flag = True
            if not flag:
                new_wk_days.append(wd)
        if new_wk_days:
            self.worked_days_line_ids = new_wk_days

        new_inputs = []
        input_line_ids = self.get_inputs(contracts, self.date_from, self.date_to)
        for l in input_line_ids:
            flag = False
            for inputs in self.input_line_ids:
                if inputs.code == l['code']:
                    if inputs.freeze == False:
                        inputs.amount = l['amount']
                    flag = True
            if not flag:
                new_inputs.append(l)
        if new_inputs:
            self.input_line_ids = new_inputs

        res = super(HrPayslip, self).compute_sheet()
        for p in self:
            for line in p.details_by_salary_rule_category:
                if line.code == 'RCIVA_T':
                    p.rciva = line.amount
                    line = line

            if p.previous_ufv > 0:
                total = p.saldo / p.previous_ufv
            else:
                total = 0
            if p.current_ufv > 0:
                p.current_saldo = total * p.current_ufv
            else:
                p.current_saldo = 0
            if p.rciva - p.current_saldo  - p.credit_form110 > 0:
                saldo = 0
                p.rciva_current = p.rciva - p.current_saldo - p.credit_form110
            else:
                saldo = (p.rciva - p.current_saldo - p.credit_form110) * -1
                p.rciva_current = 0

            for l in p.line_ids.filtered(lambda x: x.code == 'RCIVA'):
                 if l.code == 'RCIVA':
                    l.amount = p.rciva_current

            p.saldo_next_month = saldo
            if p.credit_form110 - saldo  > 0:
                p.spent_credit = p.credit_form110 - saldo
            else:
                p.spent_credit = 0

        return res

    @api.multi
    @api.depends('line_ids', 'credit_form110', 'saldo_next_month')
    def _get_spen_credit(self):
        for s in self:
            if s.credit_form110 - s.saldo_next_month  > 0:
                    s.spent_credit = s.credit_form110 - s.saldo_next_month
            else:
                s.spent_credit = 0


    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):

        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        inputs_obj = self.env['hr.others']
        advance_obj = self.env['hr.advance']
        loan_obj = self.env['hr.loan']
        form110_obj = self.env['hr.form110']

        for i in inputs_obj.search([('contract_id', 'in', contract_ids.ids), ('state', '=', 'process'), ('date', '>=', date_from), ('date', '<=', date_to)]):

            input = {
                'name': i.name,
                'code': i.code,
                'contract_id': i.contract_id.id,
                'amount': i.monto,
                'others_id': i.id
            }
            res += [input]

        for a in advance_obj.search([('contract_id', 'in', contract_ids.ids), ('state', '=', 'process'), ('date', '>=', date_from), ('date', '<=', date_to), ('state_p', '=', True)]):

            input = {
                'name': a.name,
                'code': a.code,
                'contract_id': a.contract_id.id,
                'amount': a.amount,
                'advance_id': a.id
            }
            res += [input]

        for lo in loan_obj.search([('contract_id', 'in', contract_ids.ids), ('state', '=', 'process'), ('add_nomina', '=', True)]):
            for l in lo.line_ids:
                if l.date >= date_from and l.date <= date_to and l.state == 'process':
                    input = {
                        'name': l.name,
                        'code': l.code,
                        'contract_id': lo.contract_id.id,
                        'amount': l.amount,
                        'loan_line_id': l.id
                    }
                    res += [input]
                    if l.interest > 0:
                        input = {
                            'name': l.name+' Interes',
                            'code': 'INTERES',
                            'contract_id': lo.contract_id.id,
                            'amount': l.interest,
                            'loan_line_id': l.id
                        }
                        res += [input]


        for f110 in form110_obj.search([('contract_id', 'in', contract_ids.ids), ('state', '=', 'process'), ('date', '>=', date_from), ('date', '<=', date_to)]):

            input = {
                'name': f110.name,
                'code': f110.code,
                'contract_id': f110.contract_id.id,
                'amount': f110.amount,
                'form110_id': f110.id
            }
            res += [input]

        return res


    @api.multi
    def check_done(self):
        for l in self.input_line_ids:
            if l.advance_id:
                if l.advance_id.state == 'process':
                    l.advance_id.hr_done_advance()
                    l.advance_id.payslip_id = self.id
            elif l.loan_line_id:
                if l.loan_line_id.state == 'process':
                    l.loan_line_id.hr_done_loan_line()
                    l.loan_line_id.payslip_id = self.id
            elif l.others_id:
                if l.others_id.state == 'process':
                    l.others_id.hr_done_other_inputs()
                    l.others_id.payslip_id = self.id
            elif l.form110_id:
                if l.form110_id.state == 'process':
                    l.form110_id.hr_done_form110()
                    l.form110_id.payslip_id = self.id

        # for x in self.extra_hours_line_ids:
        #     if x.extra_line_id:
        #         x.extra_line_id.hr_done_extra_hours_line();
        #         x.payslip_id = self.id
        return True

    @api.multi
    def process_sheet(self):
        move_pool = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Payroll')

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            default_partner_id = slip.employee_id.address_home_id.id
            name = _('Payslip N° %s') % (slip.number)
            date = slip.date or slip.date_to
            move = {
                'narration': name,
                'date': date,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
            }
            for line in slip.details_by_salary_rule_category:
                amt = slip.credit_note and -line.total or line.total
                if float_is_zero(amt, precision_digits=precision):
                    continue
                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id

                if line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id :
                    analytic_id = line.salary_rule_id.analytic_account_id.id
                elif slip.contract_id.analytic_account_id and slip.contract_id.analytic_account_id.id:
                    analytic_account_id = slip.contract_id.analytic_account_id.id
                else:
                    analytic_account_id = False
                if debit_account_id:

                    debit_line = (0, 0, {
                    'name': line.name,
                    'date': fields.Date.today(),
                    'partner_id': line._get_partner_id(line, credit_account=False),
                    'account_id': debit_account_id,
                    'journal_id': slip.journal_id.id,
                    'debit': amt > 0.0 and amt or 0.0,
                    'credit': amt < 0.0 and -amt or 0.0,
                    'analytic_account_id': analytic_account_id,
                    'tax_line_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if credit_account_id:

                    credit_line = (0, 0, {
                    'name': line.name,
                    'date': fields.Date.today(),
                    'partner_id': line._get_partner_id(line, credit_account=True),
                    'account_id': credit_account_id,
                    'journal_id': slip.journal_id.id,
                    'debit': amt < 0.0 and -amt or 0.0,
                    'credit': amt > 0.0 and amt or 0.0,
                    'analytic_account_id': analytic_account_id,
                    'tax_line_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': date,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': date,
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)

            move.update({'line_ids': line_ids})
            move_id = move_pool.create(move)
            self.move_id = move_id
            self.date = fields.Date.today()
            move_id.post()
        self.paid = True
        self.state = 'done'

# class hr_payslip_extra_hours(models.Model):
#     _name = 'hr.payslip.extra.hours'
#     _description = 'Horas extras'

#     name = fields.Char('Descripcion')
#     code = fields.Char('Codigo', default="XTRA_H")
#     payslip_id = fields.Many2one('hr.payslip', 'Nomina')
#     extra_line_id = fields.Many2one('hr.extra.hours.line', 'Nomina')
#     contract_id = fields.Many2one('hr.contract', 'Contrato', readonly=True, required=True, states={'draft': [('readonly', False)]})
#     hours = fields.Float('Horas extra Trabajadas')
#     amount_pay = fields.Float('Total Pagado')
#     period_id = fields.Many2one('hr.period', string="Periodo", related="extra_line_id.period_id", readonly=True)
#     state = fields.Selection([
#         ('draft', 'Borrador'),
#         ('process', 'Cola de Espera'),
#         ('done', 'Realizado'),], 'Estado', readonly=True, related="extra_line_id.state")
#     freeze = fields.Boolean('Valor Congelado')


# class hr_salary_rule(models.Model):
#     _inherit = 'hr.salary.rule'
#     _order = "sequence asc, active desc"

#     base = fields.Boolean('Regla Base', help="Reglas base, con importes fijos para el calculo de de las demas reglas.")


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.multi
    def close_payslip_run(self):
        res = super(HrPayslipRun, self).close_payslip_run()
        for s in self.slip_ids:
            s.process_sheet()
        return res


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    others_id = fields.Many2one('hr.others', 'Otras Entradas')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done','Confirmado'),
        ('cancel', 'Cancelado'),
        ], string='Estado', readonly=True)
    advance_id = fields.Many2one('hr.advance', 'Pagos adelantados')
    loan_line_id = fields.Many2one('hr.loan.line', 'Prestamos')
    form110_id = fields.Many2one('hr.form110', 'Formulario 110')
    date = fields.Date('Fecha', compute='_compute_date', store=True)
    freeze = fields.Boolean('Valor Congelado')

    @api.multi
    @api.depends('others_id', 'advance_id', 'loan_line_id')
    def _compute_date(self):
        for s in self:
            if s.others_id:
                s.date = s.others_id.date
            elif s.advance_id:
                s.date = s.advance_id.date
            elif s.loan_line_id:
                s.date = s.loan_line_id.date
            elif s.form110_id:
                s.date = s.form110_id.date
            else:
                s.date = s.Date.today()
