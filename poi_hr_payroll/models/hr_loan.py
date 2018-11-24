from odoo import models, fields, api, _, tools

class HrLoan(models.Model):
    _name = "hr.loan"
    _description = "Registro de Prestamos a Empleados"

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

    name = fields.Char('Descripcion', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    employee_id = fields.Many2one('hr.employee', 'Empleado', readonly=True, required=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', 'Contrato', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    note = fields.Text('Concepto', readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float('Monto a Prestar', readonly=True, required=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Fecha del Prestamo', readonly=True, states={'draft': [('readonly', False)]}, required=True, default=fields.Date.today())
    date_start = fields.Date('Fecha Inicio del Prestamo', default=fields.Date.today(), readonly=True, states={'draft': [('readonly', False)]}, required=True)
    time_pay = fields.Integer('Coutas de Pago', help="Determina la cantidad de cuotas en la que se pagara el prestamo", readonly=True,  states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('hr.loan.line', 'loan_id', "Pagos", readonly=True, states={'draft': [('readonly', False)]})
    add_nomina = fields.Boolean('Descontar en Nomina', readonly=True, states={'draft': [('readonly', False)]}, default=True)
    state = fields.Selection([
        ('draft','Borrador'),
        ('process','En Cola de Proceso'),
        ('cancel','Cancelado'),
        ('done','Realizado'),
        ],'Status', readonly=True, default="draft")
    company_id = fields.Many2one('res.company', string='Compañia', related="employee_id.company_id", store=True, readonly=True)
    rate = fields.Float('Interes A Pagar', readonly=True, help="Este es el interes que se añadira a cada mes de pago", states={'draft': [('readonly', False)]})

    journal_id = fields.Many2one('account.journal', 'Diario Contable', default=_get_journal, readonly=True, states={'draft': [('readonly', False)]})
    account_debit = fields.Many2one('account.account', 'Cuenta Deudora', default=_get_account_debit, domain=[('deprecated', '=', False)], readonly=True, states={'draft': [('readonly', False)]})
    account_credit = fields.Many2one('account.account', 'Cuenta Acreedora', default=_get_account_credit, domain=[('deprecated', '=', False)], readonly=True, states={'draft': [('readonly', False)]})
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica', readonly=True, states={'draft': [('readonly', False)]})
    move_id = fields.Many2one('account.move', 'Asiento Contable', readonly=True)
    force_date = fields.Date('Fecha Forzada', help='Fecha Forzada de Contabilizacion', readonly=True, states={'draft': [('readonly', False)]})
    assess = fields.Boolean('Contabilizar', default=True, readonly=True, states={'draft': [('readonly', False)]})

    amount_total_pay = fields.Float('Total a Pagar', compute="_compute_amount_total_pay")

    @api.multi
    def _compute_amount_total_pay(self):
        self.amount_total_pay = sum(l.amount_total_pay for l in self.line_ids)

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
    def calcular_loan(self):
        line_obj = self.env['hr.loan.line']
        data_line = []

        count = 0
        old_line_ids = line_obj.search([('loan_id', '=', self.id)])
        if old_line_ids:
            old_line_ids.unlink()
        if self.time_pay:
            self.amount_pay = self.amount / self.time_pay
        else:
            self.amount_pay = self.amount
        amount = self.amount

        if (self.amount_pay * self.time_pay) <= self.amount:
            resto = (self.amount - (self.amount_pay * self.time_pay)) + self.amount_pay
        if (self.amount_pay * self.time_pay) > self.amount:
            resto = self.amount - (self.amount_pay * (self.time_pay-1))
        promedio_mensual = amount / self.time_pay

        last = self.time_pay
        nextdate = datetime.strptime(self.date_start, "%Y-%m-%d").date()
        for i in range(1, self.time_pay+1):
            if i == last:
                data_line.append({'code': 'PRE', 'name': 'Couta '+str(i) , 'date': nextdate.strftime('%Y-%m-%d'), 'amount': resto})
            else:
                data_line.append({'code': 'PRE', 'name': 'Couta '+str(i) , 'date': nextdate.strftime('%Y-%m-%d'), 'amount': self.amount_pay})
            try:
              nextdate = nextdate.replace(month=nextdate.month+1)
            except ValueError:
              if nextdate.month == 12:
                nextdate = nextdate.replace(year=nextdate.year+1, month=1)
              if nextdate.month + 1 == 2 and nextdate.day > 28:
                nextdate = nextdate.replace(month=nextdate.month+1, day=28)

        self.line_ids = data_line


    @api.multi
    def cancel_loan(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def hr_process_loan(self):
        if self.assess:
            self.process_loan()
        if not self.add_nomina:
            self.write({'state': 'process'})
            return self.hr_done_loan()
        for l in self.line_ids:
            l.state = 'process'
        return self.write({'state': 'process'})

    @api.multi
    def hr_done_loan(self):
        return self.write({'state': 'done'})

    @api.multi
    def process_loan(self):
        move_pool = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Payroll')

        for loan in self:
            date = loan.date
            if loan.force_date:
                date = loan.force_date
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            default_partner_id = loan.employee_id.address_home_id.id
            name = _('Adelanto de %s') % (loan.employee_id.name)
            move = {
                'narration': name,
                'date': date,
                'ref': loan.name,
                'journal_id': loan.journal_id.id,
            }


            amt = False and -loan.amount or loan.amount
            if float_is_zero(amt, precision_digits=precision):
                continue
            partner_id = default_partner_id
            debit_account_id = loan.account_debit.id
            credit_account_id = loan.account_credit.id

            if debit_account_id:

                debit_line = (0, 0, {
                    'name': loan.name,
                    'date': date,
                    'partner_id': partner_id or False,
                    'account_id': debit_account_id,
                    'journal_id': loan.journal_id.id,
                    'debit': amt > 0.0 and amt or 0.0,
                    'credit': amt < 0.0 and -amt or 0.0,
                    'analytic_account_id': loan.analytic_account_id and loan.analytic_account_id.id or False,
                    # 'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                    # 'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                })
                line_ids.append(debit_line)

            if credit_account_id:

                credit_line = (0, 0, {
                    'name': loan.name,
                    'date': date,
                    'partner_id': partner_id or False,
                    'account_id': credit_account_id,
                    'journal_id': loan.journal_id.id,
                    'debit': amt < 0.0 and -amt or 0.0,
                    'credit': amt > 0.0 and amt or 0.0,
                    'analytic_account_id': loan.analytic_account_id and loan.analytic_account_id.id or False,
                    # 'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                    # 'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
                })
                line_ids.append(credit_line)
            move.update({'line_ids': line_ids})
            move_id = move_pool.create(move)
            self.write({'move_id': move_id.id})
            move_id.post()


class HrLoanLine(models.Model):
    _name = "hr.loan.line"
    _description = "Plan de Pagos por Prestamos"


    loan_id = fields.Many2one('hr.loan', 'Prestamo', readonly=True, required=True, ondelete='cascade', states={'draft': [('readonly', False)]})
    code = fields.Char('Codigo', readonly=True, default="PRE")
    name = fields.Char('Descripcion', readonly=True, states={'draft': [('readonly', False)]})
    amount = fields.Float('Monto', readonly=True, states={'draft': [('readonly', False)]})
    interest = fields.Float('Interes', readonly=True, states={'draft': [('readonly', False)]}, default=0.00)
    amount_total_pay = fields.Float('Monto Total', compute="_compute_amount_total_pay", store=True)
    date = fields.Date('Fecha', required=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('process', 'En Proceso'),
        ('done','Realizado'),
        ],'Status', select=True, default='draft', readonly=True)
    payslip_id = fields.Many2one('hr.payslip', 'Nomina', readonly=True)

    @api.multi
    @api.depends('interest', 'amount', 'state')
    def _compute_amount_total_pay(self):
        for s in self:
            if s.state == 'process':
                s.amount_total_pay = s.amount_total + s.interest

    @api.multi
    def cancel_loan_line(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def hr_process_loan_line(self):
        return self.write({'state': 'process'})

    @api.multi
    def hr_done_loan_line(self):
        self.write({'state': 'done'})
        flag = True
        for l in self.loan_id.line_ids:
            if l.state != 'done':
                flag = False
        if flag:
            self.loan_id.hr_done_loan()
        return

class HrLoanConfig(models.Model):
    _name = 'hr.loan.config'
    _description = 'Configuracion Contable Prestamos'
    _rec_name = "date"

    date = fields.Date('Fecha', default=fields.Date.today(), required=True)
    active = fields.Boolean('Activo', default=False)
    journal_id = fields.Many2one('account.journal', 'Diario Contable')
    account_debit = fields.Many2one('account.account', 'Cuenta Deudora', domain=[('deprecated', '=', False)])
    account_credit = fields.Many2one('account.account', 'Cuenta Acreedora', domain=[('deprecated', '=', False)])
