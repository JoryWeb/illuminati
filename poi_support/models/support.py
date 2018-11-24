# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SupportTicket(models.Model):
    _name = 'poi.support.ticket'
    _description = 'Ticket de soporte'

    name = fields.Char('Nombre', required=True)
    type_int = fields.Selection([('user','User report'),('bug','Bug'),('system','System')], string='Tipo interno', help="Valor interno para especificar el origen del mensaje")
    user_id = fields.Many2one('res.users', string='User')
    description = fields.Text(u'Descripcioó')
    debug_error = fields.Text(u'Error técnico')
    debug_url = fields.Char(u'URL error')

    @api.model
    def log_ticket(self, name='', message='', url=''):
        if name != '':
            self.create({
                'type_int': 'bug',
                'user_id': self.env.uid,
                'name': name,
                'debug_error': message,
                'debug_url': url,

            })

        return True
