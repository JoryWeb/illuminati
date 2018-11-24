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

from openerp import models, fields, api

import openerp.addons.decimal_precision as dp


# Partida arancelaria se aplica a importaciones como exportaciones
# Se lo vuelve generico para cualquiero de los dos modulos
class PartidaArancelaria(models.Model):
    _name = 'partida.arancelaria'
    name = fields.Char("Nombre")


class product(models.Model):
    _inherit = 'product.template'

    @api.one
    def _get_last_purchase(self):
        """ Buscar el último precio con el que se compró el item
            En caso de no encontrar facturas, usar el campo alternativo que se puede usar para cargas iniciales"""

        last_purch_price = 0.0
        if self.company_id:
            self.env.cr.execute("""select il.price_unit,i.currency_id
                        from account_invoice_line il inner join account_invoice i on il.invoice_id = i.id
                        where i.type = 'in_invoice' and i.state not in ('draft','proforma')
                        and il.product_id = %s and il.company_id = %s  
                        order by i.date_invoice,i.id desc limit 1""", (self.id, self.company_id.id))
        else:
            self.env.cr.execute("""select il.price_unit,i.currency_id
                        from account_invoice_line il inner join account_invoice i on il.invoice_id = i.id
                        where i.type = 'in_invoice' and i.state not in ('draft','proforma')
                        and il.product_id = %s   
                        order by i.date_invoice,i.id desc limit 1""", (self.id,))
        rs = self.env.cr.fetchone()
        last_purch_price = rs and rs[0] or 0.0

        if not last_purch_price:
            last_purch_price = self.last_purch_price_init
        self.last_purch_price = last_purch_price

    last_purch_price = fields.Float(compute="_get_last_purchase", method=True, digits=dp.get_precision('Account'),
                                    string=u"�~Zltimo precio de Compra", readonly=False)
    last_purch_price_init = fields.Float('UPC inicial', digits=dp.get_precision('Account'), readonly=False,
                                         help=u"Campo opcional sólo para carga inicial de último precio de compra migrado desde otro sistema")
    old_code = fields.Char(u'Código antíguo', size=64, required=False, readonly=False)
    ice = fields.Float("Alicuota ICE", digits=dp.get_precision('Account'),
                       help=u"Alicuota específica ICE (Bs./UdM). Aplica para el cálculo de impuestos sobre el Item")
    partida = fields.Many2one("partida.arancelaria", "Partida Arancelaria")
    _defaults = {
        'valuation': 'real_time',
    }
