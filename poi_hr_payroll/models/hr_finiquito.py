from openerp import models, fields, api, _, tools
from datetime import datetime
from datetime import date


class HrFiniquitoOther(models.Model):
    _name = "hr.finiquito.other"
    _description = "Otros Conceptos de Pago"

    finiquito_id = fields.Many2one('hr.finiquito', 'Finiquito', required=True, ondelete='cascade')
    name = fields.Char('Descripcion')
    first_amount = fields.Float('Primer Mes')
    second_amount = fields.Float('Segundo Mes')
    third_amount = fields.Float('Tercer Mes')
    amount_total = fields.Float('Monto Total', compute="_compute_amount_total")

    @api.multi
    def _compute_amount_total(self):
        self.amount_total = (self.first_amount or 0.00) + (self.second_amount or 0.00) + (self.third_amount or 0.00)




class HrFiniquitoBenefit(models.Model):
    _name = 'hr.finiquito.benefit'
    _description = 'Calculo de Tiempos para los finiquitos'

    finiquito_id = fields.Many2one('hr.finiquito', 'Finiquito', required=True, ondelete='cascade')
    code = fields.Char(string="Codigo", required=True, default="Otros")
    name = fields.Char(string="Descripcion")
    gestion = fields.Integer(string="Gestion")
    tiempo = fields.Integer(string="Tiempo")
    medida = fields.Char(string="Medida")
    tiempo2 = fields.Integer(string="Tiempo_2")
    medida2 = fields.Char(string="Medida_2")
    monto = fields.Float(string="Monto")


class HrFiniquitoDeductions(models.Model):
    _name = 'hr.finiquito.deductions'
    _description = "Registro de Dedudciones"


    finiquito_id = fields.Many2one('hr.finiquito', 'Finiquito', required=True)
    code = fields.Char(string="Codigo")
    name = fields.Char(string="Descripcion")
    amount_total = fields.Float(string="Monto Total")
    advance_id = fields.Many2one('hr.advance', 'Adelanto', readonly=True)


class HrFiniquito(models.Model):
    _name = "hr.finiquito"
    _description = "Finiquito"
    _rec_name = "employee_id"

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id.contract_id:
            self.contract_id = self.employee_id.contract_id.id
            self.date_from = self.contract_id.date_start
            payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id),('state', '=', 'done')], limit=3, order="date_from desc")
            for index, p in enumerate(payslip_ids):
                if index == 0:
                    self.payslip_third_id = p.id
                    self.payslip_second_id = False
                    self.payslip_one_id = False
                elif index == 1:
                    self.payslip_second_id = p.id
                    self.payslip_one_id = False
                elif index == 2:
                    self.payslip_one_id = p.id
            if not payslip_ids:
                self.payslip_third_id = False
                self.payslip_second_id = False
                self.payslip_one_id = False
        else:
            self.contract_id = False
            self.date_from = False
            self.payslip_third_id = False
            self.payslip_second_id = False
            self.payslip_one_id = False

    @api.onchange('payslip_one_id')
    def onchange_payslip_one_id(self):
        for s in self.payslip_one_id.details_by_salary_rule_category.filtered(lambda x: x.code == 'NET'):
            self.first_amount = s.total

    @api.onchange('payslip_second_id')
    def onchange_payslip_second_id(self):
        for s in self.payslip_second_id.details_by_salary_rule_category.filtered(lambda x: x.code == 'NET'):
            self.second_amount = s.total

    @api.onchange('payslip_third_id')
    def onchange_payslip_third_id(self):
        for s in self.payslip_third_id.details_by_salary_rule_category.filtered(lambda x: x.code == 'NET'):
            self.third_amount = s.total

    @api.onchange('date_to', 'date_from')
    def onchange_date_to(self):
        if self.date_from == False:
            return
        if self.date_to == False:
            return

        data_entrada = datetime.strptime(self.date_from, '%Y-%m-%d')
        data_salida = datetime.strptime(self.date_to, '%Y-%m-%d')
        dif = (data_salida - data_entrada).days
        years = float(dif) / 360
        months = ((years - float(int(years))) * 360) / 30
        days = ((months - float(int(months))) * 30)

        self.years = int (years)
        self.months = int (months)
        self.days = days


    company_id = fields.Many2one('res.company', string=u'Compañia', change_default=True,
        default=lambda self: self.env['res.company']._company_default_get('hr.finiquito'))

    date = fields.Date('Fecha', default=fields.Date.today(), required=True, states={'draft': [('readonly', False)]})

    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string="Contrato", readonly=True, states={'draft': [('readonly', False)]})
    date_from = fields.Date('fecha de entrada', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_to = fields.Date('fecha de salida', required=True, readonly=True, states={'draft': [('readonly', False)]})
    note = fields.Text('Motivo del Retiro', readonly=True, states={'draft': [('readonly', False)]})
    ouster = fields.Boolean(string="Desahucio(Retiro Forsozo)", readonly=True, states={'draft': [('readonly', False)]})
    ouster_amount = fields.Float('Desahucio', readonly=True, states={'draft': [('readonly', False)]})
    benefit_ids = fields.One2many('hr.finiquito.benefit', 'finiquito_id', 'Lineas de Tiempo', readonly=True, states={'draft': [('readonly', False)]})
    other_ids = fields.One2many('hr.finiquito.other', 'finiquito_id', "Parte b", readonly=True, states={'draft': [('readonly', False)]})
    other_amount = fields.Float('Total Promedio Indemnizable', readonly=True, states={'draft': [('readonly', False)]})
    deductions_ids = fields.One2many('hr.finiquito.deductions', 'finiquito_id', "Deduciones", readonly=True, states={'draft': [('readonly', False)]})
    holidays_day = fields.Float('Vacacion(Dias)', readonly=True, states={'draft': [('readonly', False)]})
    holidays_month = fields.Float('Vacacion(Meses)', readonly=True, states={'draft': [('readonly', False)]})
    amount_benefit = fields.Float('Total Beneficios Sociales', readonly=True, states={'draft': [('readonly', False)]})
    amount_compensable = fields.Float(string="Total indemnizable", readonly=True, states={'draft': [('readonly', False)]})
    amount_deduction = fields.Float(string="Total Deduciones", readonly=True, states={'draft': [('readonly', False)]})
    amount_total_pay = fields.Float(string="Importe Liquido a Pagar", readonly=True, states={'draft': [('readonly', False)]})
    days = fields.Integer(string="Dias", readonly=True, states={'draft': [('readonly', False)]})
    months = fields.Integer(string="Meses", readonly=True, states={'draft': [('readonly', False)]})
    years = fields.Integer(string="Años", readonly=True, states={'draft': [('readonly', False)]})
    advance = fields.Boolean(string='Aplicar Adelanto')

    payslip_one_id = fields.Many2one('hr.payslip', 'Nomina Mes Primero')
    payslip_second_id = fields.Many2one('hr.payslip', 'Nomina Mes Segundo')
    payslip_third_id = fields.Many2one('hr.payslip', 'Nomina Mes Tercero')

    first_amount = fields.Float('Monto Mes Primero', required=True)
    second_amount = fields.Float('Monto Mes Segundo', required=True)
    third_amount = fields.Float('Monto Mes Tercero', required=True)

    amount_promedio = fields.Float('Proemdio Total', compute="_compute_amount_total")

    state = fields.Selection([
        ('draft','Borrador'),
        ('done','Confirmado'),
        ('cancel','Cancelado'),
        ],'Status', readonly=True, default="draft")


    dbonus = fields.Boolean('Doble Aguinaldo', default=False)
    years_amount = fields.Float('Monto por Años', default=0)
    months_amount = fields.Float('Monto por Meses', default=0)
    days_amount = fields.Float('Monto por Dias', default=0)

    months_bonus = fields.Integer('Aguinaldo Meses', default=0)
    days_bonus = fields.Integer('Aguinaldo Dias', default=0)
    bonus_amount = fields.Float('Total Aguinaldo', default=0)



    @api.multi
    def _compute_amount_total(self):
        self.amount_promedio = (self.first_amount or 0.00) + (self.second_amount or 0.00) + (self.third_amount or 0.00)

    @api.multi
    def compute_finiquito(self):
        promedio = sum(o.amount_total for o in self.other_ids) or 0.00
        promedio += self.amount_promedio
        promedio /= 3
        deductions = sum(d.amount_total for d in self.deductions_ids)

        self.years_amount = float(int(self.years)) * promedio
        self.months_amount = (float(self.months) / 12) * promedio
        self.days_amount = (float(self.days) / 360) * promedio

        aguinaldo_months = 0
        aguinaldo_days = 0
        if self.years > 0:
            data_entrada = date(date.today().year, 1, 1)
            data_entrada = datetime.combine(data_entrada, datetime.min.time())
            data_salida = datetime.strptime(self.date_to, '%Y-%m-%d')
            dif = (data_salida - data_entrada).days
            years = float(dif) / 360
            aguinaldo_months = ((years - float(int(years))) * 360) / 30
            aguinaldo_days = ((aguinaldo_months - float(int(aguinaldo_months))) * 30)
            aguinaldo_months_total = (aguinaldo_months / 12) * promedio
            aguinaldo_days_total = (aguinaldo_days / 360) * promedio

        self.months_bonus = aguinaldo_months
        self.days_bonus = aguinaldo_days
        self.bonus_amount = aguinaldo_months_total + aguinaldo_days_total
        if self.dbonus:
            self.bonus_amount *= 2

        benefits = []
        total_vacacion = 0
        if self.years >= 1:
            if self.holidays_day > 0:
                if self.years <= 4:
                    a = 2
                if self.years > 4 and self.years <= 9:
                    a = 1.5
                if self.years > 9:
                    a = 1
                total_vacacion = self.holidays_day / a / 360 * promedio
                benefits.append((0,0,{'code': 'otros', 'descripcion': 'Vacacion','tiempo': self.holidays_day, 'medida': 'Dias', 'monto': total_vacacion, 'gestion':''}))
            if self.holidays_month > 0:
                if self.years <= 4:
                    a = 2
                if self.years > 4 and self.years <= 9:
                    a = 1.5
                if self.years > 9:
                    a = 1
                total_vacacion = self.holidays_day / a / 12 * promedio
                benefits.append((0,0,{'code': 'otros', 'descripcion': 'Vacacion','tiempo': self.holidays_day, 'medida': 'Dias', 'monto': total_vacacion, 'gestion':''}))

            total_s = self.years_amount + self.months_amount + self.days_amount + self.bonus_amount + total_vacacion

            importe_liquido = total_s - deductions



            self.other_amount = promedio
            if self.ouster:
                self.ouster_amount = promedio * 3
            else:
                self.ouster_amount = 0.00
            self.benefit_ids = benefits
            self.amount_benefit = total_s
            self.amount_deduction = deductions
            self.amount_total_pay = importe_liquido


    @api.multi
    def cancel_finiquito(self):
        self.contract_id.date_out = False
        self.contract_id.state = 'open'
        self.state = 'cancel'


    @api.multi
    def done_finiquito(self):
        self.calcular_finiquito()
        self.contract_id.date_out = self.date_to
        self.contract_id.state = 'close'
        self.state = 'done'
