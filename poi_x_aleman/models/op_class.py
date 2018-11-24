# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpCourse(models.Model):
    _inherit = 'op.course'
    _rec_name = 'course_id'

    name = fields.Char('Name', required=False)
    code = fields.Char('Code', size=16, required=False)
    section = fields.Char('Section', size=32, required=False)
    fees_term_id = fields.Many2one('op.fees.terms', required=False)
    state = fields.Selection([
        ('activo', 'Activo'),
        ('inactivo', 'inactivo'),
        ('historico', 'Historico'),
    ], string='Estado', default='activo', index=True, readonly=True)
    
    course_id = fields.Many2one('op.batch', 'Curso', required=True)
    school_year = fields.Char('Año Escolar', required=True)
    course_responsable_1 = fields.Many2one('op.teacher', 'Responsable de Curso 1', required=True)
    course_responsable_2 = fields.Many2one('op.teacher', 'Responsable de Curso 2')

    @api.multi
    def change_status(self):
        if not self:
            return False
        elif self.state == 'activo':
            self.write({'state': 'inactivo'})
            return True
        else: 
            self.write({'state': 'activo'})
            return True
        
    def action_view_all_students(self):
        return {
            'name': 'Estudiantes',
            'res_model': 'op.student',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 20
        }
