# -*- encoding: utf-8 -*-
##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2011 Poiesis Consulting (<http://www.poiesisconsulting.com>). All Rights Reserved.
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from osv import osv
from osv import fields

import decimal_precision as dp

class invoice(osv.osv):
    """ Description """
    _inherit = 'account.invoice'

    _columns = {
        'discount_global': fields.float('Descuento Global (%)', readonly=True, states={"draft":[["readonly",False]]}, digits_compute= dp.get_precision('Discount')),
    }

    def _copy_global_discount(self, cr, uid, ids, context=None):
        
        line_obj = self.pool.get('account.invoice.line')
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.discount_global:
                disc_glob = inv.discount_global
                line_ids = []
                for line in inv.invoice_line:
                    line_ids.append(line.id)
                line_obj.write(cr, uid, line_ids, {'discount': disc_glob}, context=context)
    
    def button_reset_taxes(self, cr, uid, ids, context=None):
        
        self._copy_global_discount(cr, uid, ids, context=context)
        return super(invoice,self).button_reset_taxes(cr, uid, ids, context)
    
    def action_move_create(self, cr, uid, ids, context=None):
        
        self._copy_global_discount(cr, uid, ids, context=context)
        return super(invoice,self).action_move_create(cr, uid, ids, context)
    
invoice()

class invoice_line(osv.osv):
    """ Description """
    _inherit = 'account.invoice.line'
    #, address_invoice_id=False
    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None, discount_global=False):
        
        ret_values = super(invoice_line, self).product_id_change(cr, uid, ids, product, uom, qty, name, type, partner_id, fposition_id, price_unit, currency_id, context, company_id)
        
        if discount_global:
            ret_values['value']['discount'] = discount_global
                
        return ret_values  

invoice_line()
