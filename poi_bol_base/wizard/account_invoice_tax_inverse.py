#!/usr/bin/env python
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from openerp.osv import fields, osv

import time
from openerp.tools.translate import _

class tax_inverse(osv.TransientModel):

    _name = 'poi_bol.tax_inverse.wizard'
    _description = "Cálculo precio inverso"
    
    _columns = {
       'amount': fields.float('Precio efectivo', required=True, help="Monto a ser calculado despues de aplicar los Impuestos del caso. Setear el precio para llegar a tal monto."),

    }

    def action_update_price(self, cr, uid, ids, context=None):

        if context is None:
            context={}
        if 'invoice_line_id' in context and context['invoice_line_id']:
            invoice_line_id = context['invoice_line_id']
        else:
            return True

        for data in  self.read(cr, uid, ids, context=context):

            amount = data['amount']

            new_price = 0.0
            tot_tax = 0.0

            iline = self.pool.get('account.invoice.line').browse(cr, uid, invoice_line_id, context={})[0]
            tax_ids=iline.invoice_line_tax_ids.ids
            invoice_id = iline.invoice_id.id
            decimals = iline.invoice_id.currency_id.decimal_places

            for itax in self.pool.get('account.tax').browse(cr, uid, tax_ids, context={}):
                if itax.children_tax_ids:
                    for ichild in itax.children_tax_ids:
                        tot_tax = tot_tax + (1 * abs(ichild.amount))
                else:
                    tot_tax = tot_tax + itax.amount

            new_price = amount / (1 - (tot_tax/100))
            new_price = round(new_price,decimals)

            if new_price > 0.0:
                ret = self.pool.get('account.invoice.line').write(cr, uid, invoice_line_id, {'price_unit': new_price}, context=context)
                #ret = self.pool.get('account.invoice.line')._compute_price(cr, uid, invoice_line_id, context=context)
                #ret = self.pool.get('account.invoice')._compute_amount(cr, uid, invoice_id,context=context)
                ret = self.pool.get('account.invoice').compute_taxes(cr, uid, invoice_id,context=context)

                #return {'type': 'ir.actions.act_window_close'}     #No refleja los cambios
                return {
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'account.invoice',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'domain': str([]),
                    'res_id': invoice_id,
                    'context': context,
                }
            else:
                return True



tax_inverse()
