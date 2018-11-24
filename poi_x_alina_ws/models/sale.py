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
from openerp import tools

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_ws_id = fields.Integer('Id del Perdido WS')
    order_date = fields.Date('Fecha de Pedido')
    date_delivery = fields.Date('Fecha de Entrega')
    state_delivery = fields.Selection([
        ('0', 'Anulado'),
        ('1', 'Por Preparar'),
        ('2', 'Por Autorizar'),
        ('3', 'Cargado'),
    ], string="Estado de Reserva")

    @api.model
    def item_reserve(self, compant_id='ALINA', data={}):
        items = []
        order_ws_id = False
        msj = False
        order_id = False
        if data.get('PedidoId', False):
            order_ids = self.search([('order_ws_id', '=', data.get('PedidoId', False)), ('state', '!=', 'cancel')], limit=1)
        if not order_ids:
            msj = "Reserva Creada Exitosamente"
            for i in data.get('Items', []):
                items.append((0,0,{
                    'product_id': i.get('ItemId', False),
                    'product_uom_qty': i.get('Cantidad', 0),
                    'warehouse_id': i.get('AlmacenId', ''),
                }))

            data_order = {
                'order_ws_id': data.get('PedidoId', False),
                'order_date': data.get('Pedido_Fecha', False),
                'partner_id': data.get('ClienteId', False) or default_partner_id,
                'user_id': data.get('VendedorId', False),
                'note': data.get('Comentarios', ''),
                'warehouse_id': data.get('AlmacenId', False),
                'date_delivery': data.get('FechaEntrega', False),
                'order_line': items,
                'pricelist_id': data.get('ListaPrecioId', False),
            }

            order_id = self.sudo().create(data_order)
            order_id.action_confirm()
        else:
            order_id = order_ids[0]
            msj = "El Pedido "+ str(order_id.order_ws_id) + " ya cuenta con una Reserva."

        res = {
            "Empresa": "ALINA",
            "ErrorId": False,
            "Error": False,
            "Mensaje": msj,
            "Reserva": {
                "ReservaId": order_id.id
                }
            }
        return res

    @api.model
    def update_reserve(self, company_id='ALINA', order_id=False, order_ws_id=False, reserve_action=False):
        order_ids = self.search([('id', '=', order_id),('order_ws_id', '=', order_ws_id), ('state', '!=', 'cancel')])
        for o in order_ids:
            o.state_delivery = str(reserve_action)

        res = {
            "Empresa": "ALINA",
            "ErrorId": False,
            "Error": False,
            "Mensaje": 'Reserva Actulizada Exitosamente.',
        }
        return res

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    warehouse_id = fields.Char('Codigo de Almacenes Moviles "Camiones"')
