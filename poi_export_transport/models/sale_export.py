# -*- encoding: utf-8 -*-
from odoo import models, api, fields, registry, _
import odoo.addons.decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)


class SaleOrderExportTag(models.Model):
    _name = 'sale.order.export.tag'
    _description = 'Naturaleza del Producto'

    name = fields.Char(required=True)
    color = fields.Integer('Color Index')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # _authmode = True
    @api.one
    def _compute_total_weight(self):
        self.total_weight = sum([x.total_weight for x in self.order_line])

    sale_export = fields.Boolean('Venta de Exportaciones', default=False)

    total_weight = fields.Float(
        compute=_compute_total_weight, string='Peso Total (Kg.)', readonly=True,
        digits_compute=dp.get_precision('Stock Weight'))

    tag_ids = fields.Many2many('sale.order.export.tag', 'sale_order_export_tag_rel', string='Naturaleza Del Producto')

    other_tag = fields.Char('Otro')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo' and vals.get('sale_export') is not True:
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or '/'
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.order.exports') or '/'
        return super(SaleOrder, self).create(vals)

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        inv_ids = super(SaleOrder, self).action_invoice_create(grouped=grouped, final=final)
        if self.sale_export:
            invoice_obj = self.env['account.invoice']
            for inv in invoice_obj.browse(inv_ids):
                inv.tipo_fac = '13'
        return inv_ids


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _compute_total_weight(self):
        for s in self:
            s.total_weight = s.weight * s.product_uom_qty

    weight = fields.Float('Peso', readonly=True, related="product_id.weight")

    total_weight = fields.Float(
        compute="_compute_total_weight", string="Peso Total",
        digits_compute=dp.get_precision('Stock Weight'),
        help="Total Peso Kg.")
