
from odoo import api, fields, exceptions, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning
from odoo.tools.float_utils import float_compare
from  odoo import fields as f2
import odoo.addons.decimal_precision as dp

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    _authmode = True
    # JG Campos de Ventas
    order_id = fields.Many2one('sale.order', 'Cotizacion de Venta', readonly=True)
    sale_type_id = fields.Many2one('sale.type', 'Tipo de Venta', related="order_id.sale_type_id", readonly=True)
    nit_flag = fields.Boolean('nit check', related="sale_type_id.edit_nit", readonly=True)
    razon_flag = fields.Boolean('razon flag', related="sale_type_id.edit_razon", readonly=True)
    cc_dos_lock = fields.Boolean('Dosicacion Cerrada', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacén', compute="_get_warehouse", store=True)

    n_produccion = fields.Char(u"Número de producción")
    fecha_produccion = fields.Datetime(u"Fecha de producción")
    fecha_salida = fields.Datetime(u"Fecha de salida")
    fecha_llegada = fields.Datetime(u"Fecha de llegada")
    activity_id = fields.Many2one("company.activity", string=u"Actividad económica",
                                  related='cc_dos.activity_id', readonly=True, store=True)
    lot_id = fields.Many2one('stock.production.lot', 'lote', compute="_compute_lot_id", store=True)
    copia = fields.Integer('Copia N#', default=0)
    skip_order = fields.Boolean('Omitir Orden', help=u"Campo flag para omitir la validación de forzar OVs para cada factura. No visible en interfaz de usuario. En principio pensado para cargas masivas.")
    # Campos para dosificación
    # Actualizar factura con datos de importaciones

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoice, self).default_get(fields)
        if res.get('type', False) and res.get('type') == 'out_invoice':
            res.update({'date_invoice': f2.Date.today()})
        return res

    @api.multi
    @api.depends('order_id')
    def _compute_lot_id(self):
        for s in self:
            if s.order_id and s.order_id.lot_id and s.order_id.lot_id.id:
                s.lot_id = s.order_id.lot_id.id
                break
    # Todo: Refactorizar para todos los productos
    # def _prepare_invoice_line_from_po_line(self, line):
    #     if line.product_id.purchase_method == 'purchase':
    #         qty = line.product_qty - line.qty_invoiced
    #     else:
    #         qty = line.qty_received - line.qty_invoiced
    #     if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
    #         qty = 0.0
    #     taxes = line.taxes_id
    #     invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
    #     invoice_line = self.env['account.invoice.line']
    #     data = {}
    #     if qty > 0:
    #         data = {
    #             'purchase_line_id': line.id,
    #             'name': line.name,
    #             'origin': self.purchase_id.origin,
    #             'uom_id': line.product_uom.id,
    #             'product_id': line.product_id.id,
    #             'account_id': invoice_line.with_context(
    #                 {'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
    #             'price_unit': line.order_id.currency_id.compute(line.price_unit, line.order_id.currency_id, round=False),
    #             'quantity': qty,
    #             'discount': 0.0,
    #             'account_analytic_id': line.account_analytic_id.id,
    #             'invoice_line_tax_ids': invoice_line_tax_ids.ids,
    #             'segment_id': line.product_id.segment_id.id,
    #         }
    #         if line.colorinterno or line.colorexterno or line.edicion:
    #             data['colorinterno'] = line.colorinterno.id
    #             data['colorexterno'] = line.colorexterno.id
    #             data['edicion'] = line.edicion
    #         account = invoice_line.get_invoice_line_account('in_invoice', line.product_id,
    #                                                         self.purchase_id.fiscal_position_id,
    #                                                         self.env.user.company_id)
    #         for line_move in line.move_ids.sorted(key=lambda l: l.id):
    #             if line_move.state == 'done':
    #                 self.n_embarque = line_move.picking_id.embarque
    #                 self.nombre_embarque = line_move.picking_id.barco
    #                 self.fecha_salida = line.order_id.date_order
    #                 self.fecha_llegada = line_move.date_expected
    #         if account:
    #             data['account_id'] = account.id
    #
    #         # Como la factura se tiene que generar desde el FOB del picking tenemos que obtener ese dato
    #         moves = self.env['stock.move'].search([('purchase_line_id', '=', line.id), ('state', '=', 'done')])
    #         for move in moves.sorted(key=lambda l: l.id):
    #             data['price_unit'] = line.order_id.currency_id.compute(move.price_unit, line.order_id.currency_id, round=False)
    #             # Registramos el id de stock.move del cual se genera la factura
    #             data['move_int_id'] = move.id
    #
    #     return data

    # Load all unsold PO lines
    #Todo refactorizar para crear facturas de importacion
    # @api.onchange('purchase_id')
    # def purchase_order_change(self):
    #     if not self.purchase_id:
    #         return {}
    #     if not self.partner_id:
    #         self.partner_id = self.purchase_id.partner_id.id
    #
    #     new_lines = self.env['account.invoice.line']
    #     for line in self.purchase_id.order_line:
    #         # Load a PO line only once
    #         if line in self.invoice_line_ids.mapped('purchase_line_id'):
    #             continue
    #         data = self._prepare_invoice_line_from_po_line(line)
    #         if data:
    #             new_line = new_lines.new(data)
    #             new_line._set_additional_fields(self)
    #             new_lines += new_line
    #
    #     self.invoice_line_ids += new_lines
    #     self.n_produccion = self.purchase_id.n_produccion
    #     self.fecha_produccion = self.purchase_id.date_order
    #     self.purchase_id = False
    #     return {}

    @api.multi
    @api.depends('order_id', 'state')
    def _get_warehouse(self):
        for s in self:
            if s.order_id and s.type == 'out_invoice':
                s.warehouse_id = s.order_id.warehouse_id.id

    @api.multi
    def invoice_validate(self):
        for lines in self.invoice_line_ids:
            if self.type == 'in_invoice':
                if not lines.account_analytic_id:
                    raise exceptions.Warning(_('Cuenta analítica sin asignar en una linea de la factura de compra'))
                if not lines.invoice_line_tax_ids and lines.invoice_id.tipo_fac == '1':
                    raise exceptions.Warning(_('Una o varias lineas de la factura no tiene asignado el impuesto'))
                if lines.purchase_line_id:
                    moves = self.env['stock.move'].search(
                        [('purchase_line_id', '=', lines.purchase_line_id.id), ('state', '=', 'done')])
                    for move in moves:
                        for move in move.move_line_ids:
                            if move.lot_id:
                                if not move.lot_id.invoice_purchase_id:
                                    move.lot_id.invoice_purchase_id = self.id
            if lines.product_id.categ_id.activity_id and lines.product_id.categ_id.activity_id.id != self.activity_id.id and self.type == 'out_invoice':
                raise UserError(_(
                    'El producto %s no pertence a la actividad económica que esta tratando de validar') % lines.product_id.name_template)


            if lines.lot_id and self.type == 'out_invoice':
                if self.sale_type_id.car_released and lines.lot_id.state_finanzas != 'liberado':
                    raise Warning(
                        'El Vehiculo no se encuentra Liberado su estado es %s' % (lines.lot_id.state_finanzas))
                if self.sale_type_id.nationalized_car and lines.lot_id.state_importaciones != 'nacionalizado':
                    raise Warning('El Vehiculo no se encuentra Nacionalizado su estado es %s' % (
                    lines.lot_id.state_importaciones))
        if self.type in ('in_invoice', 'in_refund') and self.reference:
            if self.search([('type', '=', self.type), ('reference', '=', self.reference), ('company_id', '=', self.company_id.id), ('commercial_partner_id', '=', self.commercial_partner_id.id), ('id', '!=', self.id)]):

                self.env.cr.execute("""
                    SELECT
                        copia
                    FROM
                        account_invoice
                    WHERE
                        type = '%s'
                        and reference = '%s'
                        and commercial_partner_id = %s
                        and id != %s
                    order by copia desc
                    limit 1
                    """ % (self.type, self.reference, self.commercial_partner_id.id, self.id))
                copia = self.env.cr.fetchone()[0] or 0
                self.copia = copia + 1
                self.reference = self.reference + ' Copia ' + str(copia)

        if self.type == 'out_invoice':
            # if not (self.cc_dos and self.cc_dos.sale_type_id and self.cc_dos.sale_type_id.id == self.sale_type_id.id):
            #     raise Warning('El tipo de Venta Difiere con el parametrizado en la dosificacion')
            if self.order_id:
                res = super(AccountInvoice, self).invoice_validate()
                if self.lot_id:
                    self.lot_id.state = 'invoiced'
                if self.sale_type_id.plate_procesing != 'without_plate':
                    self.order_id.plate_flag = True
                return res
            elif self.skip_order:
                return super(AccountInvoice, self).invoice_validate()
            else:
                # Verificar si se trata de una Orden de trabajo
                if self.env['workshop.order'].search([('invoice_id', '=', self.id)]):
                    super(AccountInvoice, self).invoice_validate()
                    work_shop = self.env['workshop.order'].search([('invoice_id', '=', self.id)])
                    for work in work_shop:
                        if work.invoice_porcentaje >= 100:
                            work.state = 'invoiced'
                else:
                    raise Warning('No se puede crear una factura sin una orden de Venta previamente creada.')
        else:
            res = super(AccountInvoice, self).invoice_validate()

    @api.multi
    def action_invoice_open(self):
        if self.type == 'out_invoice':
            if self.order_id:
                auth = self.check_authorization(code='account.invoice.min.advanced')
                if auth:
                    super(AccountInvoice,self).action_invoice_open()
            else:
                if self.env['workshop.order'].search([('invoice_id', '=', self.id)]) or self.skip_order:
                    super(AccountInvoice, self).action_invoice_open()
                else:
                    raise Warning('No se puede crear una Factura de Venta sin una Oden de Venta previamente creada.')
        else:
            super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def on_authorized(self):
        code = self.auth_log_id.auth_id.code
        res = super(AccountInvoice, self).on_authorized()
        if code == 'account.invoice.min.advanced':
            self.action_invoice_open()

    @api.multi
    def on_rejected(self):
        code = self.auth_log_id.auth_id.code
        res = super(AccountInvoice, self).on_rejected()
        if code == 'account.invoice.min.advanced':
            return True


    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.env.context.get('default_payment_term_id', False) and self.type == 'in_invoice' and not self.partner_id.property_supplier_payment_term_id:
            self.payment_term_id = self.env.context.get('default_payment_term_id', False)
        return res

    # @api.onchange('currency_id')
    # def _onchange_currency_id(self):
    #     if self.currency_id:
    #         for line in self.invoice_line_ids.filtered(lambda r: r.purchase_line_id):
    #             if not line.account_analytic_id:
    #                 raise exceptions.Warning(
    #                     _('No valid distribution type.'))
    #             line.price_unit = line.purchase_id.currency_id.compute(line.purchase_line_id.price_unit,
    #                                                                    self.currency_id, round=False)



class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    lot_id = fields.Many2one('stock.production.lot', 'Chasis', copy=False, readonly=True)
    reserve_type = fields.Many2one('stock.reserve.type', 'Tipo de Reserva', related="lot_id.tipo_reserva",
                                   readonly=True)
    colorinterno = fields.Many2one("color.interno", string="Color Int")
    colorexterno = fields.Many2one("color.externo", string="Color Ext")
    edicion = fields.Char("ED")
    tipo_fac = fields.Selection(string=u"Tipo Factura",
                                related='invoice_id.tipo_fac', readonly=True)

    move_int_id = fields.Char(string=u"Move Id")
    price_subtotal_with_tax2 = fields.Float('Precio total con Impuestos', digits=dp.get_precision('Product Price'), compute="_compute_price2")


    @api.multi
    def _compute_price2(self):
        for s in self:
            s.price_subtotal_with_tax2 = s.price_subtotal_with_tax
