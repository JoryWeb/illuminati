# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __odoo__.py file in root directory
##############################################################################
from odoo import api, exceptions, fields, models, _
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from collections import Counter
import odoo.addons.decimal_precision as dp
import calendar
import unicodedata
import operator
from odoo.exceptions import Warning, ValidationError
ops = {'=': operator.eq,
       '!=': operator.ne,
       '<=': operator.le,
       '>=': operator.ge,
       '>': operator.gt,
       '<': operator.lt}

ESTADO_VENTA = [
    ('draft', 'Disponible'),
    ('reserve', 'Reservado'),
    ('invoiced', 'Facturado'),
    ('done', 'Entregado'),
]

ESTADO_FINANZAS = [
    ('sin_warrant', 'Sin Warrant'),
    ('no_liberado', 'Con Warrant'),
    ('en_tramite', 'En Trámite'),
    ('liberado', 'Liberado'),
]

ESTADO_IMPORTACION = [
    ('no_nacionalizado', 'No Nacionalizado'),
    ('en_tramite', 'En Tramite'),
    ('temporal', u'Internación Temporal'),
    ('nacionalizado', 'Nacionalizado'),
]

INC_POSICION = [
    ('1', u'DELANTERA DERECHA'),
    ('2', u'PUERTA DELANTERA DERECHA'),
    ('3', u'PUERTA TRASERA DERECHA'),
    ('4', u'TRASERA DERECHA'),
    ('5', u'DELANTERA MEDIA DERECHA'),
    ('6', u'TECHO DELANTERO DERECHA'),
    ('7', u'TECHO TRASERO DERECHA'),
    ('8', u'TRASERA MEDIO DERECHA'),
    ('9', u'DELANTERA MEDIA IZQUIERDA'),
    ('10', u'TECHO DELANTERO IZQUIERDA'),
    ('11', u'TECHO TRASERO IZQUIERDA'),
    ('12', u'TRASERA MEDIO IZQUIERDA'),
    ('13', u'DELANTERA IZQUIERDA'),
    ('14', u'PUERTA DELANTERA IZQUIERDA'),
    ('15', u'PUERTA TRASERA IZQUIERDA'),
    ('16', u'TRASERA IZQUIERDA'),
]

INC_CLASIFICACION = [
    ('1', u'PINCELADO'),
    ('2', u'PINTADO PARCIAL'),
    ('3', u'PINTADO PIEZA COMPLETA'),
    ('4', u'PULIDO'),
    ('5', u'DESABOLLADO MENOR'),
    ('6', u'DESABOLLADO MAYOR'),
]

TIPO_UBICACION = [
    ('almacen', u'ALMACEN'),
    ('almacen_pds', u'ALMACEN PDS'),
    ('exposicion', u'EXPOSICIÓN'),
    ('exterior', u'EXTERIOR'),
    ('pds', u'PDS'),
    ('recinto', u'RECINTO'),
    ('show_room', u'SHOW ROOM'),
]


# class StockMove(models.Model):
#     _inherit = 'stock.move'
#
#     def check_tracking(self, cr, uid, move, ops, context=None):
#         """ Checks if serial number is assigned to stock move or not and raise an error if it had to.
#         """
#         return True

class StockLotIncidenceType(models.Model):
    _name = 'stock.lot.incidence.type'
    name = fields.Char("Nombre")


class StockLotIncidence(models.Model):
    _name = 'stock.lot.incidence'

    # Funciones para adjuntar imagenes por las incidencias
    @api.one
    @api.depends('file')
    def _get_flag(self):
        if not self.file:
            self.flag = False
        else:
            self.flag = True

    @api.one
    def _set_flag(self):
        if not self.file:
            self.flag = False

    name = fields.Char("Nombre")
    lot_id = fields.Many2one("stock.production.lot", string="Chasis")
    tipo = fields.Many2one("stock.lot.incidence.type", string=u"Tipo de Incidencia")
    recordatorio = fields.Many2one("res.users", string=u"Reportado por")
    cantidad = fields.Integer(string=u"Cantidad de Daños")
    cantidad_fabrica = fields.Integer(string=u"Cantidad Fábrica")
    cantidad_revisada = fields.Integer(string=u"Cantidad Revisada")
    posicion = fields.Selection(INC_POSICION, string=u"Posición Incidencia", default='1')
    clasificacion = fields.Selection(INC_CLASIFICACION, string=u"Clasificación", default='1')
    observaciones = fields.Text("Observaciones")
    file = fields.Many2many('ir.attachment', 'stock_lot_attachment_ir_rel', 'hr_id', 'attachment_id',
                            string=u'Adjuntar Imagen',
                            inverse="_set_flag", ondelete='cascade')
    flag = fields.Boolean('Entregado', compute="_get_flag", store=True)

    # Validamos que no puedan ser seleccionados solo creados
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if not name:
            domain = [('id', '=', False)]
        incidences = self.search(domain + args, limit=limit)
        return incidences.name_get()

    @api.multi
    def show_images(self):
        for inci in self:
            dummy, view_res = self.env['ir.model.data'].get_object_reference('poi_x_toyosa', 'view_stock_lot_incidence')
            return {
                'name': _('Imagenes Incidencia'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.lot.incidence',
                'views': [(view_res, 'form')],
                'view_id': view_res,
                'target': 'new',
                'res_id': inci.id,
            }


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def _default_invoice_dui(self):
        for lot in self:
            for invoice in self.env['account.invoice'].sudo().search([('lot_dui_id', '=', lot.id)]):
                if invoice:
                    lot.invoice_id = invoice.id
                else:
                    lot.invoice_id = False

    @api.model
    def _default_price_unit(self):
        for lot in self:
            if lot.product_id.tracking == 'serial':
                if lot.quant_ids:
                    for quant in lot.quant_ids:
                        inventory_value = quant.inventory_value
                    lot.price_unit = inventory_value
                else:
                    lot.price_unit = inventory_value

    @api.model
    def _porcentaje_pago(self):
        for lot in self:
            if lot.precio_venta and lot.precio_venta > 0:
                lot.porcentaje_pago = round((lot.pagos / lot.precio_venta) * 100, 2)
            else:
                lot.porcentaje_pago = 0

    @api.model
    def _total_pagos(self):
        payment_obj = self.env['account.payment']
        for lot in self:
            if lot.sudo().sale_line_id:
                payment_ids = payment_obj.search(
                    [('order_id', '=', lot.sudo().sale_line_id.order_id.id), ('state', '=', 'posted')])
                amount_total = 0
                if payment_ids:
                    for p in payment_ids:
                        for moves in p.move_line_ids:
                            amount_total = amount_total + moves.credit
                lot.pagos = amount_total
                # if lot.sudo().sale_line_id:
                #     for payment_line in lot.sudo().sale_line_id.invoice_lines.invoice_id.payment_move_line_ids:
                #         amount = sum(
                #             [p.amount for p in payment_line.matched_debit_ids if
                #              p.debit_move_id in lot.sudo().sale_line_id.invoice_lines.invoice_id.move_id.line_ids])
                #         lot.pagos += amount
                # else:
                #     lot.pagos = 0.0

    @api.multi
    def _total_pagos_anterior(self):
        payment_obj = self.env['account.payment']
        for lot in self:
            if lot.sudo().sale_line_id:
                today = datetime.now()
                days = calendar.monthrange(today.year, today.month)
                date_init = date(year=today.year, month=today.month, day=1)
                # date_end = date(year=today.year, month=today.month, day=int(days[1]))

                payment_ids = payment_obj.search(
                    [('order_id', '=', lot.sudo().sale_line_id.order_id.id), ('state', '=', 'posted')])
                amount_total = 0
                if payment_ids:
                    for p in payment_ids:
                        if datetime.strptime(p.payment_date, DEFAULT_SERVER_DATE_FORMAT).date() < date_init:
                            for moves in p.move_line_ids:
                                amount_total = amount_total + moves.credit
                lot.pagos_anterior = amount_total

                # for invoice_line in lot.sudo().sale_line_id.invoice_lines:
                #     for payment_line in invoice_line.invoice_id.payment_move_line_ids:
                #         amount = sum(
                #             [p.amount for p in payment_line.matched_debit_ids if
                #              p.debit_move_id in lot.sudo().sale_line_id.invoice_lines.invoice_id.move_id.line_ids])
                #         lot.pagos_anterior += amount
            else:
                lot.pagos_anterior = 0.0

    @api.multi
    def _total_pagos_mes(self):
        for lot in self:
            payment_obj = self.env['account.payment']
            if lot.sudo().sale_line_id:
                today = datetime.now()
                days = calendar.monthrange(today.year, today.month)
                date_init = date(year=today.year, month=today.month, day=1)
                # date_end = date(year=today.year, month=today.month, day=int(days[1]))

                payment_ids = payment_obj.search(
                    [('order_id', '=', lot.sudo().sale_line_id.order_id.id), ('state', '=', 'posted')])
                amount_total = 0
                if payment_ids:
                    for p in payment_ids:
                        if datetime.strptime(p.payment_date, DEFAULT_SERVER_DATE_FORMAT).date() >= date_init:
                            for moves in p.move_line_ids:
                                amount_total = amount_total + moves.credit
                lot.pagos_mes = amount_total

                # for invoice_line in lot.sudo().sale_line_id.invoice_lines:
                #     for payment_line in invoice_line.invoice_id.payment_move_line_ids:
                #         amount = sum(
                #             [p.amount for p in payment_line.matched_debit_ids if
                #              p.debit_move_id in lot.sudo().sale_line_id.invoice_lines.invoice_id.move_id.line_ids])
                #         lot.pagos_mes += amount
            else:
                lot.pagos_mes = 0.0

    @api.model
    def _total_saldo(self):
        for lot in self:
            lot.saldo = lot.precio_venta - lot.pagos

    @api.model
    def _total_saldo_anterior(self):
        for lot in self:
            lot.saldo_anterior = lot.sudo().precio_venta - lot.pagos_anterior

    @api.model
    def _total_saldo_cobrar(self):
        for lot in self:
            lot.saldo_cobrar = lot.saldo_anterior - lot.pagos_mes

    @api.model
    def _compute_plate_count(self):
        for lot in self:
            lot_plate = self.env['plate.plate'].sudo().search([('lot_id', '=', lot.id)])
            lot.lot_plate_count = len(lot_plate)

    def _default_invoice_purchase(self):
        for lot in self:
            invoice_line_obj = self.env['account.invoice.line']
            line_purchase_id = False
            move_int_id = False
            for quant in lot.quant_ids:
                for move in quant.history_ids:
                    if move.purchase_line_id:
                        line_purchase_id = move.purchase_line_id.id
                        move_int_id = move.id
                        break
            if line_purchase_id and move_int_id:
                invoice_line = invoice_line_obj.search(
                    [('purchase_line_id', '=', line_purchase_id), ('move_int_id', '=', move_int_id)], limit=1)
                lot.invoice_purchase_id = invoice_line.invoice_id.id
                lot.invoice_number = invoice_line.invoice_id.cc_nro

    @api.multi
    def reset_contract_ref(self):
        self.contract_ref = ""

    # @api.depends('sale_line_id', 'sale_line_id.order_id.order_date')
    # def _compute_contract(self):
    #     for lot in self:
    #         if lot.sale_line_id and lot.sale_line_id.order_id:
    #             if lot.sale_line_id.order_id.order_id:
    #                 lot.contract_ref = lot.sale_line_id.order_id.order_id.name
    #                 if lot.sale_line_id.order_id.order_date:
    #                     date = datetime.strptime(lot.sale_line_id.order_id.order_id.order_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    #                     lot.contract_ref = lot.sale_line_id.order_id.order_id.name +' - '+ date
    #             else:

    # @api.multi
    # @api.depends('sale_line_id', 'sale_line_id.order_id.order_date')
    # def _compute_contract(self):
    #     for lot in self:
    #         if lot.sale_line_id and lot.sale_line_id.order_id:
    #             if lot.sale_line_id.order_id.order_id:
    #                 lot.contract_ref = lot.sale_line_id.order_id.order_id.name
    #                 if lot.sale_line_id.order_id.order_date:
    #                     date = datetime.strptime(lot.sale_line_id.order_id.order_id.order_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    #                     lot.contract_ref = lot.sale_line_id.order_id.order_id.name +' - '+ date
    #             else:



    state = fields.Selection(ESTADO_VENTA, string="Estado Venta", default='draft')
    state_finanzas = fields.Selection(ESTADO_FINANZAS, string="Estado Finanzas")
    state_importaciones = fields.Selection(ESTADO_IMPORTACION, string="Estado Importaciones")
    lot_name_chasis = fields.Char("Nombre/Chasis")
    placa = fields.Char("Placa")
    soat = fields.Char("SOAT")
    n_motor = fields.Char(u"N° Motor")
    n_produccion = fields.Char(u"N° Producción")
    produccion = fields.Char(u"Producción")
    n_llaves = fields.Char(u"N° Llave")
    cant_llaves = fields.Integer(u"Cant. Llaves")

    price_unit = fields.Float(string=u"Precio", compute='_default_price_unit')
    colorinterno = fields.Many2one("color.interno", string="Color Interno")
    colorexterno = fields.Many2one("color.externo", string="Color Externo")
    anio_fabricacion = fields.Many2one("anio.toyosa", string=u"Año Fabricación")
    anio_modelo = fields.Many2one("anio.toyosa", string=u"Año Modelo")
    n_caja = fields.Integer(u"N° Caja")
    prioridad = fields.Integer(u"Prioridad de Liberación", default=1)
    prioridad_liberacion = fields.Integer(u"Prioridad Liberación", default=1)
    mot_desarmada = fields.Boolean(string=u"Motocicleta Desarmada")
    bloqueo_cif = fields.Boolean(string=u"Bloqueo por Venta CIF")
    bloqueo_venta = fields.Boolean(string=u"Bloqueo para la Venta")
    obs_bloqueo_venta = fields.Char(string=u"Observaciones de bloqueo")
    fecha_cambio = fields.Date(string=u"Fecha de Cambio")
    fecha_comprometida = fields.Date(string=u"Fecha Comprometida")
    embarque = fields.Char(string=u"Embarque")
    caso = fields.Selection(
        [('especial', 'Especial'), ('multa', 'Multa'), ('usados', 'Usados'), ('entra_sale', 'Entra y Sale')],
        string=u"Caso")
    edicion = fields.Char("ED")
    incidencia = fields.Many2many("stock.lot.incidence", string=u"Incidencia registrada")
    modelo = fields.Many2one("modelo.toyosa", string="Modelo", related='product_id.modelo', readonly=True, store=True)
    marca = fields.Many2one("marca.toyosa", related='product_id.modelo.marca', string="Marca")
    partner_id = fields.Many2one("res.partner", string=u"Cliente")
    user_id = fields.Many2one("res.users", string=u"Vendedor")
    porcentaje_pago = fields.Float("Porcentaje de Pago", compute='_porcentaje_pago')
    # El campo es actualizado en sale.py toyosa
    # Al Momento de seleccionar Lote o Guardar el pedido de ventas se guarda el id de la linea de
    # pedido de ventas hacia el lote
    sale_line_id = fields.Many2one("sale.order.line", string="Linea Pedido de Venta")
    order_line_id = fields.Many2one("purchase.order.line", string="Linea Pedido de compra", help='Divisa de compra')
    purchase_currency_id = fields.Many2one('res.currency', 'Moneda Compra',
                                           related='order_line_id.order_id.currency_id')
    purchase_price_unit = fields.Float(string='Precio Compra', related='order_line_id.price_unit',
                                       help='Precio de Compra')
    purchase_bank_id = fields.Many2one('res.bank', 'Banco', related='order_line_id.order_id.bank_id')
    # project_id = fields.Many2one("account.analytic.account", string=u"Cuenta Analítica",
    #                             related='sale_line_id.order_id.project_id', readonly=True, store=True)
    project_id = fields.Many2one("account.analytic.account", string=u"Cuenta Analítica", readonly=True, store=True)
    katashiki = fields.Many2one("katashiki.toyosa", string=u"Código modelo",
                                related='product_id.katashiki', readonly=True)
    precio_venta = fields.Monetary(string='Precio Venta', related='sale_line_id.order_id.amount_total')
    cantidad_venta = fields.Float(string='Cantidad', related='sale_line_id.product_uom_qty', required=False, store=True,
                                  digits=dp.get_precision('Product Unit of Measure'))
    descuento = fields.Float(string='% Descuento', related='sale_line_id.discount', required=False, store=True,
                             digits=dp.get_precision('Discount'))
    date_sale = fields.Date(string='Fecha', related='sale_line_id.order_id.validity_date', required=False, store=True)
    category = fields.Many2one(string='Categoría', related='product_id.categ_id', required=False, store=True)
    pagos = fields.Float(string=u"Pagos", compute='_total_pagos')
    saldo = fields.Float(string=u"Saldo", compute='_total_saldo')
    saldo_anterior = fields.Float(string=u"Saldo Anterior", compute='_total_saldo_anterior', readonly=True)
    saldo_cobrar = fields.Float(string=u"Saldo por Cobrar", compute='_total_saldo_cobrar', readonly=True)
    pagos_anterior = fields.Float(string=u"Pago Anterior", compute='_total_pagos_anterior', readonly=True)
    pagos_mes = fields.Float(string=u"Pago Mes Actual", compute='_total_pagos_mes')
    fecha_pago = fields.Date(compute='_fecha_pago', string=u"Fecha Pago", default=False)
    fecha_pago_store = fields.Date(string=u"Fecha Pago", default=False)
    mes = fields.Char(string=u"Mes")
    sucursal = fields.Many2one("stock.warehouse", string=u"Sucursal de Reserva",
                               related='sale_line_id.order_id.warehouse_id', readonly=True, store=True,
                               help="Dato de la sucursal donde el chasis ha sido reservado para la venta")

    # invoice_id = fields.One2many(
    #    comodel_name='account.invoice',
    #    inverse_name='lot_id', string='Factura Dui')
    invoice_id = fields.Many2one('account.invoice', string=u"Factura DUI", compute='_default_invoice_dui')
    imp_pol = fields.Char(string=u"Nro. Póliza Importación", related='invoice_id.imp_pol', readonly=True)
    imp_pol_manual = fields.Char(string=u"Nro. Póliza Manual")
    # Campos adicionales para ver el tramite de placas
    # lot_plate_count = fields.Integer(compute="_compute_plate_count", string='Contador de Placas', copy=False, default=0)
    lot_plate_count = fields.Integer(string='Contador de Placas', copy=False, default=0)

    discount = fields.Boolean('Descuento', compute="_compute_discount")
    invoice_purchase_id = fields.Many2one('account.invoice', string=u"Factura de Compra/Importación",
                                          help=u"Factura de compra o importaciones asignado a esta serie o chasis")
    invoice_number = fields.Char(related='invoice_purchase_id.reference', string=u'N° Factura Compra/Importación',
                                 help=u"N° de Factura de compra o importaciones asignado a esta serie o chasis")
    codigo_frv = fields.Char(string=u"Código FRV")
    uso_especial = fields.Char(string=u"Uso Especial")
    bank_id = fields.Many2one('res.bank', string="Banco")
    contract_ref = fields.Char('Contrato')
    contract_ref2 = fields.Char('Contrato2')
    current_adenda = fields.Char('Adenda Actual', readonly=True)

    # _sql_constraints = [
    #     ('name_ref_uniq', 'unique (name, product_id)',
    #      '¡La combinación de número de serie o producto tiene que ser única!'),
    # ]

    _sql_constraints = [
        ('check_name_chasis',
         "CHECK (name !~ E'[^\|\/\A-Z0-9-]')",
         _(u'Los numeros de chasis solo puede contener caracteres validos [A-Z0-9]')),
    ]

    # Afecta el performance en modo listado
    # @api.model
    # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
    #     res = super(StockProductionLot, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
    #     if 'saldo_cobrar' in fields:
    #         for line in res:
    #             if '__domain' in line:
    #                 lines = self.search(line['__domain'])
    #                 inv_value = 0.0
    #                 for line2 in lines:
    #                     inv_value += line2.saldo_cobrar
    #                 line['saldo_cobrar'] = inv_value
    #     return res

    @api.model
    def _check_contract(self):
        for l in self.search([('sale_line_id', '!=', False)]):
            ov_origin = False
            current_order = l.sale_line_id.order_id
            next_order = l.sale_line_id.order_id
            while not ov_origin:
                if next_order.order_id:
                    next_order = next_order.order_id
                else:
                    ov_origin = next_order
            if (ov_origin.id != current_order.id) and ov_origin.state == 'cancel':
                date = datetime.strptime(ov_origin.order_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                contract_ref = ov_origin.name + ' - ' + date
                ov_origin.contract_ref = contract_ref
                current_order.contract_ref = contract_ref
                l.current_adenda = current_order.name
                if current_order.state in ('sale', 'done'):
                    date = datetime.strptime(ov_origin.order_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                    contract_ref = ov_origin.name + ' - ' + date
                    l.contract_ref = contract_ref
                else:
                    l.contract_ref = ''
            elif ov_origin.id == current_order.id and ov_origin.state in ('draft', 'sent', 'cancel'):
                l.contract_ref = ''
                l.current_adenda = ''
                ov_origin.contract_ref = ''
            elif ov_origin.id == current_order.id and ov_origin.state in ('sale', 'done'):
                date = datetime.strptime(ov_origin.order_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                contract_ref = ov_origin.name + ' - ' + date
                l.contract_ref = contract_ref
                ov_origin.contract_ref = contract_ref

    @api.multi
    def _set_contract(self):
        if self.sale_line_id:
            order_id = self.sale_line_id.order_id
            if not order_id.order_id and order_id.state in ('sale', 'done'):
                date = datetime.strptime(order_id.order_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                self.contract_ref = order_id.name + ' - ' + date
                order_id.contract_ref = self.contract_ref
            elif order_id.order_id and order_id.order_id.state == 'bidding' and order_id.state in ('sale', 'done'):
                date = datetime.strptime(order_id.order_date, "%Y-%m-%d").strftime("%d/%m/%Y")
                self.contract_ref = order_id.name + ' - ' + date
                order_id.contract_ref = self.contract_ref
            elif order_id.order_id and order_id.order_id.state != 'bidding':
                self.contract_ref = order_id.contract_ref
                self.current_adenda = order_id.name

    @api.multi
    @api.depends("product_id")
    def _compute_field(self):
        for s in self:
            s.product_id.pro

    # fecha_pago_write = fields.Date(string=u"Fecha Pago", compute='_fecha_pago')

    @api.multi
    @api.depends('sale_line_id', 'sale_line_id.price_unit')
    def _fecha_pago(self):
        for lot in self:
            if lot.sudo().sale_line_id:
                fecha = ''
                payment_obj = self.env['account.payment']
                payment_ids = payment_obj.search(
                    [('order_id', '=', lot.sudo().sale_line_id.order_id.id), ('state', '=', 'posted')])
                if payment_ids:
                    for p in payment_ids:
                        fecha = p.payment_date
                if fecha != '':
                    lot.fecha_pago = fecha
                else:
                    lot.fecha_pago = False
            else:
                lot.fecha_pago = False

    #
    #
    # Definir el chasis para ser buscado
    # con nombre y ubicación de requerimiento
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = [('name', operator, name)]
        lot = self.search(domain + args, limit=limit)
        return lot.name_get()



    @api.multi
    def action_view_lot_plate(self):
        action = self.env.ref('poi_x_toyosa.plate_action_form')
        result = action.read()[0]
        res = self.env.ref('poi_x_toyosa.plate_view_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['context'] = "{'default_lot_id': %d}" % self.id
        result['domain'] = "[('lot_id','in',[" + ','.join(map(str, [self.id])) + "])]"
        return result

    @api.multi
    def action_email_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('poi_x_toyosa', 'email_template_plate')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'stock.production.lot',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Solicitud de Placas'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_email_send_nacionalizacion(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('poi_x_toyosa', 'email_template_nacionalizacion')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'stock.production.lot',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Solicitud de Nacionalización'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def show_lot(self):
        # assert len(ids) > 0
        # picking_id = self.browse(cr, uid, ids[0], context=context).picking_id.id
        for lot in self:
            # data_obj = self.pool['ir.model.data']
            # view = data_obj.xmlid_to_res_id(cr, uid, 'stock.view_picking_form')
            imd = self.env['ir.model.data']
            # action = imd.xmlid_to_object('account.action_invoice_tree1')
            # list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
            form_view_id = imd.xmlid_to_res_id('stock.view_production_lot_form')
            return {
                'name': _('Serie/Chasis'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.production.lot',
                'views': [(form_view_id, 'form')],
                'view_id': form_view_id,
                'target': 'new',
                'res_id': lot.id,
            }

    @api.multi
    def action_view_incidence(self):
        '''
        Funcion necesaria para obtener las incidencias registradas por Chasis
        '''
        # lot_ids = []
        incidence_ids = []
        for lot in self:
            incidence_ids += lot.incidencia.ids
        action = self.env.ref('poi_x_toyosa.stock_lot_incidence_action')
        result = action.read()[0]
        res = self.env.ref('poi_x_toyosa.view_stock_lot_incidence_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['domain'] = "[('id','in',[" + ','.join(map(str, incidence_ids)) + "])]"
        return result




class StockLocation(models.Model):
    _inherit = "stock.location"
    cod_ubicacion = fields.Char(string=u"Código Ubicación", size=20)
    cod_localidad = fields.Char(string=u"Código de Localidad", size=20)
    cod_antiguo = fields.Char(string=u"Código Antíguo", size=20)
    tipo_localidad = fields.Selection(TIPO_UBICACION, string=u"Tipo Ubicación Toyosa")
    visible = fields.Boolean("Visible en Lector")
    salida = fields.Boolean("Salida en Lector")

    @api.multi
    def LeerUbicaciones(self):
        location_list = []
        for location in self.env['stock.location'].search([('usage', 'in', ('internal', 'transit'))]):
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', location.id)])
            cod_localidad = ''
            for ware in warehouse:
                cod_localidad = ware.city

            unicode_char = location.complete_name
            output = unicodedata.normalize('NFKD', unicode_char).encode('ASCII', 'ignore')
            location_data = {
                'activo': location.active,
                'cod_antiguo': location.cod_antiguo or '',
                'datos_salida': location.salida,
                'departamento': warehouse.state_id.name or '',
                'id_ubic_odoo': location.id,
                'localidad': cod_localidad or '',
                'tipo': location.tipo_localidad or '',
                'ubicacion': warehouse.name or '',
                'visible': location.visible,
            }
            location_list.append(location_data)
        return location_list


class StockMove(models.Model):
    _inherit = "stock.move"
    price_unit_fob = fields.Float("Costo Unidad")
    price_flete = fields.Float("Costo Flete")
    price_seguro = fields.Float("Costo Seguro")
    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True)
    colorinterno = fields.Many2one("color.interno", string="Color Interno", copy=True, readonly=True)
    colorexterno = fields.Many2one("color.externo", string="Color Externo", copy=True, readonly=True)
    edicion = fields.Char("ED", copy=True, readonly=True)
    modelo = fields.Many2one("modelo.toyosa", string="Modelo", readonly=True, copy=True)
    marca = fields.Many2one("marca.toyosa", string="Marca", copy=True, readonly=True)

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):

        type_id = self._context.get('default_picking_type_id')
        if type_id:
            type = self.env['stock.picking.type'].browse(type_id)
            if type.code == 'outgoing':
                self = self.with_context(sale_out=True)
            else:
                self = self.with_context(sale_out=False)

        return super(StockMove, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                      submenu=submenu)

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        # Validar si viene de una compra y es serie unica
        if self.purchase_line_id and self.product_id.tracking == 'serial' and self.picking_code == 'incoming':
            n_correlativo = self.env['ir.sequence'].next_by_code('production.lot')
            produccion = str(self.purchase_line_id.order_id.n_produccion)
            self.picking_id.n_produccion = produccion
            codigo = self.origin + "|" + produccion + '-' + str(n_correlativo)
            lot_id = self.env['stock.production.lot'].create({
                'name': codigo,
                'product_id': self.product_id.id,
                'katashiki': self.purchase_line_id.katashiki.id,
                'modelo': self.purchase_line_id.modelo.id,
                'colorinterno': self.purchase_line_id.colorinterno.id,
                'colorexterno': self.purchase_line_id.colorexterno.id,
                'state_finanzas': 'sin_warrant',
                'state_importaciones': 'no_nacionalizado',
                'embarque': self.picking_id.embarque,
                'n_produccion': codigo,
                'produccion': produccion,
                'edicion': self.purchase_line_id.edicion,
                'anio_modelo': self.purchase_line_id.anio.id,
                'order_line_id': self.purchase_line_id.id,
                'bank_id': self.purchase_line_id.order_id.bank_id.id,
            })
            vals['lot_name'] = codigo
            vals['lot_id'] = lot_id.id
        return vals

    # Actualizar precio unitario
    @api.onchange('price_unit')
    def onchange_price_unit(self):
        for move in self:
            move.price_unit = move.currency_id.compute(move.price_unit_fob + move.price_flete + move.price_seguro,
                                                       self._origin.company_id.currency_id,
                                                       round=False)

    # Actualizar precio unitario
    @api.onchange('price_unit_fob')
    def onchange_price_unit_fob(self):
        for move in self:
            move.price_unit = move.currency_id.compute(move.price_unit_fob + move.price_flete + move.price_seguro, self._origin.company_id.currency_id,
                round=False)
            #move.price_unit = self._origin.company_id.currency_id.compute(move.price_unit_fob + move.price_flete + move.price_seguro, move.currency_id, round=False)
            # move.price_unit = move.price_unit_fob + move.price_flete + move.price_seguro

    @api.onchange('price_flete')
    def onchange_price_unit_flete(self):
        for move in self:
            move.price_unit = move.currency_id.compute(move.price_unit_fob + move.price_flete + move.price_seguro,
                                                       self._origin.company_id.currency_id, round=False)
            # move.price_unit = move.price_unit_fob + move.price_flete + move.price_seguro

    @api.onchange('price_seguro')
    def onchange_price_unit_seguro(self):
        for move in self:
            move.price_unit = move.currency_id.compute(move.price_unit_fob + move.price_flete + move.price_seguro,
                                                       self._origin.company_id.currency_id, round=False)
            # move.price_unit = move.price_unit_fob + move.price_flete + move.price_seguro

    @api.multi
    def write(self, vals):
        if 'price_unit' in vals and self.purchase_line_id:
            if vals.get('price_unit') <= 0:
                raise Warning('Debe registrar un costo mayor a 0')
            self.purchase_line_id.price_unit = self.company_id.currency_id.compute(vals.get('price_unit'), self.currency_id, round=False)
        result = super(StockMove, self).write(vals)
        return result

    def _unreserve_initial_demand(self, new_move):
        if self.product_id.tracking == 'serial':
            new_move = self.env['stock.move'].browse(new_move)
            new_move.write({'move_line_ids': [(4, x.id) for x in self.move_line_ids if x.qty_done == 0]})
        pass

    def _action_done(self):
        result = super(StockMove, self)._action_done()
        for line in self:
            if line.purchase_line_id and line.price_unit <= 0 and line.product_id.tracking == 'serial' and line.quantity_done > 0:
                raise Warning(_("Debe registrar un costo mayor a 0 para el producto %s") % line.product_id.name)
        return result
class StockLocationPath(models.Model):
    _inherit = 'stock.location.path'

    @api.model
    def _prepare_push_apply(self, rule, move):
        '''Inherit to write the end date of the rental on the return move'''
        vals = super(StockLocationPath, self)._prepare_push_apply(rule, move)
        vals['colorinterno'] = move.colorinterno.id
        vals['colorexterno'] = move.colorexterno.id
        vals['edicion'] = move.edicion
        vals['modelo'] = move.modelo.id
        vals['marca'] = move.marca.id
        vals['price_unit'] = move.price_unit
        return vals
