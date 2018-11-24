#!/usr/bin/env python
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
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


from openerp import models, fields, api, _, tools
from openerp.tools.translate import _
from openerp.exceptions import UserError, ValidationError


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    description_revert = fields.Many2one('revert.description','Reason')
    no_annul = fields.Boolean('No Annul')

    @api.onchange('description_revert')
    def change_description(self):
        self.description = self.description_revert.name or False

    @api.multi
    def compute_refund(self, mode='refund'):

        inv_obj = self.env['account.invoice']
        context = dict(self._context or {})

        for form in self:
            for inv in inv_obj.browse(context.get('active_ids')):
                if inv.state == 'open' and mode == 'refund' and not form.no_annul:
                    raise ValidationError(_('You cannot use this mode on this invoice.'))
                    return False

        ret = super(AccountInvoiceRefund, self).compute_refund(mode)

        for form in self:
            if ret and (not form.no_annul and mode=='refund') or (mode in ('cancel', 'modify')):
                #Marcar una factura reintegrada como Anulada para fines impositivos
                updated = inv_obj.browse(context.get('active_ids'))
                if updated:
                    updated.estado_fac = 'A'
                    if (updated.reference):
                        updated.reference = '1°Rectificativa ' + updated.reference
                    else:
                        updated.reference = '1°Rectificativa ' + updated.move_name
                        
                if not updated:
                    raise ValidationError(('No se ha podido marcar la factura origen como Anulada.'))
                    return False
        try:
            if 'domain'in ret:
                if len(ret['domain']) == 3:
                    invoice_ids = ret['domain'][2][2]
                    for i in inv_obj.browse(invoice_ids).filtered(lambda i: i.state == 'paid'):
                        i.reference = '2°Rectificativa ' + i.reference

        except TypeError, te:
            return ret

        return ret
