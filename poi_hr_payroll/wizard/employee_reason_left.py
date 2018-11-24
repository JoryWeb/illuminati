from odoo import models, fields, api, _, tools


class EmployeeReasonLeft(models.TransientModel):
    _name = "employee.reason.left"
    _description = "Razones de Desactivacion"

    reason_id = fields.Many2one('hr.employee.reason', 'Motivo')
    black_list = fields.Boolean('Lista Negra')

    @api.multi
    def action_desactive(self):
    	emp_id = self.env.context.get('active_id', False)
    	if emp_id:
    		emp_id = self.env['hr.employee'].browse(emp_id)
    		emp_id.active = not emp_id.active
    		emp_id.reason_id = self.reason_id.id
    		emp_id.black_list = self.black_list
