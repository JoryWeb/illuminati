# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpParent(models.Model):
    _name = 'op.parent.contact'

    image = fields.Binary('Imagen', attachment=True)
    family_id = fields.Many2many('op.family', string='Codigo Familia', required=True)
    name = fields.Char('Nombre', required=True)
    relationship_id = fields.Many2one('op.relationship', 'Parentesco', required=True)

    # Datos Generales
    first_nationality = fields.Char('1ra Nacionalidad')
    second_nationality = fields.Char('2da Nacionalidad')
    mother_language = fields.Char('Leguaje Madre')
    religion = fields.Many2one('op.religion', 'Religion')
    family_tag_id = fields.Many2many('op.family.tag', string="Etiqueta Familiar")

    # Otra Informacion
    ex_student = fields.Boolean('Ex-Estudiante')
    clase = fields.Char('Clase')
    birthdate = fields.Date('Fecha de Nacimiento')

    # Datos de Identificacion
    ci = fields.Char('CI')
    extension_ci = fields.Char('')
    passport = fields.Char('Pasaporte')
    foreign_id = fields.Char('ID Extranjero')

    # Datos de Contacto
    phone = fields.Char('Telefono')
    cellphone = fields.Char('Celular')
    email = fields.Char('Email')

    # Datos de Labores
    profession_id = fields.Many2one('op.profession', 'Profesion')
    workplace = fields.Char('Lugar de Trabajo')
    job = fields.Char('Puesto de Trabajo')
    work_phone = fields.Char('Telefono de Trabajo')
    work_cellphone = fields.Char('Celular de Trabajo')
    work_email = fields.Char('Email de Trabajo')

    # Detale de Direccion
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    department = fields.Selection(
        [('lp', 'La Paz'), ('or', 'Oruro'), ('pt', 'Potosi'), ('cb', 'Cochabamba'), ('ch', 'Chuquisaca'),
         ('tj', 'Tarija'), ('pa', 'Pando'), ('bn', 'Beni'),
         ('sc', 'Santa Cruz')])
    zone = fields.Char()
    country_id = fields.Many2one('res.country', 'Pais')
