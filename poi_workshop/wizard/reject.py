##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2016 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models
from odoo import netsvc


class workshop_request_reject(models.TransientModel):
    _name = 'workshop.request.reject'
    _description = 'Reject Request'

    reject_reason = fields.Text('Reject Reason', required=True)

    @api.multi
    def reject_request(self):
        active_id = self._context.get('active_id')
        if active_id:
            request = self.env['workshop.request'].browse(self._context.get('active_id'))
            request.write({'reject_reason': self.reject_reason})
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(self.env.user.id, 'workshop.request', active_id, 'button_reject', self.env.cr)
        return {'type': 'ir.actions.act_window_close',}


class workshop_order_stop(models.TransientModel):
    _name = 'workshop.order.stop'
    _description = 'Reject Request'

    stop_reason = fields.Many2one('workshop.stop.reason')

    @api.multi
    def stop_workshop(self):
        active_id = self._context.get('active_id')
        if active_id:
            workshop_order = self.env['workshop.order'].browse(self._context.get('active_id'))
            workshop_order.write({'stop_reason': self.stop_reason.id})
            workshop_order.write({'state_stop': workshop_order.state})
            workshop_order.write({'state': 'stop'})
            #                        self.env.cr)
        return {'type': 'ir.actions.act_window_close',}
