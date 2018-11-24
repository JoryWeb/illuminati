##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013 Camptocamp SA
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

from odoo import api, exceptions, fields, models, _
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, Warning
import operator
ops = {'=': operator.eq,
       '!=': operator.ne,
       '<=': operator.le,
       '>=': operator.ge,
       '>': operator.gt,
       '<': operator.lt}

class StockReserveType(models.Model):
    _name = 'stock.reserve.type'
    name = fields.Char("Nombre")
    fecha_reserva = fields.Date("Fecha reserva hasta")
    tiempo_limite = fields.Integer(string=u"N° de Dias Permitidos")
    tiempo_aviso = fields.Integer(string=u"N° de Dias de Aviso")
    monto_minimo = fields.Float(string=u'Monto Mínimo Permitido', required=True, digits=dp.get_precision('Product Price'))
    descripcion = fields.Text(string=u'Descripción')
    recordatorio = fields.Many2one("res.users", string=u"Usuario de Recordatorio")

class StockProductionLot(models.Model):
    """ Allow to reserve products.

    The fields mandatory for the creation of a reservation are:

    * product_id
    * product_uom_qty
    * product_uom
    * name

    The following fields are required but have default values that you may
    want to override:

    * company_id
    * location_id
    * location_dest_id

    Optionally, you may be interested to define:

    * date_validity  (once passed, the reservation will be released)
    * note
    """
    _inherit = 'stock.production.lot'
    _description = 'Reserva de Lotes'
    #_inherit = ['mail.thread']

    @api.one
    @api.depends('fecha_reserva_hasta')
    def _compute_day(self):
        """
        Requerimos saber el numero de dias restantes
        para la reserva a partir de la fecha actual
        Al actualizar la fecha_reserva_hasta se actualiza el valor
        En todo caso el cron jobs ayuda a actualizar el campo
        """
        fmt = '%Y-%m-%d'
        from_date = fields.Date.context_today(self)
        to_date = self.fecha_reserva_hasta
        if to_date:
            d1 = datetime.strptime(from_date, fmt)
            d2 = datetime.strptime(to_date, fmt)
            self.tiempo_reserva = (d2 - d1).days

    @api.model
    def _compute_log_count(self):
        for lot in self:
            lot_log = self.env['poi.stock.reservation.lot.log'].search([('lot_id', '=', lot.id)])
            lot.lot_log_count = len(lot_log)

    @api.model
    def _compute_payment_count(self):
        for lot in self:
            lot_log = self.env['chasis.payment.history.report'].search([('lot_id', '=', lot.id)])
            lot.lot_payment_count = len(lot_log)

    @api.multi
    def _search_log_count(self, operator, value):
        if operator not in ops.keys():
            raise exceptions.Warning(
                _('Search operator %s not implemented for value %s')
                % (operator, value)
            )
        found_ids = []
        self.env.cr.execute("""
        select lot_id from poi_stock_reservation_lot_log group by lot_id
                """)
        for lot_id in self.env.cr.fetchall():
            found_ids.append(lot_id[0])

        return [('id', 'in', found_ids)]

    observaciones = fields.Text(string=u"Observaciones de reserva")
    tipo_reserva = fields.Many2one("stock.reserve.type", string=u"Tipo de reserva")
    fecha_reserva_hasta = fields.Date(string=u"Fecha Reserva hasta", default=fields.Date.context_today)
    tiempo_reserva = fields.Integer(string=u"Tiempo de reserva", compute=_compute_day, store=True)
    date_reserve = fields.Date('Fecha Registro de Reserva')
    titular_reserva = fields.Many2one("res.partner", string="Titular de Reserva")
    responsable_reserva = fields.Many2one("res.users", string="Responsable de Reserva")
    amount = fields.Monetary(string='Monto Adelantado', help="Es requerido definir un monto adelantado por el cliente para poder reservar el chasis")
    currency_id = fields.Many2one('res.currency', string='Moneda',
                                  default=lambda self: self.env.user.company_id.currency_id)

    lot_log_count = fields.Integer(compute="_compute_log_count", search="_search_log_count", string='Contador de Logs', copy=False, default=0)
    #lot_payment_count = fields.Integer(compute="_compute_payment_count", string='Contador de Pagos', copy=False, default=0)
    lot_payment_count = fields.Integer(string='Contador de Pagos', copy=False)

    #Al crear una reserva
    # @api.model
    # def create(self, vals):
    #     lot_id = super(StockProductionLot, self.with_context(mail_create_nolog=True)).create(vals)
    #     self.write_lot_log(lot_id, lot_id.fecha_reserva_hasta)
    #     return lot_id

    # reserve actualiza y pone en confirm un movimiento de inventar
    # o siemplemente cambia el estado del chasis
    @api.multi
    def reserve(self, tipo_reserva_id, observaciones):
        """
        En cualquiera de los casos reservar puede
        conllevar a actualizar el movimiento de stock
        para que sea reservado
        Para el caso de Lotes se puede actualizar el estado de reserva
        pero se debe implicar ver si la venta esta asignada a este
        numero de serie
        """
        for lot_id in self:
            if lot_id.state in ('reserve'):
                self.write_lot_log(lot_id, lot_id.fecha_reserva_hasta, observaciones)
                return False
            if tipo_reserva_id and lot_id.state in ('draft', 'reserve'):
                tiempo_limite = self.env['stock.reserve.type'].browse(tipo_reserva_id).tiempo_limite
                fecha = datetime.now() + timedelta(days=tiempo_limite)
                # ACtualizar parametros de lote chasis con los campos enviados
                lot_id.fecha_reserva_hasta = fecha
                lot_id.tipo_reserva = tipo_reserva_id
                lot_id.tiempo_limite = tiempo_limite
                lot_id.observaciones = observaciones
                # Escribimos al resposanble de reserva
                # No importa si es de compra o algun vendedor
                lot_id.responsable_reserva = self._uid
                lot_id.date_reserve = fields.Date.context_today(self)
                self.write_lot_log(lot_id, fecha, observaciones)
            if lot_id.state in ('draft', 'reserve'):
                lot_id.state = 'reserve'
        # No tiene sentido bloquerlo por
        # ventas ya que es un campo manual
        self.bloqueo_venta = True
        return True

    @api.multi
    def get_state_reserve(self):
        """
        Verficar el estado indefinido de un chasis y su estado
        """
        for lot_id in self:
            if lot_id.state in ('invoiced', 'done'):
                return 'reservado'
            elif lot_id.tipo_reserva.tiempo_limite < 0 and lot_id.state in ('invoiced', 'done', 'reserve'):
                return 'reservado_ilimitado'
            else:
                return 'borrador'

    @api.multi
    def release(self):
        """
        Release moves y quants reservados en pedidos de venta
        """
        if self.state in ('invoiced', 'done'):
            raise UserError('El chasis ya se encuentra facturado o entregado')
        for lot in self:
            for quant in lot.quant_ids:
                if quant.location_id.usage == 'internal':
                    for history_move in quant.history_ids:
                        if history_move.state != 'done':
                            history_move.action_cancel()

        self.state = 'draft'
        self.user_id = False
        self.partner_id = False
        self.sale_line_id = False
        self.observaciones = ''
        self.bloqueo_venta = False
        self.tipo_reserva = False
        self.tiempo_reserva = 0

        #self.mapped('move_id').action_cancel()
        return True

    @api.model
    def write_lot_log(self, lot_id, date, observaciones=''):
        if lot_id and date:
            values = {
                'lot_id': lot_id.id,
                'observaciones': observaciones,
                'tipo_reserva': lot_id.tipo_reserva.id,
                'fecha_reserva_hasta': date,
                'tiempo_reserva': lot_id.tiempo_reserva,
                'titular_reserva': lot_id.titular_reserva.id,
                'responsable_reserva': lot_id.responsable_reserva.id,
                'amount': lot_id.amount,
                'currency_id': lot_id.currency_id.id,
            }
            self.env['poi.stock.reservation.lot.log'].create(values)

    @api.model
    def update_tiempo_reserva(self, ids=None):
        """
        Requerimos saber el numero de dias restantes
        para la reserva a partir de la fecha actual
        Es necesario actualizar el campo
        tiempo_reserva para poder ser buscable en la base de datos
        el proceso se ejecuta con un cron jobs
        """
        lot_reserve = self.env['stock.production.lot'].search([('fecha_reserva_hasta', '>=', fields.date.today())])

        for lot_res in lot_reserve:
            fmt = '%Y-%m-%d'
            from_date = fields.Date.context_today(self)
            to_date = lot_res.fecha_reserva_hasta
            d1 = datetime.strptime(from_date, fmt)
            d2 = datetime.strptime(to_date, fmt)
            lot_res.tiempo_reserva = (d2 - d1).days

            # En caso de que los dias de reserva sean menores a cero se aplica liberar el chasis
            if lot_res.tiempo_reserva <= 0:
                if lot_res.state not in ('invoiced', 'done'):
                    notification = _('Tiempo de reserva superado, puede volver a generar otra OV para reservar la unidad seleccionada')
                    lot_res.sale_line_id.order_id.message_post(body=notification, message_type="notification", subtype="sale.order")
                    # En caso de liberar la reserva escribir en el log
                    values = {
                        'lot_id': lot_res.id,
                        'observaciones': 'Unidad liberada para reservar',
                        'tipo_reserva': lot_res.tipo_reserva.id,
                        'fecha_reserva_hasta': datetime.now(),
                        'tiempo_reserva': 0,
                        'titular_reserva': lot_res.partner_id.id,
                        # Esta definido para que sea el vendedor el que sea responsable de reserva
                        'responsable_reserva': lot_res.user_id.id,
                        'amount': 0,
                        'currency_id': False,
                    }
                    self.env['poi.stock.reservation.lot.log'].create(values)
                    lot_res.release()

            # El sistema enviara los correos de aviso a los usuario configurados en los tipos de reserva
            if lot_res.tiempo_reserva <= lot_res.tipo_reserva.tiempo_limite:
                body_html = "<table style='width:100%;border: 1px solid black;border-collapse: collapse;'>" \
                            "<tr><td>Chasis</td>" \
                            "<td>Dias Restantes</td>" \
                            "<td>Fecha Expiración</td></tr>"
                body_tr = ''
                body_tr = body_tr + "<tr><td>" + str(lot_res.name) + "</td>" \
                                              "<td>" + str(lot_res.tiempo_reserva) + "</td>" \
                                              "<td>" + str(lot_res.fecha_reserva_hasta) + "</td></tr>"
                body_html = body_html + body_tr + "</table>"
                user_id = self._uid
                usuario = self.env['res.users'].browse(user_id)
                # Solo si existe un responsable de reserva asignado se le podrá enviar la notificación
                #if lot_res.responsable_reserva:
                    # Falta verificar a que usuario se le enviaran las notificaciones
                #    usuario.message_post(body="<p>Reservas Chasis por Expirar</p>" + body_html, partner_ids=[lot_res.responsable_reserva.partner_id.id],
                #                         model='mail.channel', subject='',
                #                         message_type='comment', subtype_is=1)


        return True

    @api.multi
    def open_move(self):
        self.ensure_one()
        action = self.env.ref('stock.action_move_form2')
        action_dict = action.read()[0]
        action_dict['name'] = _('Reservation Move')
        # open directly in the form view
        view_id = self.env.ref('stock.view_move_form').id
        action_dict.update(
            views=[(view_id, 'form')],
            res_id=self.move_id.id,
            )
        return action_dict

    @api.multi
    def action_view_lot_log(self):
        action = self.env.ref('poi_x_toyosa.action_poi_stock_reservation_lot_log_tree')
        result = action.read()[0]
        res = self.env.ref('poi_x_toyosa.view_poi_stock_reservation_lot_log_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['context'] = "{'default_lot_id': %d}" % self.id
        result['domain'] = "[('lot_id','in',[" + ','.join(map(str, [self.id])) + "])]"
        return result

    @api.multi
    def action_view_lot_payment(self):
        action = self.env.ref('poi_x_toyosa.action_chasis_payment_history_report_all')
        result = action.read()[0]
        res = self.env.ref('poi_x_toyosa.view_chasis_payment_history_report_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['context'] = "{'default_lot_id': %d}" % self.id
        result['domain'] = "[('lot_id','in',[" + ','.join(map(str, [self.id])) + "])]"
        return result

class PoiStockReservationLotLog(models.Model):
    _name = 'poi.stock.reservation.lot.log'
    lot_id = fields.Many2one("stock.production.lot", string="Lote")
    observaciones = fields.Char(string=u"Observaciones de reserva")
    tipo_reserva = fields.Many2one("stock.reserve.type", string=u"Tipo de reserva")
    fecha_reserva_hasta = fields.Date(string=u"Fecha Reserva hasta")
    tiempo_reserva = fields.Integer(string=u"Tiempo de reserva")
    titular_reserva = fields.Many2one("res.partner", string="Titular de Reserva")
    responsable_reserva = fields.Many2one("res.users", string="Responsable de Reserva")
    amount = fields.Monetary(string='Monto Adelantado',
                             help="Es requerido definir un monto adelantado por el cliente para poder reservar el chasis")
    currency_id = fields.Many2one('res.currency', string='Moneda',
                                  default=lambda self: self.env.user.company_id.currency_id)
