##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2011 Poiesis Consulting (<http://www.poiesisconsulting.com>). All Rights Reserved.
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from odoo import models, fields, api

CONTRACT_TYPES = [('draft','Borrador'),
                  ('in_process','En proceso'),
                  ('done','Finalizado'),
                  ('canceled','Cancelado')]

CONTRACT_PAYMENTS = [('plan_pagos','Plan de Pagos'),
                  ('plan_fijos_res','Plan Fijos Recurrente'),]

class PartnerContractInvoice(models.Model):
    _name = "partner.contract.invoice"
    _description = 'Contratos de Compras y Facturas'
    _inherit = ['mail.thread']

    name = fields.Char('Nombre del Contracto')
    partner_id = fields.Many2one('res.partner', 'Proveedor', required=True)
    user_id = fields.Many2one('res.users', string='Gestor contable', track_visibility='onchange',
                              readonly=True, states={'draft': [('readonly', False)]},
                              default=lambda self: self.env.user)
    reference = fields.Char('Referencia')
    order_id = fields.Many2one('purchase.order', 'Orden de Compra Base', required=True)
    state = fields.Selection(CONTRACT_TYPES, string='State', default='draft', required=True)
    plan_pagos = fields.Selection(CONTRACT_PAYMENTS, string=u'Plan Facturación', default='plan_pagos')
    company_id = fields.Many2one('res.company', u'Compañia', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('partner.contract.invoice'))
    date_start = fields.Date(u'Fecha Inicial', required=True, help=u'Fecha inicial del contrato')
    date_end = fields.Date(u'Fecha Final', required=True, help=u'Fecha finalización del contracto')
    reference_payment = fields.Char('Referencia Pago')
    delivery_invoice_id = fields.One2many('purchase.delivery.invoice', 'contract_id', 'Plan de entregas y facturas')
    contract_invoice_id = fields.One2many('partner.contract.invoice.line', 'contract_id', u'Plan de facturación y pagos')
    denom = fields.Char(u'Denominación')
    propi = fields.Char(u'Propietario')
    ubica = fields.Char(u'Ubicación')
    condi = fields.Text(u'Condiciones')
    mejor = fields.Text(u'Mejoras')
    hecta = fields.Char(u'Hectareas')
    is_banking = fields.Boolean(u'Sujeto a bancarización')

    @api.multi
    def contract_cancel(self):
        for contract in self:
            contract.state = 'cancel'
        return True

    @api.multi
    def contract_done(self):
        for contract in self:
            contract.state = 'done'
        return True

    @api.multi
    def contract_in_process(self):
        for contract in self:
            contract.state = 'in_process'
        return True

    @api.multi
    def verificar_invoice(self):
        valor = True
        for delivery in self.delivery_invoice_id:
            if delivery.invoice_id.state not in ('paid','cancel'):
               valor = False

        for inv in self.contract_invoice_id:
            if inv.invoice_id.state not in ('paid', 'cancel'):
                valor = False
        if valor:
            self.signal_workflow('verificar_facturas')


    @api.multi
    def action_view_account_move(self):
        '''
        Funcion necesaria para obtener los quants asignados a este chasis
        '''
        action = self.env.ref('account.action_account_moves_all_a')
        result = action.read()[0]
        res = self.env.ref('account.view_move_line_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.id
        result['domain'] = "[('partner_id','in',[" + ','.join(map(str, [self.partner_id.id])) + "])]"
        return result

class PurchaseDeliveryInvoice(models.Model):
    _name = "purchase.delivery.invoice"

    @api.one
    @api.depends('picking_id')
    def _compute_total_invoice(self):
        for record in self:
            invoice = self.env['account.invoice'].search([('picking_id', '=', record.picking_id.id)])
            record.invoice_id = invoice.id
            record.amount_inv = invoice.amount_total
            if invoice.residual > 0:
                record.amount_paid = invoice.amount_total - invoice.residual
                record.amount_rest = invoice.residual
            else:
                record.amount_paid = 0.0
                record.amount_rest = 0.0

    picking_id = fields.Many2one('stock.picking', 'Ingreso',
                                 readonly=True, index=True, ondelete='restrict', copy=False)
    date_done = fields.Datetime(related='picking_id.date_done', string='Fecha Recepción', required=False, help=u'Fecha Recepción de los productos')
    state = fields.Selection(related='picking_id.state', string='Estado', store=True, help=u'Estado Albarán')

    amount_inv = fields.Float(compute='_compute_total_invoice', string="Monto Factura")
    amount_paid = fields.Float(compute='_compute_total_invoice', string="Monto Pagado")
    amount_rest = fields.Float(compute='_compute_total_invoice', string="Monto Restante")
    invoice_id = fields.Many2one(compute='_compute_total_invoice',
                                  comodel_name='account.invoice',
                                  string="Factura")
    contract_id = fields.Many2one('partner.contract.invoice')

    @api.multi
    def btn_view_invoice(self):
        mod_obj = self.env['ir.model.data']
        model, action_id = tuple(
            mod_obj.get_object_reference(
                'account',
                'action_invoice_tree'))
        action = self.env[model].browse(action_id).read()[0]
        res = False
        uid_company_id = self.env.user.company_id.id
        for contract_line in self:
            inv_lines = []
            if not contract_line.invoice_id:
                return True
            else:
                res = mod_obj.get_object_reference('account', 'invoice_supplier_form')
                action['views'] = [(res and res[1] or False, 'form')]
                action['res_id'] = contract_line.invoice_id.id or False

        return action

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(PurchaseDeliveryInvoice, self).default_get(cr, uid, fields, context=context)
        contract_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not contract_ids or len(contract_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('purchase.order'), 'Bad context propagation'
        contract_id, = contract_ids
        contract = self.pool.get('purchase.order').browse(cr, uid, contract_id, context=context)
        items = []
        items2 = []
        for po in contract.order_id.picking_ids:
            item = {
                'purchase_id': po.order_id.id,
                'purchase_line_id': po.id,
                'product_id': po.product_id.id,
                'product_qty': po.product_qty,
                'delivery_date': po.date_planned,
            }
            if po.product_id:
                items.append(item)

            item2 = {
                'purchase_id': po.order_id.id,
                'purchase_line_id': po.id,
                'product_id': po.product_id.id,
                'product_qty': po.product_qty,
                'delivery_date': po.date_planned,
            }
            if po.product_id:
                items2.append(item2)

        #res.update(item_ids=items)
        res.update(item_planned_ids=items2)
        res.update(base_date=purchase.minimum_planned_date)
        return res

class PartnerContractInvoiceLine(models.Model):
    _name = "partner.contract.invoice.line"

    @api.depends('invoice_id')
    def _compute_total_paid(self):
        for record in self:
            if record.invoice_id:
                if record.invoice_id.residual > 0:
                    record.amount_paid = record.invoice_id.amount_total - record.invoice_id.residual
                elif record.invoice_id.state in ('paid'):
                    record.amount_paid = record.invoice_id.amount_total
                else:
                    record.amount_paid = 0.0


    @api.depends('invoice_id')
    def _compute_total_rest(self):
        for record in self:
            record.amount_rest = record.invoice_id.residual

    date = fields.Date('Fecha Planificada', required=False, help=u'Fecha Recepción de los productos')
    product_id = fields.Many2one('product.product', 'Servicio')
    amount_inv = fields.Float('Monto Factura')
    invoice_id = fields.Many2one('account.invoice', 'Factura')
    amount_paid = fields.Float(compute='_compute_total_paid', string='Monto Pagado')
    amount_rest = fields.Float(compute='_compute_total_rest', string='Monto Restante')
    contract_id = fields.Many2one('partner.contract.invoice')
    order_line_id = fields.Many2one('purchase.order.line', 'Linea de pedido de compra')

    @api.multi
    def btn_gen_invoice(self):
        mod_obj = self.env['ir.model.data']
        model, action_id = tuple(
            mod_obj.get_object_reference(
                'account',
                'action_invoice_tree'))
        action = self.env[model].browse(action_id).read()[0]
        res = False
        uid_company_id = self.env.user.company_id.id
        invoice = self.env['account.invoice']
        for contract_line in self:

            inv_lines = []
            if not contract_line.invoice_id:
                val_invoice = {
                    'partner_id': 1,
                    'type': 'in_invoice',
                    'purchase_id': contract_line.order_line_id.order_id.id,
                }
                invoice_id = self.env['account.invoice'].create(val_invoice)
                invoice_id.partner_id = contract_line.contract_id.partner_id.id
                invoice_id.date_invoice = contract_line.date
                self.invoice_id = invoice_id.id

                new_lines = self.env['account.invoice.line']
                #for line in self:
                #    # Load a PO line only once
                data = self._prepare_invoice_line_from_po_line(contract_line.order_line_id, contract_line.amount_inv, invoice_id)
                new_line = new_lines.new(data)
                #new_line._set_additional_fields(self)
                new_lines += new_line
                invoice_id.invoice_line_ids += new_lines
                invoice_id.compute_taxes()
                for invoice_line in invoice_id.invoice_line_ids:
                    self.invoice_line = invoice_line.id

                res = mod_obj.get_object_reference('account', 'invoice_supplier_form')
                action['views'] = [(res and res[1] or False, 'form')]
                action['res_id'] = invoice_id.id or False
            else:
                res = mod_obj.get_object_reference('account', 'invoice_supplier_form')
                action['views'] = [(res and res[1] or False, 'form')]
                action['res_id'] = contract_line.invoice_id.id or False

        return action

    def _prepare_invoice_line_from_po_line(self, line, amount, invoice_id):
        taxes = line.taxes_id
        invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.invoice.line']
        data = {
            'purchase_line_id': line.id,
            'name': line.name,
            'origin': line.order_id.name + '|' + self.contract_id.name,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': invoice_id.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.order_id.currency_id.compute(amount, line.order_id.currency_id, round=False),
            'quantity': line.product_qty,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, line.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data


    def _prepare_inv_line(self, account_id, order_line, contract_line):
        return {
            'name': order_line.name,
            'account_id': account_id,
            'price_unit': contract_line.amount_inv or 0.0,
            'quantity': order_line.product_qty,
            'product_id': order_line.product_id.id or False,
            'uos_id': order_line.product_uom.id or False,
            'invoice_line_tax_id': [(6, 0, [x.id for x in order_line.taxes_id])],
            'account_analytic_id': order_line.account_analytic_id.id or False,
            'purchase_line_id': order_line.id,
        }