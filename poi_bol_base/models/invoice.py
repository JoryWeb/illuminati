##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
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

from odoo import models, fields, api
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
import re


def check_mod_installed(cr, mod_name):
    cr.execute("SELECT state from ir_module_module where name = %s ", (mod_name,))
    rs = cr.fetchone()
    mod_state = rs and rs[0] or False

    if not mod_state:
        return False
    if mod_state == "installed":
        return True
    else:
        return False


# Diccionario de equivalencias entre tipificación OpenERP y tipificación SIN para facturas
type_sin_dict = {
    'out_invoice': '7',
    'in_invoice': '1',
    'out_refund': '11',
    'in_refund': '11',
    '': '10',
}


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def nuevos_datos(self):

        # Lanzar asistente de Nota de crédito
        context = {}
        context['active_ids'] = self._ids
        context['invoice_id'] = len(self._ids) > 0 and self._ids[0] or False

        view_id = self.env.ref('poi_bol_base.wiz_invoice_refund')

        wizard_form = {
            'name': u"Modificar Factura Original",
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'wiz.invoice_refund',
            'type': 'ir.actions.act_window',
            'search_view_id': False,
            'target': 'new',
            'context': context,
        }
        return wizard_form

    def _get_tipo_sin(self):
        # Asignar Tipo de Factura según la numeración de impuestos internos
        tipo = self.env.context.get('tipo_fac', False)
        if not tipo:
            inv_type = self.env.context.get('type', self.type or '')
            tipo = type_sin_dict[inv_type]
        return tipo

    def _get_tipo_com(self):
        # Asignar Tipo '1' sólo a Facturas de Compra
        tipo = False
        if self.env.context.get('type', '') == 'in_invoice':
            tipo = '1'
        return tipo

    @api.one
    @api.depends('estado_fac')
    def _get_estado_fac(self):
        self.estado_fac_display = self.estado_fac

    def _get_default_dosif(self):
        dosif_users_pool = self.env['poi_bol_base.cc_dosif.users']
        dosif_users_ids = dosif_users_pool.search([('user_id', '=', self.env.uid), ('user_default', '=', True)])
        if dosif_users_ids:
            for dosif_users in dosif_users_ids:
                if dosif_users.dosif_id.activa and dosif_users.dosif_id.applies == 'out_invoice':
                    return dosif_users.dosif_id.id

    @api.one
    @api.depends('invoice_line_ids')
    def _suma_desc(self):
        for inv in self:
            desc = 0.0
            for line in inv.invoice_line_ids:
                desc += line.price_unit * ((line.discount or 0.0) / 100.0) * line.quantity
            self.sum_desc = desc

    @api.one
    @api.depends('invoice_line_ids', 'tax_line_ids')
    def _amount_all_bs(self):
        for invoice in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            for line in invoice.invoice_line_ids:
                amount_untaxed += line.price_subtotal
            for line in invoice.tax_line_ids:
                amount_tax += line.amount
            amount_total = amount_tax + amount_untaxed
            cur = invoice.currency_id
            if cur.name == 'BOB':
                self.total_bs = amount_total
                self.tax_bs = amount_tax
            else:
                cur_bob = self.env['res.currency'].search([('name', '=', 'BOB')], limit=1)
                if cur_bob:
                    cur_bob = cur_bob[0]
                    date_rate = invoice.date_invoice and invoice.date_invoice[0:10] or False
                    self.total_bs = cur.with_context(date=date_rate).compute(amount_total, cur_bob)
                    self.tax_bs = cur.with_context(date=date_rate).compute(amount_tax, cur_bob)

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice',
                 'type')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()

        # Calculo preliminar totales segun tipo especificos de impuestos SIN
        if self.tipo_fac != '12':
            self.ice = sum(line.amount for line in self.tax_line_ids if line.type_bol == 'ice')
            self.iva = sum(line.amount for line in self.tax_line_ids if line.type_bol == 'iva')
            self.exe = sum(line.amount for line in self.tax_line_ids if line.type_bol == 'exe')

    @api.one
    @api.depends('invoice_line_ids')
    def _con_impuesto(self):
        for inv in self:
            self.con_imp = False
            for line in inv.invoice_line_ids:
                for tax in line.invoice_line_tax_ids:
                    if tax.apply_lcv:
                        self.con_imp = True

    @api.model
    def _con_impuesto_search(self, operator, operand):
        if not operator:
            return []

        if operator == '=':
            if operand:
                self.env.cr.execute(
                    """select il.invoice_id from account_invoice_line il inner join account_invoice_line_tax ilt on il.id = ilt.invoice_line_id inner join account_tax tx on ilt.tax_id = tx.id where tx.apply_lcv = True group by il.invoice_id  """)
            else:
                self.env.cr.execute(
                    """select il.id from account_invoice_line il where il.id not in (select ilt.invoice_line_id from account_invoice_line_tax ilt inner join account_tax tx on ilt.tax_id = tx.id where tx.amount > 0 group by ilt.invoice_line_id) group by il.id""")

        res = self.env.cr.fetchall()
        if not res:
            return [('id', '=', 0)]
        return [('id', 'in', [x[0] for x in res])]

    picking_id = fields.Many2one('stock.picking', 'Items Picking')
    refunds_id = fields.Many2one('account.invoice', 'Factura reintegrada', copy=False)
    note_from_id = fields.Many2one('account.invoice', 'Factura origen de Nota', copy=False,
                                   help=u"Factura de la cual originó esta Nota de Credito")
    nit = fields.Char('NIT', size=12, help="NIT o CI del cliente.")
    razon = fields.Char(u'Razón Social', help=u"Nombre o Razón Social para la Factura.")
    cc_date = fields.Date('Fecha factura fiscal',
                          help=u"Fecha de factura fiscal de Compra según copia física. Usar en caso de requerir especificar una fecha de factura diferente a la fecha de contabilización. En caso de dejar este campo vacío, se usara la fecha de Factura de la cabecera.")
    cc_nro = fields.Integer('Nro. Factura', help=u"Número de factura fiscal.", copy=False)
    cc_aut = fields.Char(u'Nro. Autorización', help=u"Número de autorización.")
    # cc_aut debería ser .integer_big(). Pero openerp no parsea el campo en vista. Resuelto en fución _init_
    cc_dos = fields.Many2one('poi_bol_base.cc_dosif', string='Serie dosificación', default=_get_default_dosif,
                             readonly=True, states={'draft': [('readonly', False)]}, domain="[('applies', '=', type)]",
                             help=u"Serie de dosificación según parametrización. Asocia Número de autorizacción y Llave de dosificación.")
    cc_dos_autonum = fields.Boolean(related='cc_dos.auto_num', string='Auto numera')
    cc_cod = fields.Char(u'Código de control', size=14,
                         help=u"Codigo de representación única para el SIN. Introducir manualmente para Compras.")
    total_bs = fields.Float(compute='_amount_all_bs', string='Total (Bs.)', store=True)
    tax_bs = fields.Float(compute='_amount_all_bs', string='Impuesto (Bs.)', store=True)
    sum_desc = fields.Float(compute="_suma_desc", method=True, string="Descuentos obtenidos", store=True,
                            digits=dp.get_precision('Account'),
                            help=u"Descuentos, Bonificaciones y Rebajas obtenidas. Es el descuento impositivo de factura que se hace visible en el Libro de Compras.")
    contract_nr = fields.Char(u'N° de contrato', help=u"El número de contrato registrado para fines de Bancarización.")
    # Para Libro CV:
    con_imp = fields.Boolean(compute='_con_impuesto', method=True, string='Incluye Impuesto',
                             search='_con_impuesto_search',
                             help=u"Indica la facturas que incluyen impuesto para LCV. Verdadero si tan sólo una línea de la Factura tiene impuesto LCV")
    tipo_fac = fields.Selection(
        [('1', 'Compra'), ('2', 'Boleto BCP'), ('3', 'Importación'), ('4', 'Recibo de Alquiler'),
         ('5', 'Nota de débito proveedor'), ('6', 'Nota de crédito cliente'), ('7', 'Venta'),
         ('8', 'Nota de débito cliente'), ('9', 'Nota de crédito proveedor'), ('10', 'Sin Asignar'),
         ('11', 'Rectificación'), ('12', 'Dui'), ('13', u'Exportación')], string='Tipo de Factura',
        default=_get_tipo_sin, help=u"Tipificación de facturas para fines técnicos.")
    estado_fac = fields.Selection([('V', u'Válida'),
                                   ('A', 'Anulada'), ('E', 'Extraviada'), ('N', 'No Utilizada'), ('na', 'No Aplica'),
                                   ('C', 'Emitida en Contingencia')], 'Estado SIN', default='V', copy=False)
    estado_fac_display = fields.Selection(
        [('V', u'Válida'), ('A', 'Anulada'), ('E', 'Extraviada'), ('N', 'No Utilizada'), ('na', 'No Aplica')],
        string='Estado SIN Display', readonly=True, compute='_get_estado_fac')
    iva = fields.Float('Importe IVA', digits=dp.get_precision('Account'),
                       states={'open': [('readonly', True)], 'paid': [('readonly', True)]})
    ice = fields.Float('Importe ICE', digits=dp.get_precision('Account'))
    exento = fields.Float('Importe Exentos', digits=dp.get_precision('Account'),
                          help=u"Importe Exentos o Ventas gravadas a tasa cero.")
    exporta = fields.Float('Exportaciones', digits=dp.get_precision('Account'),
                           states={'open': [('readonly', True)], 'paid': [('readonly', True)]},
                           help="Exportaciones y operaciones Exentas")
    supplier_invoice_number = fields.Char(string='Ref. documento Proveedor',
                                          help="La codificación referencial provista por el Proveedor (No correspode al número de factura impositivo).",
                                          readonly=True, states={'draft': [('readonly', False)]})
    # Para Importaciones. Incluidos ya en poi_bol_base porque el Libro de Compras depende de ellos
    imp_pol = fields.Char(u'Nro. Póliza Importación', size=16,
                          help=u"Número de póliza de importación para Libro de compras. Formato AAAADDDCNNNNNNNN, donde: AAAA=Año, DDD=Código de la Aduana, C=Tipo de Trámite, NNNNNNNN=Número Correlativo")
    iva_pol = fields.Float(u'IVA Póliza', digits=dp.get_precision('Account'),
                           help=u"Crédito fiscal IVA según Póliza de Importación. Este valor sera usado como base de cálculo en el Libro de Compras para esta transacción!")
    tipo_com = fields.Selection(
        [('1', 'Mercado Interno'), ('2', 'Mercado Interno NO gravadas'), ('3', 'Sujetas a proporcionalidad'),
         ('4', 'Destino Exportaciones'), ('5', 'Interno y Exportaciones')], string='Tipo de Compra',
        default=_get_tipo_com,
        help=u"""Valor único del 1 al 5 que representa el destino que se le dará a la compra realizada:
                                            1 = Compras para mercado interno con destino a actividades gravadas,
                                            2 = Compras para mercado interno con destino a actividades no gravadas,
                                            3 = Compras sujetas a proporcionalidad,
                                            4 = Compras para exportaciones,
                                            5 = Compras tanto para el mercado interno como para exportaciones.""")

    _sql_constraints = [
        ('check_nit', "CHECK (nit ~ '^[0-9\.]+$')",
         u'NIT sólo acepta valores numéricos y que no empiecen con cero!'),
        ('check_cc_aut', "CHECK (cc_aut ~ '^[0-9\.]+$')",
         u'Nro Autorización sólo acepta valores numéricos!'),
        ('check_cc_cod',
         "CHECK (cc_cod='' OR cc_cod ~ '[0-9A-F][0-9A-F][-][0-9A-F][0-9A-F][-][0-9A-F][0-9A-F][-][0-9A-F][0-9A-F]')",
         u'Formato de Codigo de control no valido! Debe tener la forma XX-XX-XX-XX (valores permitidos: 0-9 y A-F)'),
    ]

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id:
            self.nit = (
                               self.partner_id.commercial_partner_id.nit != 0 and self.partner_id.commercial_partner_id.nit) or (
                               self.partner_id.commercial_partner_id.ci != 0 and self.partner_id.commercial_partner_id.ci) or ''
            self.razon = self.partner_id.commercial_partner_id.razon_invoice or self.partner_id.commercial_partner_id.razon or self.partner_id.commercial_partner_id.name or ''

    @api.onchange('cc_aut')
    def onchange_cc_aut(self):
        if not self.cc_aut:
            return {}
        if re.match("^-?[0-9]+$", self.cc_aut) != None:
            return {}
        else:
            result = {}
            result['warning'] = {'title': u'Número de autorización inválido',
                                 'message': u'Por favor ingrese un número de autorización válido'}
            self.cc_aut = ''
            return result

    @api.onchange('nit')
    def onchange_nit(self):
        result = {}
        if self.nit and re.match("^-?[0-9]+$", self.nit) is None:
            result['warning'] = {'title': u'NIT inválido', 'message': u'Por favor ingrese un número de NIT válido'}
            self.nit = ''
            return result
        bol_customer_pool = self.env['bol.customer']
        if not self.partner_id:
            razon_bol = bol_customer_pool.get_razon(self.nit)
            if razon_bol:
                self.razon = razon_bol
        return result

    @api.onchange('cc_dos')
    def onchange_cc_dos(self):
        if self.cc_dos:
            self.cc_aut = self.cc_dos.nro_orden

    @api.onchange('cc_cod')
    def onchange_cc_cod(self):
        if self.cc_cod:
            tam = len(self.cc_cod)
            if tam == 12:
                tam_cod = self.cc_cod[:-1]
                self.cc_cod = tam_cod
            # self.cc_aut = self.cc_dos.nro_orden

    @api.multi
    def invoice_validate(self):
        ret = super(AccountInvoice, self).invoice_validate()
        for obj_inv in self:
            if obj_inv.type in ('out_invoice', 'out_refund'):
                if not obj_inv.cc_dos and obj_inv.type == 'out_invoice':
                    raise UserError(u'[BOL] Factura de venta sin serie de Dosificación.')
                if not obj_inv.company_id.allow_invoice_defer and obj_inv.date_invoice < fields.Date.context_today(
                        self):
                    raise UserError(u'[BOL] No esta permitida la creación de Facturas de venta con fecha anterior.')
                if obj_inv.cc_dos.fecha_fin and obj_inv.date_invoice > obj_inv.cc_dos.fecha_fin:
                    raise UserError(u'[BOL] Fecha de factura mayor a fecha limite de dosificación.')
                if obj_inv.cc_dos.require_taxes and not obj_inv.con_imp:
                    raise UserError(
                        u'[BOL] Esta dosificación únicamente puede ser aplicada para facturas con impuestos.')
                if obj_inv.cc_dos.auto_num:
                    nro_val = self.env['poi_bol_base.cc_dosif'].set_unique_numbering(obj_inv.id, obj_inv.cc_dos.id,
                                                                                     case='invoice')
                else:
                    nro_val = obj_inv.cc_nro
                    obj_inv.write({'cc_nro': nro_val})

                aut_val = obj_inv.cc_dos.nro_orden
                obj_inv.write({'cc_aut': aut_val})
            elif obj_inv.type == 'in_invoice':
                if obj_inv.con_imp:
                    if not obj_inv.cc_aut or not obj_inv.nit or not obj_inv.cc_nro:
                        raise UserError(u'[BOL] Faltan datos de Control SIN para factura de compra.')
            if obj_inv.nit and obj_inv.razon:
                self.env['bol.customer'].set_razon(obj_inv.nit, obj_inv.razon)
            # Conciliar Notas de crédito con su factura origen si es aplicable
            if obj_inv.note_from_id and obj_inv.note_from_id.id and obj_inv.estado_fac == "V":
                base_invoice = self.browse([obj_inv.note_from_id.id])[0]
                if base_invoice.state == 'open' and base_invoice.residual >= obj_inv.amount_total:
                    # Conciliar de la misma manera que se hace en account/wizard/account_invoice_refund.py
                    to_reconcile_ids = {}
                    reconcile_ids = []
                    movelines = base_invoice.move_id.line_ids
                    to_reconcile_lines_obj = self.env['account.move.line']
                    for line in movelines:
                        if line.account_id.id == base_invoice.account_id.id:
                            # to_reconcile_lines += line
                            reconcile_ids.append(line.id)
                            to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                        if line.reconciled:
                            line.remove_move_reconcile()
                    obj_inv.signal_workflow('invoice_open')
                    for tmpline in obj_inv.move_id.line_ids:
                        if tmpline.account_id.id == base_invoice.account_id.id:
                            # to_reconcile_lines += tmpline
                            reconcile_ids.append(tmpline.id)
                    to_reconcile_lines = to_reconcile_lines_obj.browse(reconcile_ids)
                    to_reconcile_lines.reconcile()

                    # Si la conciliación de la Nota es completa, cambiar Estado a 'paid'
                    self.env.cr.commit()
                    if obj_inv.reconciled:
                        self.confirm_paid([obj_inv.id])
            # Calculo final totales segun tipo especificos de impuestos SIN
            ice_sum = 0.0
            iva_sum = 0.0
            exe_sum = 0.0
            for line in self.tax_line_ids:
                type_bol = False
                if line.tax_id:
                    type_bol = line.tax_id.type_bol
                    if type_bol == 'ice':
                        ice_sum += line.amount or 0.0
                    elif type_bol == 'iva':
                        iva_sum += line.amount or 0.0
                    elif type_bol == 'exe':
                        exe_sum += line.amount or 0.0
            # En caso de ser factura DUI evitar que calcule a 0 los valores por defecto de los impuestos
            if self.tipo_fac != '12':
                self.ice = ice_sum
                self.iva = iva_sum
                self.exe = exe_sum

    def _prepare_tax_line_vals(self, line, tax):
        vals = super(AccountInvoice, self)._prepare_tax_line_vals(line, tax)

        if vals.get('tax_id'):
            # Incorporar los identificadores SIN para poder sacar las sumatorias respectivas mas adelante y permitir la edicion dependiendo de si es 'manual'
            tax = self.env['account.tax'].browse(vals.get('tax_id'))
            vals['type_bol'] = tax.type_bol
            # si se activa el campo manual el sistema evita que se borre esa linea
            # manual lo considera cuando el usuario agraga una linea de impuesto
            # y por lo tanto no debe borrarse
            # vals['manual'] = tax.manual
            vals['price_include'] = tax.price_include

        return vals

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ finalize_invoice_move_lines(move_lines) -> move_lines
            Reemplazar cuentas para rectificaciones de Impuesto fuera de período (o sea Notas de crédito)
        """
        move_lines = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        if self.type in ['in_refund', 'out_refund'] and (self.note_from_id or self.tipo_fac in ('5', '6', '8')):
            for line_arr in move_lines:
                line = line_arr[2]
                if 'tax_amount' in line and line['tax_amount'] > 0:
                    tax = self.env['account.tax'].search([('name', '=', line['name']), ('parent_id', '=', False)],
                                                         limit=1)
                    if tax.account_creditnote_id:
                        line['account_id'] = tax.account_creditnote_id.id
        return move_lines

    def action_cancel(self):
        # Actualizar estado para Libros CV
        if super(AccountInvoice, self).action_cancel():
            return self.write({'estado_fac': 'na'})
        else:
            return False

    @api.multi
    def action_annul(self):
        # go from canceled state to draft state
        self.write({'estado_fac': 'A'})
        self.delete_workflow()
        return True

    def action_nota(self):
        # Lanzar asistente de Nota de crédito
        context = {}
        context['active_ids'] = self._ids
        context['invoice_id'] = len(self._ids) > 0 and self._ids[0] or False
        # Checking if there is a nota not cancelled
        # nota_id = self.search(['&',('note_from_id','in',ids),('state','not in',['cancel'])])
        # if len(nota_id) > 0:
        #    raise UserError('Error', u'Ya existe una nota de crédito activa para esta factura, si existió un error cancele primero la nota de crédito generada')
        wizard_form = {
            'name': u"Generar Nota de Crédito",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'poi_bol.nota.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': context,
        }
        return wizard_form

    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        # Guardar número de factura reintegrada para futura referencia. Copiar datos SIN tambien
        invoice_data = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice=date_invoice, date=date,
                                                                   description=description, journal_id=journal_id)
        if invoice_data:
            invoice_data.update({'refunds_id': invoice.id,
                                 'nit': invoice.nit,
                                 'razon': invoice.razon,
                                 'estado_fac': 'na',
                                 'cc_dos': False,
                                 'cc_nro': 0,
                                 'tipo_fac': invoice.tipo_fac,
                                 # 'shop_id': invoice.shop_id.id,    #TODO: Update refund with warehouse_id
                                 })
        return invoice_data

    @api.multi
    def _compute_legacy_id(self):
        legacy_obj = self.env['account.invoice.legacy']
        for s in self:
            legacy_ids = legacy_obj.search([('active_id', '=', s.id)])
            if legacy_ids:
                s.legacy_id = legacy_ids.id


# Incrementar precisión de % de descuento para consistencia con MONTO de descuento
class accountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _amount_line_with_tax(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_subtotal_with_tax = taxes['total_included'] if taxes else self.quantity * price

    base_tax = fields.Float(string='Precio efectivo', digits=dp.get_precision('Account'),
                            help=u"Precio base efectivo despues de impuesto. Modificará el campo Precio unitario de manera que después de impuestos iguale el Precio efectivo.")
    price_subtotal_with_tax = fields.Monetary(string='Total', currency_field='company_currency_id', store=True,
                                              readonly=True, compute='_amount_line_with_tax',
                                              help="Monto total incluyendo impuestos.")

    @api.one
    @api.depends('base_tax', 'invoice_line_tax_id')
    def onchange_base_tax(self):
        """Calcular un nuevo precio inflado de manera que despues de sacarle impuestos de este monto base.
           Ejemplo: Caso retenciones cuando el proveedor cobra un monto fijo e independiente de si se le aplica Retención o no."""
        new_price = 0.0
        tot_tax = 0.0
        tax_ids = self.invoice_line_tax_id
        for itax in self.env['account.tax'].browse(tax_ids):
            if itax.child_ids:
                for ichild in itax.child_ids:
                    tot_tax = tot_tax + (itax.amount * abs(ichild.amount))
            else:
                tot_tax = tot_tax + itax.amount

        if tot_tax > 0.0 and tot_tax < 1:
            new_price = self.base_tax / (1 - tot_tax)

        if new_price > 0.0:
            self.price_unit = new_price
        else:
            return True

    def action_inverse_tax(self):

        # Lanzar asistente de Calculo de precio inverso
        context = {}
        context['active_ids'] = self.ids
        context['invoice_line_id'] = len(self.ids) > 0 and self.ids[0] or False
        view_id = self.env.ref('poi_bol_base.view_poi_bol_tax_inverse').id
        wizard_form = {
            'name': u"Cálculo precio inverso",
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'res_model': 'poi_bol.tax_inverse.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': context,
        }
        return wizard_form


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    type_bol = fields.Selection(
        [('none', 'Ninguno'), ('iva', 'IVA'), ('ice', 'ICE'), ('exe', 'Exento'), ('ret', 'Retención')],
        string="Caso SIN")
    price_include = fields.Boolean(string="Incluir en el precio",
                                   help="Aplica para impuestos editables manualmente para que sean considerados al recalcular.")


class account_invoice_refund(models.Model):
    _name = 'account.invoice.legacy'

    active_id = fields.Integer('Active_id')
    cc_nro = fields.Char(u'Número de Factura')
    cc_aut = fields.Char(u'Autorización Nro.')
    nit = fields.Char('NIT')
    invoice_line = fields.One2many('account.invoice.legacy.line', 'invoice_id', string='Invoice Lines', readonly=True)
    amount_untaxed = fields.Float('Total Sin Impuesto')
    amount_tax = fields.Float('Impuesto')
    amount_total = fields.Float('Total')


class account_invoice_refund_line(models.Model):
    _name = "account.invoice.legacy.line"

    invoice_id = fields.Many2one('account.invoice.legacy', string='Factura', ondelete='cascade', index=True)
    uos_id = fields.Many2one('product.uom', string='Unidad de Medida', ondelete='set null', index=True)
    product_id = fields.Many2one('product.product', string='Producto', ondelete='restrict', index=True)
    price_unit = fields.Float(string='Precio Unitario', digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Float(string='Monto Total', digits=dp.get_precision('Account'), readonly=True)
    price_net = fields.Float(string='Precio Neto', digits=dp.get_precision('Account'))
    quantity = fields.Float(string='Cantidad', digits=dp.get_precision('Product Unit of Measure'), default=1)
    discount = fields.Float(string='Descuento (%)', digits=dp.get_precision('Discount'), default=0.0)


class revert_description(models.Model):
    _name = "revert.description"

    name = fields.Char(string='Description', required=True)
