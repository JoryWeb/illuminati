# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __odoo__.py file in root directory
##############################################################################
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning

from collections import Counter

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    edicion = fields.Char("ED")
    colorinterno = fields.Many2one("color.interno", string="Color Interno")
    colorexterno = fields.Many2one("color.externo", string="Color Externo")
    lot_name_in = fields.Char(u"N° Chasis", required=False)
    lot_name_repeat = fields.Char(u"Repetir N° Chasis", required=False)
    n_produccion = fields.Char(u"N° Producción")
    n_correlativo = fields.Char(u"Correlativo producción")
    n_llaves = fields.Char(u"Código Llave")
    cant_llaves = fields.Integer(u"Cant. Llaves")
    n_caja = fields.Integer(u"N° Caja")
    incidencia = fields.Many2many("stock.lot.incidence", string=u"Incidencia registrada")
    mot_desarmada = fields.Boolean(string=u"Armado")
    n_motor = fields.Char(u"N° Motor")

    @api.onchange('lot_name_in', 'lot_id')
    def onchange_serial_number_two(self):
        """ When the user is encoding a move line for a tracked product, we apply some logic to
        help him. This includes:
            - automatically switch `qty_done` to 1.0
            - warn if he has already encoded `lot_name` in another move line
        """
        res = {}
        if self.product_id.tracking == 'serial':
            if not self.qty_done:
                self.qty_done = 1

            message = None
            if self.lot_name_in or self.lot_id:
                move_lines_to_check = self._get_similar_move_lines_two() - self
                if self.lot_name_in:
                    counter = Counter(move_lines_to_check.mapped('lot_name_in'))
                    if counter.get(self.lot_name_in) and counter[self.lot_name_in] > 1:
                        message = _(
                            'No puede usar el mismo número de serie dos veces. Corrija los números de serie codificados')
                elif self.lot_id:
                    counter = Counter(move_lines_to_check.mapped('lot_id.id'))
                    if counter.get(self.lot_id.id) and counter[self.lot_id.id] > 1:
                        message = _(
                            'No puede usar el mismo número de serie dos veces. Por favor, corrija los números de serie codificados.')

            if message:
                res['warning'] = {'title': _('Warning'), 'message': message}
        return res

    def _get_similar_move_lines_two(self):
        self.ensure_one()
        lines = self.env['stock.move.line']
        picking_id = self.move_id.picking_id if self.move_id else self.picking_id
        if picking_id:
            lines |= picking_id.move_line_ids.filtered(lambda ml: ml.product_id == self.product_id and (ml.lot_id or ml.lot_name_in))
        return lines

    # Intervenimos la funcion _action_done para actualizar los lotes con los datos de chasis
    def _action_done(self):
        """ This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and unreserve if needed in the source
        location.

        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move (that's what the override of `write` here
        is done.
        """
        for ml in self:
            if ml.lot_name_in == ml.lot_name_repeat:
                if ml.lot_id and ml.lot_name_in and ml.product_id.tracking == 'serial':
                    ml.lot_id.name = ml.lot_name_in
                    ml.lot_id.lot_name_chasis = ml.lot_name
                    ml.lot_id.edicion = ml.move_id.edicion
                    ml.lot_id.colorinterno = ml.move_id.colorinterno.id
                    ml.lot_id.colorexterno = ml.move_id.colorexterno.id
                    ml.lot_id.n_llaves = ml.n_llaves
                    ml.lot_id.cant_llaves = ml.cant_llaves
                    ml.lot_id.n_caja = ml.n_caja
                    ml.lot_id.mot_desarmada = ml.mot_desarmada
                    ml.lot_name = ml.lot_name_in
                    ml.lot_id.embarque = ml.picking_id.embarque
                    for incidence in ml.incidencia:
                        ml.lot_id.incidencia = [(4, incidence.id)]
                        for incid in ml.lot_id.incidencia:
                            incid.lot_id = ml.lot_id.id
            else:
                raise ValidationError(_(
                    'El numero de chasis "%s" no esta igual que el repetido') % ml.lot_name_in)

        super(StockMoveLine, self)._action_done()

# class StockPackOperationLot(models.Model):
#     _inherit = "stock.pack.operation.lot"
#     name_lot = fields.Char(u"Nombre N° Serie", required=False)
#     name_lot_repeat = fields.Char(u"Repetir nombre N° Serie", required=False)
#     n_produccion = fields.Char(u"N° Producción")
#     n_correlativo = fields.Char(u"Correlativo producción")
#     edicion = fields.Char("ED")
#     colorinterno = fields.Many2one("color.interno", string="Color Interno")
#     colorexterno = fields.Many2one("color.externo", string="Color Externo")
#     n_llaves = fields.Char(u"Código Llave")
#     cant_llaves = fields.Integer(u"Cant. Llaves")
#     n_caja = fields.Integer(u"N° Caja")
#     incidencia = fields.Many2many("stock.lot.incidence", string=u"Incidencia registrada")
#     mot_desarmada = fields.Boolean(string=u"Armado")
#     n_motor = fields.Char(u"N° Motor")
#     tracking = fields.Selection(related="operation_id.product_id.tracking", string="Seguimiento", store=True)
#     price_unit = fields.Float("Precio unitario")
#     # #Validar recurrencia al hacer clic sobre el simbolo mas
#     # @api.multi
#     # def write(self, vals):
#     #     cadena = "%s,%s" % ('stock.pack.operation.lot', self.id)
#     #     fecha = datetime.utcnow() - timedelta(seconds=1)
#     #     values = {
#     #         cadena: fecha.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#     #     }
#     #     self = self.with_context(__last_update=values)
#     #     return super(StockPackOperationLot, self).write(vals)
#
#     @api.onchange('name_lot_repeat')
#     def onchange_name_lot_repeat(self):
#         if self.operation_id.product_id.tracking in ('serial', 'lot'):
#             if self.name_lot != self.name_lot_repeat:
#                 return {'value': {}, 'warning': {'title': 'Advertencia!',
#                                                  'message': ('Los registro de chasis "%s" no son iguales, verifique' % (
#                                                      self.name_lot))}}
#
#     @api.onchange('lot_id')
#     def onchange_lot_id(self):
#         if self.lot_id:
#             self.n_motor = self.lot_id.n_motor
#             self.n_llaves = self.lot_id.n_llaves
#             self.edicion = self.lot_id.edicion
#             self.colorinterno = self.lot_id.colorinterno.id
#             self.colorexterno = self.lot_id.colorexterno.id
#
#     @api.multi
#     def actualizar_chasis(self, operation_id):
#         oper = operation_id
#         context = self._context
#         return 'Se conecto'
#
#
#     @api.multi
#     def do_plus(self):
#         if self.operation_id.product_id.tracking == 'serial':
#             if self.qty >= 1:
#                 raise Warning('El chasis ya esta confirmado, cierre la actual ventana y vuelva  a abrir')
#         res = super(StockPackOperationLot, self).do_plus()
#         return res

