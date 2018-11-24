##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2014 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Grover Menacho
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

import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError


# These are going to be the core of each document, so it needs all the possible information
class PoiAuthDocumentLog(models.Model):
    _name = 'poi.auth.document.log'
    _description = 'Authorization Document'
    _inherit = ['mail.thread']
    _order = "start_date desc, id desc"

    auth_id = fields.Many2one('poi.auth.auth', 'Auth ID')
    user_id = fields.Many2one('res.users', 'Requesting User')
    circuit_id = fields.Many2one('poi.auth.circuit', 'Authorization Circuit',
                                 help="If this field is not filled header circuit is going to be applied")
    model_id = fields.Many2one('ir.model', string='Model', related='auth_id.model_id')
    res_id = fields.Integer('ID of model')
    start_date = fields.Datetime('Requesting Date', default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    end_date = fields.Datetime('Closing Date')
    line_ids = fields.One2many('poi.auth.document.log.line', 'log_id', 'Lines')
    state = fields.Selection([('pending', 'Pending'),
                              ('approved', 'Approved'),
                              ('denied', 'Denied'),
                              ('cancelled', 'Cancelled')], string='State', default='pending')
    extra_data = fields.Text('Extra Data',
                             help='All the extra data must be filled here: context, parameters, date... Any extra data that could be useful to use on approve or reject. Data must be filled in JSON (dict block)')
    description = fields.Text('Description')

    #CALCULATED FIELDS
    @api.multi
    def _is_auth_assigned(self):
        for doc in self:
            res = False
            state = ''
            for line in doc.line_ids:
                if line.user_id.id == self.env.uid:
                    res = True
                    state = line.state
                    break
            doc.auth_assigned = res
            if state != '':
                doc.auth_state = state

    @api.multi
    def _set_auth_text(self):
        for doc in self:
            for l in doc.line_ids:
                if l.user_id.id == self.env.uid:
                    l.message = doc.auth_text

    @api.multi
    def _get_auth_name(self):
        for doc in self:
            res = ''
            if doc.model_id:
                res = self.env[doc.model_id.model].sudo().browse(doc.res_id).display_name
            doc.name = res

    @api.multi
    def _get_auth_log(self):
        for doc in self:
            res = ''
            for l in doc.line_ids:
                if res == '':
                    res = l.user_id.display_name + ': ' + l.state
                else:
                    res += ", " + l.user_id.display_name + ': ' + l.state
            doc.auth_log = res

    auth_assigned = fields.Boolean('Assigned to Auth', compute=_is_auth_assigned, store=False)
    name = fields.Char('Name', compute=_get_auth_name)
    auth_state = fields.Selection([('to_be_notified', 'Waiting Notification'),
                              ('notified', 'Notified'),
                              ('approved', 'Approved'),
                              ('denied', 'Denied'),
                              ('not_needed', 'Not Needed')], string='My Auth State', compute=_is_auth_assigned, store=False)

    auth_text = fields.Text('Auth Text', store=False, inverse=_set_auth_text)
    auth_log = fields.Text('Log', compute=_get_auth_log)

    #NEEDACTION
    @api.model
    def _needaction_count(self, domain=None):
        docs = self.search([('state','=','pending')])
        num = 0
        for doc in docs:
            for line in doc.line_ids:
                if line.user_id.id == self.env.uid and line.state == 'notified':
                    num += 1
        return num

    # JQUERY CALLS
    @api.model
    def get_doc_data(self, id):
        res = {'message': '', 'to_approve': False}
        doc = self.browse(id)

        users_to_approve = [l.user_id.id for l in doc.line_ids]

        if self.env.uid in users_to_approve:
            for line in doc.line_ids:
                if line.user_id.id == self.env.uid and line.state == 'notified':
                    res['message'] = doc.description
                    res['to_approve'] = True
                elif line.user_id.id == self.env.uid and line.state == 'to_be_notified':
                    res['message'] = _('Se le notificará cuando pueda aprobar / denegar el documento.')
                elif line.user_id.id == self.env.uid and line.state in ['approved','denied']:
                    res['message'] = _('Usted ya aprobó / denegó el documento. Refresque el Documento para Continuar.')

        else:
            res['message'] = doc.description

        return res

    @api.model
    def approval_click(self, id, message=''):
        doc = self.browse(id)
        if message != '':
            for l in doc.line_ids:
                if l.user_id.id == self.env.uid:
                    l.message = message
                    self.env[doc.model_id.model].browse(doc.res_id).message_post(body=message)
        doc.approve_document()

    @api.model
    def denial_click(self, id, message=''):
        doc = self.browse(id)
        if message != '':
            for l in doc.line_ids:
                if l.user_id.id == self.env.uid:
                    l.message = message
                    self.env[doc.model_id.model].browse(doc.res_id).message_post(body=message)
        doc.deny_document()

    # NORMAL FUNCTIONS

    @api.multi
    def approve_document(self):
        for l in self.line_ids:
            if l.user_id.id == self.env.uid:
                l.approve_line()

    @api.multi
    def deny_document(self):
        for l in self.line_ids:
            if l.user_id.id == self.env.uid:
                l.deny_line()


    @api.multi
    def send_notifications(self):
        partners_notified = []
        if self.circuit_id.type in ['anyone','everyone']:
            for l in self.line_ids:
                if l.state == 'to_be_notified':
                    self.message_subscribe_users(user_ids=[l.user_id.id])
                    l.state = 'notified'
                    partners_notified.append((4, l.user_id.partner_id.id))

        else:
            for l in self.line_ids:
                if l.state == 'to_be_notified':
                    self.message_subscribe_users(user_ids=[l.user_id.id])
                    l.state = 'notified'
                    partners_notified.append((4, l.user_id.partner_id.id))
                    break
                elif l.state == 'notified':
                    break
                elif l.state in ['approved','denied']:
                    continue

        msg = "Document %s needs to be approved. Reason: %s" % (self.display_name, self.description)
        new_msg = self.message_post(body=msg)
        msg = "El docuento necesita aprovacion"
        self.env[self.model_id.model].browse(self.res_id).message_post(body=msg)
        new_msg.sudo().write({'needaction_partner_ids': partners_notified})

    @api.multi
    def test_approval_state(self):

        if self.state == 'pending':
            approved = False
            denied = False

            if self.circuit_id.type == 'sequential' or self.circuit_id.type == 'everyone':
                temp_approved = False
                for l in self.line_ids:
                    if l.state == 'denied':
                        denied = True
                        temp_approved = False
                        break
                    elif l.state in ['to_be_notified', 'notified']:
                        temp_approved = False
                        break
                    elif l.state == 'approved':
                        temp_approved = True
                if temp_approved:
                    approved = True

            elif self.circuit_id.type == 'anyone':
                for l in self.line_ids:
                    if l.state == 'denied':
                        denied = True
                        break
                    elif l.state == 'approved':
                        approved = True
                        break
            if approved:
                msg = "Document %s has been approved." % (self.display_name)
                new_msg = self.message_post(body=msg)
                new_msg.sudo().write({'needaction_partner_ids': [(4, self.user_id.partner_id.id)]})
                self.write({'state': 'approved', 'end_date': time.strftime('%Y-%m-%d %H:%M:%S')})
                self.env[self.model_id.model].sudo(user=self.user_id.id).browse(self.res_id).on_authorized()
                for l in self.line_ids:
                    if l.state in [('notified','to_be_notified')]:
                        l.state = 'not_needed'
            elif denied:
                msg = "Document %s has been denied." % (self.display_name)
                new_msg = self.message_post(body=msg)
                new_msg.sudo().write({'needaction_partner_ids': [(4, self.user_id.partner_id.id)]})
                self.write({'state': 'denied', 'end_date': time.strftime('%Y-%m-%d %H:%M:%S')})
                self.env[self.model_id.model].sudo(user=self.user_id.id).browse(self.res_id).on_rejected()
                for l in self.line_ids:
                    if l.state in [('notified','to_be_notified')]:
                        l.state = 'not_needed'
            else:
                self.send_notifications() #If not approved it'll send notifications
        return True

    @api.multi
    def open_action(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.model_id.model,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.res_id,
            'context': {},
        }

class PoiAuthDocumentLogLine(models.Model):
    _name = 'poi.auth.document.log.line'

    log_id = fields.Many2one('poi.auth.document.log', 'Document Log')
    user_id = fields.Many2one('res.users', 'User')
    state = fields.Selection([('to_be_notified', 'Waiting Notification'),
                              ('notified', 'Notified'),
                              ('approved', 'Approved'),
                              ('denied', 'Denied'),
                              ('not_needed', 'Not Needed')], string='State')
    message = fields.Text('Approval/Reject Message')
    confirmed_date = fields.Datetime('Approval/Reject Date')

    @api.multi
    def approve_line(self):
        if self.env.uid != self.user_id.id:
            raise UserError(_('You cannot approve this. This line can be approved only by %s') % self.user_id.name)
        if self.state == 'to_be_notified':
            raise UserError(_(
                'You still cannot approve this document. You will be notified when you can approve or deny this document'))
        elif self.state == 'notified' or self.state == '':
            self.write({'state': 'approved', 'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        elif self.state == 'approved' or self.state == 'denied':
            self

        self.log_id.test_approval_state()

    @api.multi
    def deny_line(self):
        if self.env.uid != self.user_id.id:
            raise UserError(_('You cannot deny this. This line can be denied only by %s') % self.user_id.name)
        if self.state == 'to_be_notified':
            raise UserError(_(
                'You still cannot deny this document. You will be notified when you can approve or deny this document'))
        elif self.state == 'notified' or not self.state:
            if not self.message:
                raise UserError(_('You must fill the reason before denying the request'))
            self.write({'state': 'denied', 'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        elif self.state == 'approved' or self.state == 'denied':
            self

        self.log_id.test_approval_state()
