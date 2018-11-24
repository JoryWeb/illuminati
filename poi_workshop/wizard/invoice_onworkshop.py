##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2016 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
import time

class InvoiceOnworkshop(models.TransientModel):
    _name = 'invoice.onworkshop'
    _description = 'Invoice Workshop'

    journal_id = fields.Many2one(comodel_name='account.journal', string="Diario Contable", required=False,
                                 domain=[('type', 'in', ['sale', 'general'])])
    date_invoice = fields.Date(string='Date Invoice')
    partner_id = fields.Many2one('res.partner', string='Partner')

    @api.model
    def default_get(self, fields):
        res = super(InvoiceOnworkshop, self).default_get(fields)
        if self._context and self._context.get('active_id'):
            orders = self.env['workshop.order'].browse(self._context['active_id'])
            if any(order.state not in ('ready', 'done', 'invoiced') for order in orders):
                raise UserError(_("Solo puede registrar Ordenes en estado Aprobado"))
            if any(ord.partner_id != orders[0].partner_id for ord in orders):
                raise UserError(
                    _("Con el fin de facturar multiples ordenes a la vez, deben pertenecer al mismo cliente."))

            res['partner_id'] = orders.partner_id.id
        return res

    @api.multi
    def invoice_create(self):
        active_id = self._context.get('active_id')
        context = dict(self._context or {})
        active_ids = context.get('active_ids')

        for act_id in active_ids:
            workshop = self.env['workshop.order'].browse(act_id)
            valid_invoice = True
            for picking in workshop.picking_ids:
                if picking.state in ('done', 'cancel'):
                    valid_invoice = True
                else:
                    valid_invoice = False
                    break

            if not valid_invoice:
                raise UserError(_("Debe confirmar la baja de todos los items para facturar"))

            partner = False
            if self.partner_id.parent_id:
                if not self.partner_id.parent_id.ci and not self.partner_id.parent_id.nit:
                    raise Warning(_('El cliente seleccionado no tiene NIT o CI'))
                partner = self.partner_id.parent_id
            else:
                if not self.partner_id.ci and not self.partner_id.nit:
                    raise Warning(_('El cliente seleccionado no tiene NIT o CI'))
                partner = self.partner_id
            val_invoice = {
                'partner_id': partner.id,
                'type': 'out_invoice',
                'journal_id': self.journal_id.id,
                'date_invoice': self.date_invoice,
                'asset_id': workshop.asset_id.id or False,
                'lot_id': workshop.chasis_id.id or False,
                'sale_type_id': workshop.workshop_type.sale_type_id.id,
                'nit': self.partner_id.nit or self.partner_id.ci,
                'razon': partner.razon_invoice or partner.razon,
            }
            invoice_id = self.env['account.invoice'].create(val_invoice)
            break
        origin_invoice = ''
        verif_line = True
        for act_id in active_ids:
            workshop = self.env['workshop.order'].browse(act_id)
            workshop.invoice_id = invoice_id.id
            origin_invoice = origin_invoice + workshop.name + ','
            new_lines = self.env['account.invoice.line']
            if not workshop.services_lines and not workshop.parts_lines:
                raise UserError(
                    _("No existe lineas para facturar"))

            for line in workshop.services_lines:
                # Verificar si lo servicios estan con cargo externo para facturar
                if line.cargo == 'externo':
                    data = self._prepare_invoice_line_from_workshop_service(line, invoice_id, workshop.warehouse_id.analytic_account_id.id)
                    if data:
                        self.env['account.invoice.line'].create(data)
                        #new_line = new_lines.new(data)
                        #new_line._set_additional_fields(invoice_id)
                        #new_lines += new_line
                        verif_line = False

            for line in workshop.parts_lines:
                # Verificar si los items estan con cargo externo para facturar
                if line.cargo == 'externo':
                    data = self._prepare_invoice_line_from_workshop_parts(line, invoice_id, workshop.warehouse_id.analytic_account_id.id)
                    if data:
                        self.env['account.invoice.line'].create(data)
                        #new_line = new_lines.new(data)
                        #new_line._set_additional_fields(invoice_id)
                        #new_lines += new_line
                        verif_line = False

            invoice_id.invoice_line_ids += new_lines
            invoice_id.compute_taxes()
            for invoice_line in invoice_id.invoice_line_ids:
                self.invoice_line = invoice_line.id
            # El control de facturado se lo realiza al validar la factura
            # total_ext_ot = 0
            # for line in workshop.services_lines:
            #     if line.cargo == 'externo':
            #         total_ext_ot += (line.price_unit * line.parts_qty)
            #
            # for line in workshop.parts_lines:
            #     if line.cargo == 'externo':
            #         total_ext_ot += (line.price_unit * line.parts_qty)
            # porcen_fac = (invoice_id.amount_total / total_ext_ot) * 100
            # if (workshop.invoice_porcentaje + porcen_fac) >= 100:
            #     workshop.write({'state': 'invoiced', 'date_execution': time.strftime('%Y-%m-%d %H:%M:%S')})
            workshop.write({'date_execution': time.strftime('%Y-%m-%d %H:%M:%S')})

        if verif_line:
            raise UserError(
                _("No existe servicio o items con cargo 'externo' para crear la factura"))

        invoice_id.origin = origin_invoice
        return {'type': 'ir.actions.act_window_close',}

    def _prepare_invoice_line_from_workshop_service(self, line, invoice_id, analytic_account_id):
        invoice_lines = self.env['account.invoice.line'].search([('service_line_id', '=', line.id)])
        price_invoice = 0
        price_unit = 0
        for invoice_line in invoice_lines:
            price_invoice += invoice_line.price_unit
        if line.price_unit > price_invoice:
            price_unit = line.price_unit - price_invoice
        qty = line.parts_qty
        taxes = line.service_id.taxes_id
        # invoice_line_tax_ids = self.invoice_id.fiscal_position_id.map_tax(taxes)
        account = line.service_id.property_account_income_id or line.service_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % \
                (line.service_id.name, line.service_id.id, line.service_id.categ_id.name))
        invoice_line = self.env['account.invoice.line']
        if price_unit > 0:
            data = {
                'name': line.name or line.service_id.name,
                'origin': line.maintenance_id.name,
                'uom_id': line.parts_uom.id,
                'product_id': line.service_id.id,
                'account_id': account.id,
                'price_unit': price_unit,
                'quantity': qty,
                'discount': 0.0,
                # 'account_analytic_id': line.account_analytic_id.id,
                'invoice_line_tax_ids': [(6, 0, taxes.ids)],
                'invoice_id': invoice_id.id,
                'account_analytic_id': analytic_account_id,
                'service_line_id': line.id,
            }
            account = invoice_line.get_invoice_line_account('out_invoice', line.service_id,
                                                            invoice_id.fiscal_position_id, self.env.user.company_id)
            if account:
                data['account_id'] = account.id
            return data
        else:
            return {}

    def _prepare_invoice_line_from_workshop_parts(self, line, invoice_id, analytic_account_id):
        invoice_lines = self.env['account.invoice.line'].search([('item_line_id', '=', line.id)])
        qty_invoice = 0
        qty = 0
        for invoice_line in invoice_lines:
            qty_invoice += invoice_line.quantity
        if line.parts_qty > qty_invoice:
            qty = line.parts_qty - qty_invoice
        taxes = line.parts_id.taxes_id
        invoice_line = self.env['account.invoice.line']

        account = line.parts_id.property_account_income_id or line.parts_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % \
                (line.parts_id.name, line.parts_id.id, line.parts_id.categ_id.name))


        if qty > 0:
            data = {
                # 'purchase_line_id': line.id,
                'name': line.name or line.parts_id.name,
                'origin': line.maintenance_id.name,
                'uom_id': line.parts_uom.id,
                'product_id': line.parts_id.id,
                'account_id': account.id,
                'price_unit': line.price_unit,
                'quantity': qty,
                'discount': 0.0,
                'invoice_line_tax_ids': [(6, 0, taxes.ids)],
                'invoice_id': invoice_id.id,
                'account_analytic_id': analytic_account_id,
                'item_line_id': line.id,
            }
            account = invoice_line.get_invoice_line_account('out_invoice', line.parts_id,
                                                            invoice_id.fiscal_position_id, self.env.user.company_id)
            if account:
                data['account_id'] = account.id
            return data
        else:
            return {}
