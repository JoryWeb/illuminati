from odoo import models, fields, api, _, tools

class HrContract(models.Model):
    _inherit = 'hr.contract'

    date_out = fields.Date(string="Fecha de Cancelacion")
    state = fields.Selection(
            [('draft', 'New'),
             ('open', 'Running'),
             ('pending', 'To Renew'),
             ('close', 'Expired')],
            string='Status', track_visibility='onchange',
            help='Status of the contract', default="draft")



    @api.multi
    def action_cancel_contract(self):
        # self.date_out = self.fields.Date.today()
        return self.write({'state': 'cancel'})

    @api.multi
    def action_done_contract(self):
        return self.write({'state': 'done'})

    @api.multi
    def action_valid_contract(self):
        return self.write({'state': 'valid'})
