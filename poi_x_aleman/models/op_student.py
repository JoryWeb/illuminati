# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from dateutil import parser


class OpStudent(models.Model):
    _inherit = 'op.student'

    student_code = fields.Char('Codigo de Alumno', required=True)
    family_code = fields.Many2one('op.family', 'Codigo de Familia', required=True)
    middle_name = fields.Char()
    last_name = fields.Char()
    last_name2 = fields.Char('Segundo Apellido', size=128)
    full_name = fields.Char('Nombre Completo', required=True)

    # INFORMACION GENERAL
    # Datos generales
    gender = fields.Selection([('m', 'Masculino'), ('f', 'Femenino'), ('o', 'Otro')], 'Género', required=True)
    first_nationality = fields.Many2one('res.country', 'Primera Nacionalidad', required=True)
    second_nationality = fields.Many2one('res.country', 'Segunda Nacionalidad')
    third_nationality = fields.Many2one('res.country', 'Tercera Nacionalidad')
    religion = fields.Many2one('op.religion', 'Religion')
    # Datos de Identificacion
    ci = fields.Char('CI', required=True)
    issued_ci = fields.Selection(
        [('lp', 'LP'), ('or', 'OR'), ('pt', 'PT'), ('cb', 'CB'), ('ch', 'CH'), ('tj', 'TJ'), ('pa', 'PA'), ('bn', 'BN'),
         ('sc', 'SC')], required=True)
    extension_ci = fields.Char('Extension')
    passport = fields.Char('Pasaporte')
    foreign_id = fields.Char('ID Extranjero')
    # Datos de Edad
    birth_date = fields.Date('Birth Date')
    age = fields.Char('Edad', compute='_compute_age')
    # Datos de Contacto
    phone = fields.Char('Telefono')
    cellphone = fields.Char('Celular')
    email = fields.Char('Email')

    # DATOS FAMILIARES
    family = fields.Many2many('op.parent.contact', related='family_code.parents_ids', readonly=True)

    # DATOS DE EDUCACION
    class_id = fields.Many2one('op.course', 'Clase')
    course_id = fields.Many2one('op.batch', compute='_compute_class', store=True, string='Curso')
    course_level = fields.Char('Nivel de Curso', compute='_compute_class', store=True)
    rude = fields.Char('Registro RUDE')
    son_level = fields.Char('Nivel de Hijo')
    high_date = fields.Date('Fecha de Alta')
    low_date = fields.Date('Fecha de Baja')
    kinder = fields.Boolean('Kinder Proxima Gestion')


    # DATOS DE PAGO
    type_scholarship_id = fields.Many2one('op.type.scholarship', 'Tipo de Beca/Descuento')
    payment_responsable = fields.Many2one('op.parent.contact', 'Responsable de Pago', required=True)
    discount = fields.Integer('Descuento', related='type_scholarship_id.discount', readonly=True)
    total_discount = fields.Integer('Descuento Total', related='type_scholarship_id.discount', readonly=True)
    first_pension_applies = fields.Boolean('Aplica Primera Pension',
                                           related='type_scholarship_id.first_pension_applies', readonly=True)
    regular_pension_applies = fields.Boolean('Aplica Pension Regular',
                                             related='type_scholarship_id.regular_pension_applies', readonly=True)
    first_pension = fields.Float('Primera Pension')
    regular_pension = fields.Float('Pension Regular')

    # FUNCIONES
    # Calculo de Edad

    @api.multi
    @api.depends('class_id')
    def _compute_class(self):
        for record in self:
            if record.class_id:
                record.course_id = (record.class_id.course_id and record.class_id.course_id.id) or False
                record.course_level = (record.class_id.course_id and record.class_id.course_id.course_level) or False

    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                now = datetime.datetime.now()
                year = now.year
                birth_date = parser.parse(record.birth_date)
                age = year - birth_date.year
                record.age = age



    @api.onchange('family_code')
    def get_parents(self):
        return {
            'domain': {
                'payment_responsable':
                    [
                        ('family_id', '=', (self.family_code and self.family_code.id) or False)
                    ]
            }
        }
