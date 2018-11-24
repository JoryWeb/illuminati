# -*- coding: utf-8 -*-

from odoo import models, fields, api


@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()


class OpTeacher(models.Model):
    _name = 'op.teacher'

    image = fields.Binary('Imagen')
    title_id = fields.Many2one('op.title', 'Titulo')
    name = fields.Char('Nombre', required=True)
    last_name = fields.Char('Apellido Paterno', required=True)
    last_name2 = fields.Char('Apellido Materno')
    initials = fields.Char('Sigla')
    gender = fields.Selection([('m', 'Masculino'), ('f', 'Femenino'), ('o', 'Otro')], 'Genero', required=True)
    phone = fields.Integer('Telefono')
    cellphone = fields.Integer('Celular')
    email = fields.Char('Email')
    classification_id = fields.Many2one('op.teacher.classification', 'Clasificacion')

    # INFORMACION PERSONAL
    birth_date = fields.Date('Fecha de Nacimiento', required=True)
    nationality = fields.Many2one('res.country', 'Primera Nacionalidad')
    lang = fields.Selection(_lang_get, string='Lenguaje Madre', default=lambda self: self.env.lang)
    blood_group_id = fields.Many2one('op.blood.group', 'Grupo Sanguineo')
    emergency_contact = fields.Many2one('res.partner', 'Contacto')

    # DATOS DE IDENTIFICACION
    ci = fields.Char('CI')
    issued_ci = fields.Selection(
        [('lp', 'LP'), ('or', 'OR'), ('pt', 'PT'), ('cb', 'CB'), ('ch', 'CH'), ('tj', 'TJ'), ('pa', 'PA'), ('bn', 'BN'),
         ('sc', 'SC')])
    extension_ci = fields.Selection(
        [('lp', 'LP'), ('or', 'OR'), ('pt', 'PT'), ('cb', 'CB'), ('ch', 'CH'), ('tj', 'TJ'), ('pa', 'PA'), ('bn', 'BN'),
         ('sc', 'SC')])
    passport = fields.Integer('Nº Pasaporte')
    due_date_visa = fields.Date('Fecha Vencimiento VISA')
    foreign_id = fields.Char('ID Extranjero')
    due_date_foreign_id = fields.Date('Fecha Vencimiento ID Extranjero')

    # DETALLE DE DIRECCION
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    department = fields.Selection(
        [('lp', 'La Paz'), ('or', 'Oruro'), ('pt', 'Potosi'), ('cb', 'Cochabamba'), ('ch', 'Chuquisaca'), ('tj', 'Tarija'), ('pa', 'Pando'), ('bn', 'Beni'),
         ('sc', 'Santa Cruz')])
    zone = fields.Char()
    country_id = fields.Many2one('res.country', 'Pais')
    
    #MATERIAS
    matter_ids = fields.One2many('op.subject', 'id', string='Materias')
