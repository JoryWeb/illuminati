##############################################################################
#
#    OpenERP, Open Source Management fSolution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp import models, fields, api, _
from openerp import SUPERUSER_ID


class ProductStockControl(models.Model):
    _name = 'product.stock.control'
    _description = 'Product Stock Control'
    _order = 'name'

    @api.one
    @api.depends('product_id')
    def _get_product_uom(self):
        self.product_uom = self.product_id.uom_id.id


    @api.onchange('product_id') # if these fields are changed, call method
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id


    name = fields.Char(string='Name')
    type = fields.Selection([('location','Location'),
                             ('company','Company')], string='Control Type')

    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Location')
    company_id = fields.Many2one('res.company', string='Company')

    product_uom = fields.Many2one('product.uom', string='Unit of Measure', compute=_get_product_uom, store=True)

    margin_calculation = fields.Selection([('manual','Manual'),
                                           ('automatic','Automatic')], string='Margin Calculation', default='manual', required=True)

    #THESE ARE THE PARAMETERS THAT ARE GOING TO HELP US TO GET QUANTITIES on MANUAL CALCULATION
    min_qty = fields.Float(string='Min. Quantity')


    #A Security percentage for Automatic and Manual margin calculation
    security_percentage = fields.Float(string='Security (%)', help=u"""Porcentaje que se introduce en cada Artículo/Almacén para incrementar el número de unidades mínimas a mantener por motivos subjetivos o externos a la aplicación. 10% modificable por el usuario.Mediante esta fórmula, el programa calcula para cada artículo en cada almacén el Stock mínimo ideal para servir al cliente de forma inmediata, pero manteniendo el stock mínimo necesario para ello, con la consiguiente reducción de costes.""")
    max_qty = fields.Float(string='Max. Quantity')
    #Automatic Parameters
    #based_on_last_months: Based on last n months
    #based_on_last_days: Based on last n days,
    #   NOTE: If you count it as days it's not real. But It's in case that user wants 90 days instead 3 months
    #   3 months is going to get (Example: April (January, February and March (April days are not going to be counted)))
    #   90 days is going to get April days too.
    #based_on_month: Based on same month of last n years #TODO!!!
    automatic_minimum_calculation = fields.Selection([('based_on_last_months', 'Based on last n months')], 'Automatic Minimum Calculation')
    automatic_period = fields.Integer('Period Calculation')
