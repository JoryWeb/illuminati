#########################################################################
#                                                                       #
# Copyright (C) 2015  Agile Business Group                              #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU Affero General Public License as        #
# published by the Free Software Foundation, either version 3 of the    #
# License, or (at your option) any later version.                       #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU Affero General Public Licensefor more details.                    #
#                                                                       #
# You should have received a copy of the                                #
# GNU Affero General Public License                                     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#                                                                       #
#########################################################################
import logging
from openerp import fields, models, api, _
from openerp.exceptions import Warning, ValidationError


_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pay_type_id = fields.Many2one('sale.order.pay', string='Forma de Pago')
    delivery_time_id = fields.Many2one('sale.order.delivery', string="Tiempo de Entrega")
    destination = fields.Text('Destination', default="Presente.-")

class SaleOrderPay(models.Model):
    _name = 'sale.order.pay'

    name = fields.Char('Tipo')
    html = fields.Text('Datos')

class SaleOrderDelivery(models.Model):
    _name = 'sale.order.delivery'

    name = fields.Char('Tiempo de Entrega')
