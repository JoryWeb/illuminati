##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2004-TODAY odoo S.A. <http://www.odoo.com>
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

from odoo import models, fields, api, exceptions, _
from odoo.tools.translate import _
from datetime import datetime, timedelta


class PoiReservationWizard(models.TransientModel):
    _name = 'poi.reservation.wizard'
    _description = 'Reservar producto'

    tipo_reserva = fields.Many2one("stock.reserve.type", string=u"Tipo de reserva")
    fecha_reserva_hasta = fields.Date(string=u"Fecha Reserva hasta")
    observaciones = fields.Text(string=u"Observaciones de reserva")

    @api.model
    def default_get(self, fields):
        # if context is None: context = {}
        res = super(PoiReservationWizard, self).default_get(fields)
        lot_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')

        if not lot_ids or len(lot_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.production.lot'), 'No es el objeto seleccionado'
        lot_id, = lot_ids
        lot_res = self.env['stock.production.lot'].browse(lot_id)
        res['tipo_reserva'] = lot_res.tipo_reserva.id
        res['fecha_reserva_hasta'] = lot_res.fecha_reserva_hasta
        res['observaciones'] = lot_res.observaciones
        return res

    @api.onchange('tipo_reserva')
    def _onchange_tipo_reserva(self):
        tiempo_limite = self.env['stock.reserve.type'].browse(self.tipo_reserva.id).tiempo_limite
        fecha = datetime.now() + timedelta(days=tiempo_limite)
        self.fecha_reserva_hasta = fecha
        return

    @api.multi
    def update_reserve(self):
        """
        Actualizar el dato de la reserva y volver al parametro de reserva
        en caso de forma verificar la accion
        """

        context = self._context or {}
        line_reservation = self.env['stock.production.lot'].browse(context.get('active_ids', []))
        line_reservation.fecha_reserva_hasta = self.fecha_reserva_hasta
        line_reservation.observaciones = self.observaciones
        line_reservation.tipo_reserva = self.tipo_reserva.id
        line_reservation.reserve(self.tipo_reserva.id, self.observaciones)
        dummy, view_id = self.env['ir.model.data'].get_object_reference('poi_x_toyosa',
                                                                        'view_production_lot_toyosa')
        if self.tipo_reserva.tiempo_limite < 0:
            line_reservation._set_contract()
        if context.get('active_id'):
            lot_id = self.env['stock.production.lot'].browse(context['active_id'])
            if lot_id:
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.production.lot',
                    'type': 'ir.actions.act_window',
                    'view_id': view_id,
                    'res_id': lot_id.id,
                    'context': context
                }
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def cancel_reserve(self):
        """
        Actualizar el dato de la reserva y volver al parametro de reserva
        en caso de forma verificar la accion
        """

        context = self._context or {}
        line_lot = self.env['stock.production.lot'].browse(context.get('active_ids', []))

        line_lot.tipo_reserva = False
        line_lot.fecha_reserva_hasta = ''
        line_lot.tiempo_reserva = 0
        line_lot.observaciones = 'Cancelado por: ' + (self.observaciones or '')

        line_lot.write_lot_log(line_lot, datetime.now(), line_lot.observaciones)
        # Cancelar toda reserva en pedido de venta he inventarios
        # En caso de "Cancelar"
        dummy, view_id = self.env['ir.model.data'].get_object_reference('poi_x_toyosa',
                                                                        'view_production_lot_toyosa')
        line_lot.release()
        if context.get('active_id'):
            lot_id = self.env['stock.production.lot'].browse(context['active_id'])
            if lot_id:
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.production.lot',
                    'type': 'ir.actions.act_window',
                    'view_id': view_id,
                    'res_id': lot_id.id,
                    'context': context
                }
        return {'type': 'ir.actions.act_window_close'}
