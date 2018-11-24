# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning

class OpSchoolPeriod(models.Model):
    _name = 'op.school.charge'
    _description = "Gestion Escolar, Cargos"

    period_id = fields.Many2one('op.school.period', 'Gestion Escolar')
    year_id = fields.Many2one('op.year', 'Gestion Escolar')
    month_id = fields.Many2one('op.month', 'Mes')
    auto = fields.Boolean('Generar Cargo Automatico')
    date = fields.Date('Fecha de Generacion')
    count_charge = fields.Integer('Cargos Generados')


class OpSchoolPeriod(models.Model):
    _name = 'op.school.nivel'
    _description = "Gestion Escolar, Niveles"

    period_id = fields.Many2one('op.school.period', 'Gestion Escolar')
    name = fields.Integer('Nivel')
    amount_first_fee = fields.Float('Monto Primera Pension')
    amount_regular_fee = fields.Float('Monto Pension Regular')


class OpSchoolPeriod(models.Model):
    _name = 'op.school.chargeauto'
    _description = "Gestion Escolar, Cargos"

    period_id = fields.Many2one('op.school.period', 'Gestion Escolar')
    year_id = fields.Many2one('op.year', 'Gestion Escolar')
    month_id = fields.Many2one('op.month', 'Mes')
    auto = fields.Boolean('Generar Cargo Automatico')
    count_charge = fields.Integer('Cargos Generados')


class OpSchoolPeriod(models.Model):
    _name = 'op.school.period'
    _description = "Gestion Escolar"


    year_id = fields.Many2one('op.year', 'Gestion Escolar')
    currency_id = fields.Many2one('res.currency', 'Moneda')
    date_from = fields.Date('Fecha de Incio')
    date_to = fields.Date('Fecha de Cierre')

    surcharge = fields.Float('Recargo por pension retrasada(%)')
    discount_childs = fields.Float('Descuento por pago anual  por Hijo')
    day_initial = fields.Integer('Dia del mes para generar cargo')

    visit_cost = fields.Float('Costo de Visita')
    first_fee = fields.Float('Primera Cuota')
    supplies_cost =  fields.Float('Material Escolar')

    amount_camera = fields.Float('Monto Camara')

    charge_id = fields.One2many('op.school.charge', 'period_id', 'Cargos/Pensiones')
    nivel_id = fields.One2many('op.school.nivel', 'period_id', 'Nivel')
    chargeauto_id = fields.One2many('op.school.chargeauto', 'period_id', 'Cargos Automaticos')

    state = fields.Selection(
            string="Estado",
            selection=[
                    ('draft', 'incial'),
                    ('active', 'activo'),
                    ('archive', 'Archivado'),
            ], default='draft', readonly=True, states={'draft':[('readonly',False)]}
        )

    @api.multi
    def action_open_period(self):
        return
