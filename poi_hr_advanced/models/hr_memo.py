from odoo import models, fields, api, _, tools
import time

class HrMemo(models.Model):
    _name = 'hr.memo'
    _description = 'Memo Empleado'


    def _get_user_create(self):
        user_create = self.env['res.users'].browse(self.env.user.id).id
        if not user_create:
            return False
        return user_create

    def _get_employee(self):
        context = self.env.context
        active_id = context.get('active_id',[])
        employee_id = self.env['hr.employee'].browse(active_id).id
        if not employee_id:
            return False
        return employee_id

    @api.multi
    def _get_employee_from(self):
        employee_obj = self.env['hr.employee']
        employee_id = employee_obj.search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id[0].id


    name = fields.Char( string='Descripción:', required=True)
    memo_type_id = fields.Many2one('hr.memo.type',  string='Tipo:', required=True)
    date = fields.Date('Fecha:', default= lambda *a: time.strftime('%Y-%m-%d'))
    company_id = fields.Many2one('res.company',  string='Compañia', default=lambda self: self._context.get('company_id', self.env.user.company_id.id))
    mensaje = fields.Html('Mensaje')
    employee_from = fields.Many2one('hr.employee',  string='De:', required=True, default=_get_employee_from)
    employee_id = fields.Many2one('hr.employee',  string='Dirigido a:', default=_get_employee, required=True)
    user_create = fields.Many2one('res.users', string='Creado por:', default=_get_user_create, required=True, readonly=True)
    employee_cc_ids = fields.Many2many('hr.employee', string='C.C.:')
    template_id = fields.Many2one('hr.memo.template', string= 'Plantilla', select=True)
    state = fields.Selection([
        ('draft','Borrador'),
        ('done','Confirmado'),
        ],'Status', readonly=True, default="draft")

    @api.multi
    def write(self, vals):
        dirigido_a = self.employee_id
        memo_type = self.memo_type_id
        memo_count = self.search_count([('employee_id','=',dirigido_a.id),('memo_type_id', '=', memo_type.id)])
        permitido = self.memo_type_id.number_permit
        if memo_count > permitido:
            raise osv.except_osv(_('No permitido!'), _('El empleado superó el número permitido de Memo especificado en el Tipo de Memo.'))

        return super(HrMemo,self).write(vals)


    @api.multi
    def action_confirm_memo(self):
        self.state = 'done'

    @api.multi
    def action_memo_print(self):
        return self.env['report'].get_action(self, 'poi_hr_advanced.memo_print')

    @api.multi
    def save_as_template(self):
        template_obj = self.env['hr.memo.template']
        if self.template_id:
            self.template_id.template = self.mensaje
        else:
            template_id = template_obj.create({
                'name': self.name,
                'template': self.mensaje,
                'memo_type_id': self.memo_type_id.id,
                })
            self.template_id = template_id.id

    @api.onchange('template_id')
    def on_change_template(self):
        if self.template_id:
            self.mensaje = self.template_id.template
            self.name = self.template_id.name


class HrMemoTemplate(models.Model):
    _name = 'hr.memo.template'
    _description = 'templates de los memos'

    name = fields.Char('Descripción')
    memo = fields.Char('Descripción del Memo')
    template = fields.Html('Template del Mensaje')
    memo_type_id = fields.Many2one('hr.memo.type', 'Tipo de Memo')


class HeMemoType(models.Model):
    _name = 'hr.memo.type'
    _description = 'Tipo de memo'

    name = fields.Char(string='Tipo Memo', required=True)
    number_permit = fields.Float(string= 'Número Permitido')



class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'

    @api.multi
    def _memo_count(self):
        memo = self.env['hr.memo']
        for s in self:
            s.memo_count = memo.search_count([('employee_id', '=', s.id)])


    memo_ids= fields.One2many('hr.memo', 'employee_id', string='Memos', required=False, readonly=True)
    memo_count= fields.Float(compute="_memo_count", type='integer', string='Memo')

    @api.multi
    def open_memo(self):
        res = self.env['ir.actions.act_window'].for_xml_id('poi_hr_advanced', 'act_hr_employee_memo_list')
        hr_memo_ids = [po.id for po in self.browse(self.id)[0].memo_ids]
        res['domain'] = ((res.get('domain', []) or []) +[('id', 'in', hr_memo_ids)])
        return res
