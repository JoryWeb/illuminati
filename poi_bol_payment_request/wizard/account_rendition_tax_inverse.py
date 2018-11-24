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

from odoo import models, fields, api, _

class TaxInverseWizard(models.TransientModel):
    _name = 'poi_bol_rendition.tax_inverse.wizard'
    _description = "Cálculo precio inverso"


    amount = fields.Float('Precio efectivo', required=True, help="Monto a ser calculado despues de aplicar los Impuestos del caso. Setear el precio para llegar a tal monto.")

    @api.multi
    def action_update_price(self):
        if self.env.context.get('rendition_invoice_id', False):
            rendition_invoice_id = self.env.context.get('rendition_invoice_id')
        else:
            return True

        for data in self.read():

            amount = data['amount']

            new_price = 0.0
            tot_tax = 0.0

            iline = self.env['account.expenses.rendition.invoice'].browse(rendition_invoice_id)[0]

            rendition_id = iline.rendition_id.id
            decimals = iline.rendition_id.currency_id.decimal_places

            for itax in iline.taxes_ids:
                if itax.children_tax_ids:
                    for ichild in itax.children_tax_ids:
                        tot_tax = tot_tax + (1 * abs(ichild.amount))
                else:
                    tot_tax = tot_tax + itax.amount

            new_price = amount / (1 - (tot_tax/100))
            new_price = round(new_price,decimals)

            if new_price > 0.0:
                iline.write({'amount': new_price})
                return {
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'account.expenses.rendition',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'domain': str([]),
                    'res_id': rendition_id,
                    'context': context,
                }
            else:
                return True
