#!/usr/local/bin/python
from odoo import models, fields, api, _, tools

class HrAttachmentType(models.Model):
    _name = 'hr.attachment.type'
    _description = 'Tipos de Adjuntos'

    name = fields.Char('Nombre')
    auto = fields.Boolean('Auto', help="Si esta Marcado el tipo de Adjunto sera creado automaticamente cuando se cree un nuevo empleado.", default=True)


class HrAttachment(models.Model):
    _name = 'hr.attachment'
    _description = 'Archivos Adjuntos del Empleado'
    _rec_name = "type_id"

    @api.multi
    @api.depends('file_id')
    def _get_flag(self):
        for s in self:
            if not s.file_id:
                s.flag = False
            else:
                s.flag = True

    @api.multi
    def _set_flag(self):
        for s in self:
            if not s.file_id:
                s.flag = False

    @api.multi
    @api.depends('date_due')
    def _get_expired(self):
        for s in self:
            if s.date_due:
                if s.date_due < fields.Date.today():
                    s.expired = True
                else:
                    s.expired = False
            else:
                s.expired = False

    employee_id = fields.Many2one('hr.employee', 'Empleado',  required=True, ondelete='cascade')
    type_id = fields.Many2one('hr.attachment.type', 'Tipo de Documento', required=True)
    file_id = fields.Many2many('ir.attachment', 'attachment_ir_rel', 'hr_id', 'attachment_id', string='Archivo', inverse="_set_flag",  ondelete='cascade')
    flag = fields.Boolean('Entregado', compute="_get_flag", store=True)
    date_due = fields.Date('Fecha de Vencimiento')
    code = fields.Integer('Numero/Codigo')
    note = fields.Char('Nota')
    company_id = fields.Many2one('res.company', 'Compañia', related="employee_id.company_id", store=True, readonly=True)
    expired = fields.Boolean('Expirado?', compute="_get_expired")



class HrEmployee(models.Model):
    _description = 'Empleado'
    _inherit = 'hr.employee'

    @api.multi
    def _attachment_count(self):
        allowance = self.env['hr.attachment']
        for s in self:
            s.attachment_count = allowance.search_count([('employee_id', '=', s.id),('flag', '=', True)])

    attachment_count = fields.Integer(compute="_attachment_count", string="Subcidios")

    @api.model
    def create(self, values):
        res = super(HrEmployee, self).create(values)
        attachment_obj = self.env['hr.attachment']
        type_obj = self.env['hr.attachment.type']
        type_ids = type_obj.search([('auto', '=', True)])
        for type_id in type_ids:
            values_attachment = {
                'employee_id': res.id,
                'type_id': type_id.id,
            }
            attachment_obj.create(values_attachment)

        return res
