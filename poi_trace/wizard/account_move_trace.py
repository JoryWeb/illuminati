##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.odoo.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.osv import osv

class AccountMoveTraceWizard(models.TransientModel):
    _name = 'account.move.trace.wizard'
    _description = 'Account Move Trace wizard'

    lines = fields.One2many('account.move.trace.wizard.line','wizard_id','Lines')

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMoveTraceWizard, self).default_get(default_fields)
        lines = []

        move_obj = self.env['account.move']
        for move in move_obj.browse(self.env.context.get('active_ids')):
            if move.src:
                reg_arr = move.src.split(',')
                res_model = str(reg_arr[0])
                res_id = int(reg_arr[1])
                name_description = "["+str(move.name_get()[0][1])
                if move.ref:
                    name_description+=" - "+ move.ref
                name_description += "] : " + str(self.env[res_model].browse(res_id).name_get()[0][1])
                lines.append((0, 0, {'name': name_description}))

        res.update(lines=lines)

        return res

    @api.multi
    def view_account_move_origin(self):


        #view = self.env.ref('stock.view_stock_enter_transfer_details')
        actual_context = self.env.context

        move_obj = self.env['account.move']
        sources = [x.src for x in move_obj.browse(actual_context.get('active_ids'))]

        res_model = False
        res_ids = []

        for reg in sources:
            if reg:
                reg_arr = reg.split(',')
                if not res_model:
                    res_model = str(reg_arr[0])
                    res_ids.append(int(reg_arr[1]))
                elif res_model != str(reg_arr[0]):
                    raise osv.except_osv(_('Error!'),_('You only can see grouped sources from the same model!!!'))
                else:
                    res_ids.append(int(reg_arr[1]))

        if not res_ids:
            return False

        return {
            'name': _('Account Move Origin'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': res_model,
            #'views': [(view.id, 'form')],
            #'view_id': view.id,
            'target': 'current',
            'domain': [('id','in',res_ids)],
            'context': self.env.context,
        }

class AccountMoveTraceWizardLine(models.TransientModel):
    _name = 'account.move.trace.wizard.line'
    _description = 'Account Move Trace wizard line'

    wizard_id = fields.Many2one('account.move.trace.wizard','Wizard')
    name = fields.Text('Name')
