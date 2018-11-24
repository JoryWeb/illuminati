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
from odoo import fields, models, api, _
from odoo.exceptions import Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from lxml import etree
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta, date

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _authmode = True

    @api.multi
    @api.depends("state", "amount_total", "amount_total_a")
    def _compute_amount_total_plus_a(self):
        for s in self:
            if s.currency_id and s.currency_report_id:
                s.amount_total_plus_a = s.amount_total + s.amount_total_a


    @api.multi
    @api.depends("state", "amount_total", "amount_total_a")
    def _compute_amount_total_plus_a_exchange(self):
        for s in self:
            if s.currency_id and s.currency_report_id:
                s.amount_total_plus_a_exchange = s.currency_id.compute((s.amount_total + s.amount_total_a), s.currency_report_id)

    @api.multi
    @api.depends("amount_total_a", "currency_report_id")
    def _compute_amount_total_a_exchange(self):
        for s in self:
            s.amount_total_a_exchange = s.currency_id.compute(s.amount_total_a, s.currency_report_id)
            s.amount_total_plus_a_exchange = 0

    order_line_a = fields.One2many('sale.order.line.a', 'order_id', 'Accesorios')

    @api.multi
    @api.depends("amount_total_a", "discount_amount", "currency_report_id")
    def _compute_subtotal_exchange(self):
        for s in self:
            s.subtotal_exchange = s.amount_total_plus_a + s.discount_amount

    @api.multi
    @api.depends("amount_total_plus_a")
    def _compute_residual_pay(self):
        for s in self:
            if s.opportunity_id and s.opportunity_id.id:
                 s.residual_pay = s.amount_total_plus_a - s.opportunity_id.initial_fee
            else:
                s.residual_pay = s.amount_total_plus_a

    order_date = fields.Date('Fecha', readonly=True)
    order_type_id = fields.Many2one(
        string="Tipo de Cotizacion",
        comodel_name="sale.order.type",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    sale_type_id = fields.Many2one(
        string="Tipo de Venta",
        comodel_name="sale.type",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    insurance = fields.Boolean('Con Seguro', default=False, readonly=True, states={'draft': [('readonly', False)]})
    file_complete = fields.Boolean('File Completo', default=False)

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sale Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('cancel_reasig', 'Cancelado y Reasignado'),
        ('bidding', 'Licitacion'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    sales_ids = fields.Many2many('sale.order', string="Cotizaciones", compute="_get_sales", readonly=True, copy=False)
    bidding_sale = fields.Boolean('Licitacion', compute="_get_default_vals")
    # Autorizaciones
    discount_flag = fields.Boolean('Descuento Aprobado', default=False, readonly=True, copy=False)
    discount_check = fields.Boolean('Circuito de Autoriacion de Descuento',  compute="_get_default_vals")

    amount_advanced = fields.Float('Pago Inicial Ref.', readonly=True, states={'draft': [('readonly', False)]})
    currency_advance_id = fields.Many2one('res.currency', "Moneda Ref.", readonly=True, states={'draft': [('readonly', False)]})

    # Acciones Inmediatas y Bloqueos
    edit_discount = fields.Boolean('Editar Descuento', default=True)
    price_flag = fields.Boolean('Editar Precio', default=False)
    reserve_flag = fields.Boolean('Reserva?', compute="_compute_reserve")


    # Valores por Defecto
    partner_flag = fields.Boolean('Contacto por Defecto', default=False)
    pricelist_flag = fields.Boolean('Lista de precio Por defecto', default=False)
    cc_dos_flag = fields.Boolean('Dosificacion por Defecto', default=False)
    dealsheet_line = fields.One2many('sale.order.dealsheet', 'order_id', 'Dealsheet')
    dealsheet_flag = fields.Boolean('Dealsheet Flag', compute="_get_default_vals")
    chasis_flag = fields.Boolean('Chasis Flag', default=False)
    confirm_sale = fields.Boolean('Confirmar Venta', default=False, copy=False)
    plate_id = fields.Many2one('plate.plate', 'Tramite de Placa', readonly=True, copy=False)
    plate_flag = fields.Boolean('Tramite de Placas', default=False, copy=False)
    plate_procesing = fields.Selection(
        selection=[
            ('valid_invoice', 'Realizar al Validar la Factura.'),
            ('without_plate', 'Sin tramite.'),
            ],
    string='Estado de Placas', compute="_get_default_vals")

    biddings = fields.Char('Nro. de Licitacion')
    cuce = fields.Char('Nro. de Cuce')

    sale_count = fields.Integer('Ventas Registradas', default=0, compute='_get_nsales')
    sales_ids = fields.Many2many('sale.order', compute="_compute_sales_advanced", string='Licitaciones', copy=False)
    order_id = fields.Many2one('sale.order', 'Orden de Venta', copy=False)
    lot_id = fields.Many2one('stock.production.lot', 'lote', compute="_compute_lot_id", store=True)
    lot_line_id = fields.Many2one('sale.order.line', 'Linea de Pedido', compute="_compute_lot_id")
    price_unit = fields.Float('Precio', compute="_compute_lot_id")
    discount_percent = fields.Float('Porcentaje de Descuento', compute="_compute_lot_id")
    discount_amount = fields.Float('Monto del Descuento', compute="_compute_lot_id")
    price_total = fields.Float('Precio total', compute="_compute_lot_id")

    invoice_proccess = fields.Boolean('Facturar', default=False)
    check_chasis_pre = fields.Boolean('Validar Chasis pre-facturacion', default=False, compute="_get_default_vals")

    # campos para los Accesorios
    amount_total_a = fields.Float('Monto Total Accesorios',  digits=dp.get_precision('Product Price'), store=True, readonly=True, track_visibility='always', compute="_amount_all_a")
    amount_total_price_unit_a = fields.Float('Precio Unitario Total Accesorios',  digits=dp.get_precision('Product Price'), store=True, readonly=True, track_visibility='always', compute="_amount_all_a")
    amount_total_tax_a = fields.Float('Total Impuestos Accesorios',  digits=dp.get_precision('Product Price'), store=True, readonly=True, track_visibility='always', compute="_amount_all_a")
    amount_total_untaxed_a = fields.Float('Base Imponible Accesorios', compute="_amount_all_a")

    amount_total_plus_a = fields.Float(string='Total Parcial', readonly=True, compute='_compute_amount_total_plus_a', track_visibility='always', help="Este monto es de uso solamente informativo y  representa el total de los accesorios + el costo del Vehiculo.", digits=dp.get_precision('Product Price'))

    amount_total_plus_a_exchange = fields.Float(string='Total Parcial cambio', readonly=True, compute='_compute_amount_total_plus_a_exchange', track_visibility='always', help="Este monto es de uso solamente informativo y  representa el total de los accesorios + el costo del Vehiculo.", digits=dp.get_precision('Product Price'))

    amount_total_a_exchange = fields.Float('Monto Total Accesorios',  digits=dp.get_precision('Product Price'), store=True, readonly=True, track_visibility='always', compute="_compute_amount_total_a_exchange")

    subtotal_exchange = fields.Float('Monto Total Accesorios',  digits=dp.get_precision('Product Price'), readonly=True, track_visibility='always', compute="_compute_subtotal_exchange")

    residual_pay = fields.Float('Monto Total-Cuota Inicial',  digits=dp.get_precision('Product Price'), readonly=True, track_visibility='always', compute="_compute_residual_pay")

    contract_ref = fields.Char('Contrato', readonly=True, copy=False)


    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def create(self, vals):
        saletype_obj = self.env['sale.type']
        type_id = vals.get('sale_type_id', False)

        if type_id:
            type_id = saletype_obj.browse(type_id)
        if type_id.partner_id:
            vals.update({'partner_id': type_id.partner_id.id})
        if type_id.pricelist_id and not vals.get('insurance', False):
            vals.update({'pricelist_id': type_id.pricelist_id.id})
        elif type_id.pricelist_insurance_id and vals.get('insurance', False):
            vals.update({'pricelist_id': type_id.pricelist_insurance_id.id})
        result = super(SaleOrder, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        saletype_obj = self.env['sale.type']
        type_id = vals.get('sale_type_id', False)
        if type_id:
            type_id = saletype_obj.browse(type_id)
        elif self.sale_type_id:
            type_id = self.sale_type_id
        if type_id and type_id.partner_id:
            vals.update({'partner_id': type_id.partner_id.id})
        if type_id and type_id.pricelist_id and not vals.get('insurance', False):
            vals.update({'pricelist_id': type_id.pricelist_id.id})
        elif type_id and type_id.pricelist_insurance_id and vals.get('insurance', False):
            vals.update({'pricelist_id': type_id.pricelist_insurance_id.id})
        result = super(SaleOrder, self).write(vals)
        return result

    @api.multi
    @api.depends("sale_type_id")
    def _get_default_vals(self):
        for s in self:
            if s.sale_type_id and s.sale_type_id.id:
                s.bidding_sale = s.sale_type_id.bidding_sale
                s.discount_check = s.sale_type_id.discount_flag
                s.dealsheet_flag = s.sale_type_id.dealsheet_flag
                s.plate_procesing = s.sale_type_id.plate_procesing
                s.check_chasis_pre = s.sale_type_id.check_chasis_pre
            if s.check_chasis_pre:
                s.invoice_proccess = False
            else:
                s.invoice_proccess = True

    @api.multi
    @api.depends("payment_count")
    def _compute_reserve(self):
        for s in self:
            s.reserve_flag = False
            if s.sale_type_id.booking == 'advanced':
                if s.payment_advanced_ids:
                    s.reserve_flag = True

    @api.onchange("insurance", "sale_type_id")
    def _onchange_insurance(self):
        vals = {}
        pricelist_id = False
        if self.insurance:
            if self.sale_type_id.pricelist_insurance_id and  self.sale_type_id.pricelist_insurance_id.id:
                pricelist_id = self.sale_type_id.pricelist_insurance_id.id
            elif self.sale_type_id.pricelist_id and self.sale_type_id.pricelist_id.id:
                pricelist_id = self.sale_type_id.pricelist_id.id
        elif self.sale_type_id.pricelist_id and self.sale_type_id.pricelist_id.id:
            pricelist_id = self.sale_type_id.pricelist_id.id
        if pricelist_id:
            self.pricelist_id = pricelist_id
            vals['domain'] = {
                "pricelist_id": [("id", "=", pricelist_id)],
            }

        return vals

    @api.multi
    def action_reserve(self):
        for line in self.order_line:
            if line.lot_id and line.lot_id.state == 'draft':
                reserve = line.lot_id.reserve(self.sale_type_id.booking_type_id.id, self.name)
                if not reserve:
                    raise Warning('El chasis Se encuentra Reservado')
                else:
                    # recien al confirmar se escriben los datos del cliente
                    # en el chasis
                    line.lot_id.write({'user_id': line.order_id.user_id.id})
                    line.lot_id.write({'partner_id': line.order_id.partner_id.id})
                    line.lot_id.write({'sale_line_id': line.id})
                break
            elif  line.lot_id and line.lot_id.state != 'draft':
                raise Warning('El chasis Se encuentra Reservado')


    @api.multi
    def action_plate(self):
        if self.plate_flag:
            dummy, view_id = self.env['ir.model.data'].get_object_reference('poi_x_toyosa', 'plate_view_form_wiz')
            return {
                'name':_("Tramite de Placas"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'plate.plate',
                'type': 'ir.actions.act_window',
                'search_view_id': False,
                #'target': 'new',
                'context': {
                    'default_order_id': self.id,
                }
            }
        else:
            raise Warning('Se debe Haber Confirmado la Factura antes de Continuar con el Tramite de Placas.')


    @api.multi
    def action_check_chasis(self):
        f1 = False
        f2 = False
        if self.sale_type_id.check_chasis:
            for lines in self.order_line:
                if lines.lot_id:
                    if self.sale_type_id.car_released and lines.lot_id.state_finanzas not in ('liberado', 'sin_warrant'):
                        raise Warning('El Vehiculo no se encuentra Liberado/Sin Warrant su estado es %s' % (lines.lot_id.state_finanzas))
                    else:
                        f1 = True
                    if self.sale_type_id.nationalized_car and lines.lot_id.state_importaciones != 'nacionalizado':
                        raise Warning('El Vehiculo no se encuentra Nacionalizado su estado es %s' % (lines.lot_id.state_importaciones))
                    else:
                        f2 = True
            if f1 and f2:
                self.invoice_proccess = True
        else:
            self.invoice_proccess = True

    @api.onchange("sale_type_id")
    def _onchange_sale_type_id(self):
        vals = {}
        if self.sale_type_id.partner_id:
            self.partner_flag = True
            self.partner_id = self.sale_type_id.partner_id.id
        else:
            self.partner_flag = False

        if self.sale_type_id.pricelist_id or self.sale_type_id.pricelist_insurance_id:
            self.pricelist_flag = True
            if self.insurance:
                self.pricelist_id = self.sale_type_id.pricelist_insurance_id
            else:
                self.pricelist_id = self.sale_type_id.pricelist_id
        else:
            self.pricelist_flag = False

        self.order_line = False
        if self.sale_type_id.paymemt_term_ids and self.sale_type_id.paymemt_term_ids.ids:
            vals['domain'] = {
                "payment_term_id": [("id", "in", self.sale_type_id.paymemt_term_ids.ids)],
            }
        return vals

    @api.multi
    def lot_required(self):
        lot = False
        if self.sale_type_id.chasis_flag:
            for line in self.order_line:
                if line.lot_id:
                    lot = True
            if not lot:
                raise Warning('Error de Validacion: Es Necesario Tener un chasis en la order de Venta para llevar a cabo la confirmacion.')

    @api.multi
    def sum_total_price_accesory(self):
        for line in self.order_line:
            line.price_total += self.amount_total_a
        self.amount_untaxed += self.amount_total_untaxed_a
        self.amount_tax += self.amount_total_tax_a
        self.amount_total += self.amount_total_a
        return self


    @api.multi
    def action_flag_discount(self):
        self.lot_required()
        auth = True
        if self.discount_check and not self.discount_flag:
            if not self.sale_type_id.auth_id:
                raise Warning("No se parametrizo el circuito de descuento en el Tipo de Venta.")
            else:
                auth = self.check_authorization(code=self.sale_type_id.auth_id.code)
                if auth and not self.discount_flag:
                    self.discount_flag = True
                    if self.sale_type_id.booking == 'discount':
                        self.action_reserve()
                elif self.discount_flag:
                    if self.sale_type_id.booking == 'discount':
                        self.action_reserve()

            return auth

    @api.multi
    #@api.depends('payment_count')
    def _compute_sales_advanced(self):
        sale_obj = self.env['sale.order']
        for s in self:
            sales_ids = sale_obj.search([('order_id', '=', s.id)])
            s.sales_ids = sales_ids

    @api.multi
    @api.depends('order_line')
    def _compute_lot_id(self):
        for s in self:
            for line in s.order_line:
                if line.lot_id:
                    s.lot_id = line.lot_id
                    s.lot_line_id = line.id
                    s.price_unit = line.price_unit
                    s.discount_percent = line.discount
                    s.price_total = line.price_total
                    s.discount_amount = line.currency_id.compute((line.price_unit - line.price_total), line.order_id.currency_report_id)
                    break


    @api.multi
    def _get_nsales(self):
        for s in self:
            s.sale_count = s.env['sale.order'].search_count([('order_id', '=', s.id)])


    @api.multi
    def action_view_sales(self):
        sales_ids = self.mapped('sales_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders')
        list_view_id = imd.xmlid_to_res_id('sale.view_order_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(sales_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % sales_ids.ids
        elif len(sales_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = sales_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    @api.multi
    def action_confirm(self):
        self.lot_required()
        self.order_date = fields.Date.today()
        if not self.partner_id.ci and not self.partner_id.nit:
            raise Warning(_('El cliente seleccionado no tiene NIT o CI'))
        if self.sale_type_id.bidding_sale and not self.order_id:
            for line in self.order_line:
                for n in range(int(line.product_uom_qty)):
                    #new_id = self.copy(context=self.env.context)
                    new_id = self.copy()
                    new_id.order_id = self.id
                    for nl in new_id.order_line:
                        if line.lot_id.id == nl.lot_id.id:
                            nl.price_unit = line.price_unit
                            nl.discount = line.discount
                            nl.amount_discounted = line.amount_discounted
                            nl.price_total = line.price_total
                            # recien al confirmar se escriben los datos del cliente
                            # en el chasis
                            line.lot_id.write({'user_id': line.order_id.user_id.id})
                            line.lot_id.write({'partner_id': line.order_id.partner_id.id})
                            line.lot_id.write({'sale_line_id': line.id})
                        else:
                            nl.unlink()
                    # new_id.order_line.unlink()
                    # new_id.order_id = self.id
                    # new_id.order_line = [(0,0,{
                    # 'product_id': line.product_id.id,
                    # 'lot_id': (line.lot_id and line.lot_id.id) or False,
                    # 'product_uom_qty': 1,
                    # 'order_id': new_id.id,
                    # 'price_unit': line.price_unit,
                    # 'product_uom': line.product_uom.id})]
            self.state = 'bidding'
            return

        # self = self.sum_total_price_accesory()
        self.confirm_sale = True
        # CHANGED: el siguiente bloque confirmaba el contracto
        # if self.order_id and self.order_id.state != 'bidding' and not self.contract_ref:
        #     date = datetime.strptime(self.order_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        #     self.contract_ref = self.name +' - '+ date
        # elif not self.order_id:
        #     date = datetime.strptime(self.order_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        #     self.contract_ref = self.name +' - '+ date
        # if self.order_id and self.order_id.state != 'bidding' and self.lot_id:
        #     self.lot_id.contract_ref = self.contract_ref
        #     self.lot_id.current_adenda = self.name
        # elif not self.order_id and self.lot_id:
        #     self.lot_id.contract_ref = self.contract_ref
        if not self.discount_flag and self.discount_check:
            auth = self.action_flag_discount()
            if auth:
                super(SaleOrder, self).action_confirm()
                if self.sale_type_id.booking == 'sale':
                    self.action_reserve()
                if self.opportunity_id and self.opportunity_id.id:
                    self.opportunity_id.action_set_won()
        elif not (self.discount_flag):
            super(SaleOrder, self).action_confirm()
            if self.sale_type_id.booking == 'sale':
                self.action_reserve()
                self.discount_flag = True
            if self.opportunity_id and self.opportunity_id.id:
               self.opportunity_id.action_set_won()
        elif self.discount_flag:
            super(SaleOrder, self).action_confirm()
            if self.sale_type_id.booking == 'sale':
                self.action_reserve()
                self.discount_flag = True
            if self.opportunity_id and self.opportunity_id.id:
                self.opportunity_id.action_set_won()



    @api.multi
    def on_authorized(self):
        code = self.auth_log_id.auth_id.code
        res = super(SaleOrder, self).on_authorized()
        if code == self.sale_type_id.auth_id.code:
            self.action_flag_discount()
            if self.confirm_sale:
                self.action_confirm()

    @api.multi
    def on_rejected(self):
        code = self.auth_log_id.auth_id.code
        res = super(SaleOrder, self).on_authorized()
        if code == self.sale_type_id.auth_id.code:
            self.discount_flag = False
            self.confirm_sale = False
            self.state = 'cancel'


    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        inv_ids = super(SaleOrder, self).action_invoice_create(grouped=grouped, final=final)
        invoice_obj = self.env['account.invoice']
        for r in invoice_obj.browse(inv_ids):
            r.order_id = self.id
            r.nit = (r.partner_id.nit and r.partner_id.nit != '0' and r.partner_id.nit) or r.partner_id.ci or ''
            r.date_invoice = fields.Date.today()
            for line in r.invoice_line_ids:
                if line.sale_line_ids[0].lot_id:
                    line.lot_id = line.sale_line_ids[0].lot_id.id

        return inv_ids

    @api.multi
    @api.depends("sales_bidding")
    def _compute_field(self):
        for s in self:
            pass

    @api.onchange('order_type_id')
    def _onchange_product_id_set_lot_domain(self):
        if self.order_type_id:
            self.sale_type_id = False
            return {
                'domain': {'sale_type_id': [('id', 'in', self.order_type_id.sale_type_ids.ids)]}
            }


    @api.multi
    def action_cancel(self):
        # No es necesario que ingrese dos veces a tratar de liberar
        # Se movio sobre el archivo sale_cancel.py
        if self.env.context.get('signal', False):
            res = super(SaleOrder, self).action_cancel()
        else:
            return {
                'name':_("Motivo de Cancelacion"),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'sale.order.cancel.wiz',
                'type': 'ir.actions.act_window',
                'search_view_id': False,
                'target': 'new',
            }

    @api.depends('order_line_a.price_total')
    def _amount_all_a(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_price_unit = 0.0
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line_a:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_price_unit += line.price_unit
            order.update({
                'amount_total_price_unit_a': amount_price_unit,
                'amount_total_a': amount_untaxed + amount_tax,
                'amount_total_untaxed_a': amount_untaxed,
                'amount_total_tax_a': amount_tax,
            })

    @api.onchange("order_line")
    def _onchange_order_line(self):
        if not self.order_line:
            self.order_line_a = False

    @api.onchange("pricelist_id")
    def _onchange_pricelist_id(self):
        for line in self.order_line:
            if self.pricelist_id and self.partner_id:
                product_id = line.product_id
                product = product_id.with_context(
                    year_id= (line.edicion and line.edicion.id) or False,
                    lang=self.partner_id.lang,
                    partner=self.partner_id.id,
                    quantity=line.product_uom_qty,
                    date_order=self.date_order,
                    pricelist=self.pricelist_id.id,
                    uom=line.product_uom.id,
                )
                price_unit = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, line.tax_id)
                line.price_unit = price_unit

    @api.model
    def _install_sale(self):
        """remove from action sale orden de facturacion."""
        if self.env['ir.values'].search([('name', '=', 'Invoice Orders')]):

            self.env.ref('sale.sale_order_line_make_invoice').unlink()

    @api.model
    def _install_search_invoice_missed(self):
        sale_ids = self.env['sale.order'].search([('state', 'in', ['sale', 'done', 'cancel',  'bidding'])])
        for s in sale_ids:
            for i in s.invoice_ids:
                if not i.order_id:
                    i.order_id = s.id

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    modelo = fields.Many2one("modelo.toyosa", "Modelo")
    katashiki = fields.Many2one("katashiki.toyosa", u"Código de Modelo")
    colorinterno = fields.Many2one("color.interno", string="Color Interno")
    colorexterno = fields.Many2one("color.externo", string="Color Externo")
    edicion = fields.Many2one("anio.toyosa", "Año")
    price_flag = fields.Boolean('Precio Editable')
    discount_flag = fields.Boolean('Descuento editable', compute="_compute_lot_flag")
    discount_approve = fields.Boolean('Descuento Aprobado', related="order_id.discount_flag")
    lot_flag = fields.Boolean('Lote requerrido?', compute="_compute_lot_flag")
    sale_type_id = fields.Many2one('sale.type', related="order_id.sale_type_id")

    # Accesorios
    amount_total_a = fields.Float('Total Accesorios', digits=dp.get_precision('Product Price'), readonly=True, track_visibility='always', compute="_compute_amount_total_a", store=True)

    @api.multi
    @api.depends("order_id.order_line_a")
    def _compute_amount_total_a(self):
        for s in self:
            s.amount_total_a = s.order_id.amount_total_a


    @api.one
    @api.depends("product_id")
    def _compute_lot_flag(self):
        #self.lot_flag = self.sale_type_id.chasis_flag
        self.price_flag = self.sale_type_id.edit_price
        self.discount_flag = self.sale_type_id.edit_discount


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}
        year_id = False
        if self.lot_id:
            pricelist_id = False
            if self.order_id.pricelist_id:
                pricelist_id = self.order_id.pricelist_id.id
            lot_id = self.lot_id
            year_id = (lot_id.anio_modelo and lot_id.anio_modelo.id) or False
        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.category_id.id != self.product_uom.category_id.id):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
            year_id=year_id,
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)
        return {'domain': domain}


    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom:
            self.price_unit = 0.0
            return
        year_id = False
        if self.lot_id:
            pricelist_id = False
            if self.order_id.pricelist_id:
                pricelist_id = self.order_id.pricelist_id.id
            lot_id = self.lot_id
            year_id = (lot_id.anio_modelo and lot_id.anio_modelo.id) or False
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                year_id=year_id,
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date_order=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)


    @api.onchange('product_id')
    def _onchange_product_id_set_lot_domain(self):
        vals = {}
        lot_obj = self.env['stock.production.lot']

        if self.product_id and self.product_id.id:
            if self.lot_id and self.lot_id.product_id.id == self.product_id.id:
                domain_str = [('bloqueo_venta', '=', False), ('bloqueo_cif', '=', False), ('state', '=', 'draft'), ('product_id', '=', self.product_id.id)]
                lot_ids = lot_obj.search(domain_str)
                vals['domain'] = {
                    "lot_id": [("id", "in", lot_ids.ids)],
                }
                return vals
            self.lot_id = False
            self.colorinterno = False
            self.colorexterno = False
            self.modelo = (self.product_id.modelo and self.product_id.modelo.id) or False
            domain_str = [('bloqueo_venta', '=', False), ('bloqueo_cif', '=', False), ('state', '=', 'draft'), ('product_id', '=', self.product_id.id)]
            lot_ids = lot_obj.search(domain_str)
            vals['domain'] = {
                "lot_id": [("id", "in", lot_ids.ids)],
            }
        else:
            domain_str = [('bloqueo_venta', '=', False), ('bloqueo_cif', '=', False), ('state', '=', 'draft')]
            lot_ids = lot_obj.search(domain_str)


            vals['domain'] = {
                "lot_id": [("id", "in", lot_ids.ids)],
            }

        return vals

    #lot_id = fields.Many2one(
    #    'stock.production.lot', 'Lot', copy=False)
    # TODO: Bloque posiblemente para remover
    # @api.onchange('lot_id')
    # def _on_change_price_unit(self):
    #     if self.order_id.pricelist_id and self.order_id.partner_id and self.order_id.price_flag:
    #         product = self.product_id.with_context(
    #             lang=self.order_id.partner_id.lang,
    #             partner=self.order_id.partner_id.id,
    #             quantity=self.product_uom_qty,
    #             date_order=self.order_id.date_order,
    #             pricelist=self.order_id.pricelist_id.id,
    #             uom=self.product_uom.id,
    #             fiscal_position=self.env.context.get('fiscal_position')
    #         )
    #         self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
    #         return {
    #             'warning':
    #             {
    #                'title': _("Atencion"),
    #                'message': _('Usted no puede modifcar el precio del producto'),
    #             }
    #         }

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        #self.lot_flag = self.sale_type_id.chasis_flag
        lot = self.env['stock.production.lot']
        if self.lot_id:
            pricelist_id = False
            if self.order_id.pricelist_id:
                pricelist_id = self.order_id.pricelist_id.id
            year_id = False
            lot_id = self.lot_id
            year_id = (lot_id.anio_modelo and lot_id.anio_modelo.id) or False
            product_uom_qty = self.product_uom_qty
            self.colorinterno = (self.lot_id.colorinterno and self.lot_id.colorinterno.id) or False
            self.colorexterno = (self.lot_id.colorexterno and self.lot_id.colorexterno.id) or False
            self.edicion = (self.lot_id.anio_modelo and self.lot_id.anio_modelo.id) or False
            self.modelo = (self.lot_id.modelo and self.lot_id.modelo.id) or False
            if not self.product_id and not self.product_id.id:
                self.product_id = (self.lot_id.product_id and self.lot_id.product_id.id) or False


            if self.order_id.pricelist_id and self.order_id.partner_id:
                product_id = self.product_id
                product = product_id.with_context(
                    year_id=year_id,
                    lang=self.order_id.partner_id.lang,
                    partner=self.order_id.partner_id.id,
                    quantity=product_uom_qty,
                    date_order=self.order_id.date_order,
                    pricelist=pricelist_id,
                    uom=self.product_uom.id,
                    fiscal_position=self.env.context.get('fiscal_position')
                )
                price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
                self.price_unit = price_unit
        # Se se actualiza la linea del pedido de ventas
        # Actualizar el dato del lote
        # 07022018 no tiene sentido actualizar los datos de chasis al cotizar
        # if self._origin:
        #     lot_search = lot.search([('sale_line_id', '=', self._origin.ids[0])])
        #     for lot_data in lot_search:
        #         if lot_data.location_id:
        #             if lot_data.location_id.usage == 'internal':
        #                 lot_data.write({'sale_line_id': False})
        #                 lot_data.write({'modelo': False})
        #                 lot_data.write({'marca': False})
        #                 lot_data.write({'user_id': False})
        #                 lot_data.write({'partner_id': False})
        #     for line in self:
        #         if line.lot_id:
        #             #line.lot_id.project_id = line.order_id.project_id.id
        #             line.lot_id.write({'modelo': line.modelo.id})
        #             line.lot_id.write({'marca': line.modelo.marca.id})
        #             line.lot_id.write({'user_id': line.order_id.user_id.id})
        #             line.lot_id.write({'partner_id': line.order_id.partner_id.id})
        #             line.lot_id.write({'sale_line_id': self._origin.ids[0]})

    @api.onchange("discount")
    def _onchange_discount(self):

        if not self.product_id:
            return
        else:
            if self.lot_id:
                product_obj = self.env['product.template.discount']
                if self.lot_id.anio_modelo:
                    discount_ids = product_obj.search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id), ('year_id', '=', self.lot_id.anio_modelo.id), ('discount', '=', True)], limit=1)
                    if not discount_ids:
                        return super(SaleOrderLine, self)._onchange_discount()
                    else:
                        self.amount_discounted = 0.0
                        self.discount = 0.0
                        return  {'warning': {
                            'title': _('Alerta'),
                            'message': _('El Chasis no puede llevar Descuento.')
                        }}
                else:
                    self.amount_discounted = 0.0
                    self.discount = 0.0
                    return  {'warning': {
                        'title': _('Alerta'),
                        'message': _('El Chasis No tiene Año para comprobar su Descuento.')
                    }}
            else:
                super(SaleOrderLine, self)._onchange_discount()



    # Actualizar datos de lote al guardar
    @api.model
    def create(self, vals):
        lot = self.env['stock.production.lot']
        res_id = super(SaleOrderLine, self).create(vals)
        if vals.get('order_id', False):
            order_id = self.env['sale.order'].browse(vals.get('order_id'))
            if not order_id.sale_type_id.edit_price:
                if vals.get('product_id', False) or vals.get('lot_id', False):
                    pricelist_id = False
                    year_id = False
                    if vals.get('lot_id', False):
                        lot_obj = self.env['stock.production.lot']
                        lot_id = lot_obj.browse(vals['lot_id'])
                        year_id = (lot_id.anio_modelo and lot_id.anio_modelo.id)or False

                    if vals.get('pricelist_id', False):
                        pricelist_id = vals['pricelist_id']
                    else:
                        pricelist_id = res_id.order_id.pricelist_id.id
                    if vals.get('product_uom_qty', False):
                        product_uom_qty = vals['product_uom_qty']
                    else:
                        product_uom_qty = res_id.product_uom_qty
                    if res_id.order_id.pricelist_id and res_id.order_id.partner_id:
                        if vals.get('product_id', False):
                            product_obj = self.env['product.product']
                            product_id = product_obj.browse(vals['product_id'])
                        else:
                            product_id = res_id.product_id
                        product = product_id.with_context(
                            year_id=year_id,
                            lang=res_id.order_id.partner_id.lang,
                            partner=res_id.order_id.partner_id.id,
                            quantity=product_uom_qty,
                            date_order=res_id.order_id.date_order,
                            pricelist=pricelist_id,
                            uom=res_id.product_uom.id,
                            fiscal_position=res_id.env.context.get('fiscal_position')
                        )
                        # price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, res_id.tax_id, self.company_id)

                        # res_id.price_unit = price_unit
        # Verificar que el producto se maneja por serie unica
        # 07022018 no tiene sentido actualizar los datos de chasis si la venta no esta confirmado
        # if res_id.lot_id and res_id.product_id.tracking == 'serial':
        #     # Buscar si la linea de pedido de ventas a sido asignado algun chasis
        #     # y borrar para realizar una nueva asignación
        #     lot_search = lot.search([('sale_line_id', '=', res_id.id)])
        #     for lot_data in lot_search:
        #         if lot_data.location_id:
        #             if lot_data.location_id.usage == 'internal':
        #                 lot_data.write({'sale_line_id': False})
        #                 lot_data.write({'modelo': False})
        #                 lot_data.write({'marca': False})
        #                 lot_data.write({'user_id': False})
        #                 lot_data.write({'partner_id': False})
        #     res_id.lot_id.write({'modelo': res_id.modelo.id})
        #     res_id.lot_id.write({'marca': res_id.modelo.marca.id})
        #     res_id.lot_id.write({'user_id': res_id.order_id.user_id.id})
        #     res_id.lot_id.write({'partner_id': res_id.order_id.partner_id.id})
        #     res_id.lot_id.write({'sale_line_id': res_id.id})
        return res_id

    @api.multi
    def write(self, vals):
        if vals.get('product_id', False) or vals.get('lot_id', False):
            pricelist_id = False
            year_id = False
            if vals.get('lot_id', False):
                lot_obj = self.env['stock.production.lot']
                lot_id = lot_obj.browse(vals['lot_id'])
                year_id = lot_id.anio_modelo and lot_id.anio_modelo.id or False

            if vals.get('pricelist_id', False):
                pricelist_id = vals['pricelist_id']
            else:
                pricelist_id = self.order_id.pricelist_id.id
            if vals.get('product_uom_qty', False):
                product_uom_qty = vals['product_uom_qty']
            else:
                product_uom_qty = self.product_uom_qty
            if self.order_id.pricelist_id and self.order_id.partner_id:
                if vals.get('product_id', False):
                    product_obj = self.env['product.product']
                    product_id = product_obj.browse(vals['product_id'])
                else:
                    product_id = self.product_id
                product = product_id.with_context(
                    year_id=year_id,
                    lang=self.order_id.partner_id.lang,
                    partner=self.order_id.partner_id.id,
                    quantity=product_uom_qty,
                    date_order=self.order_id.date_order,
                    pricelist=pricelist_id,
                    uom=self.product_uom.id,
                    fiscal_position=self.env.context.get('fiscal_position')
                )
                # price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
                # vals.update({'price_unit': price_unit})
        result = super(SaleOrderLine, self).write(vals)
        return result

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if self.order_id.sale_type_id.invoice_type == 'invoice_type_2':
            res.update({
                'price_unit': self.order_id.amount_total_plus_a,
                'discount': 0,
            })

        return res

    # Funcion mejorada en V11 no es necesario
    # @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    # def _onchange_product_id_check_availability(self):
    #     if not self.product_id or not self.product_uom_qty or not self.product_uom:
    #         self.product_packaging = False
    #         return {}
    #     if self.product_id.type == 'product':
    #         precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         product_qty = self.env['product.uom']._compute_qty_obj(self.product_uom, self.product_uom_qty,
    #                                                                self.product_id.uom_id)
    #         availability = 0
    #         if self.product_id:
    #             quant_obj = self.env['stock.quant']
    #             loc_ids = [self.order_id.warehouse_id.lot_stock_id.id]
    #             quant_ids = quant_obj.search([('location_id', 'in', loc_ids), ('product_id', '=', self.product_id.id),
    #                                           ('reservation_id', '=', False)])
    #             for quant in quant_ids:
    #                 availability += quant.qty
    #
    #         if float_compare(availability, product_qty, precision_digits=precision) == -1:
    #             is_available = self._check_routing()
    #             if not is_available:
    #                 warning_mess = {
    #                     'title': _('Not enough inventory!'),
    #                     'message': _(
    #                         'Pretende vender %.2f %s A nivel nacional tiene %.2f %s disponibles!\nEn su sucursal tiene %.2f %s.') % \
    #                                (self.product_uom_qty, self.product_uom.name, self.product_id.virtual_available,
    #                                 self.product_id.uom_id.name, availability,
    #                                 self.product_id.uom_id.name)
    #                 }
    #                 return {'warning': warning_mess}
    #     return {}

class SaleOrderDealsheet(models.Model):
    _name = 'sale.order.dealsheet'
    _description = 'Dealsheet'

    order_id = fields.Many2one('sale.order', 'Cotizacion')
    name = fields.Char('Descripcion')
    cost = fields.Float('Costo')
    invoiced_amount = fields.Float('Facturado')


class SaleOrderLineA(models.Model):
    _name = 'sale.order.line.a'
    _inherit = 'sale.order.line'

    order_id = fields.Many2one('sale.order', 'Orden de Venta')
    accesory = fields.Boolean('Accesorio', default=True)
