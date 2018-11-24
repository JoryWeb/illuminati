# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpMedicalFile(models.Model):
    _name = 'op.medical.file'

    #Datos Personales
    student_id = fields.Many2one('op.student', 'Alumno', required=True)
    student_family_code = fields.Many2one('op.family', 'Codigo de Familia', compute='_compute_family_code')

    #Contactos de emergencia
    #emergecy_contact

    #Cobertura Medica
    private_insurance = fields.Selection([('si', 'SI'), ('no', 'NO')], 'Seguro Privado')
    insurance_name = fields.Char('Nombre del Seguro')
    insurance_phone = fields.Integer('Telefono del Seguro')
    medical_center = fields.Char('Centro Medico de Referencia')
    phone_medical_center = fields.Integer('Telefono Centro')
    family_doctor = fields.Char('Medico pediatra o de cabecera')
    phone_doctor = fields.Integer('Telefono')
    #diseases =

    #Antecedentes de Interes
    operations = fields.Char('Operaciones')
    fractures = fields.Char('Traumatismos/Fracturas')
    coagulation_problems = fields.Char('Problemas de Coagulacion')
    blood_group_id = fields.Many2one('op.blood.group', 'Grupo Sanguineo')
    #vacunas
    #alergias
    #medicacion
    contraindicated_medications = fields.Text('Medicamentos Contraindicados', required=True)

    #Deportes que no debe practicar
    sport_ids = fields.Many2many('op.sport', 'Deportes')

    @api.multi
    @api.depends('student_id')
    def _compute_family_code(self):
        for record in self:
            if record.student_id:
                record.student_family_code = (record.student_id.family_code and record.student_id.family_code.id) or False
