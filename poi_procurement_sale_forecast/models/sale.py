# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class ProcurementSaleForecast(models.Model):
    _name = 'procurement.sale.forecast'

    @api.one
    @api.depends('forecast_lines.procurement_id')
    def _get_procurement_count(self):
        procurement_lst = []
        for line in self.forecast_lines:
            if line.procurement_id:
                procurement_lst.append(line.procurement_id.id)
        self.procurement_count = len(procurement_lst)

    name = fields.Char(string='Name', required=True)
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    forecast_lines = fields.One2many('procurement.sale.forecast.line',
                                     'forecast_id', string="Forecast Lines")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    procurement_count = fields.Integer(string="Procurement Count",
                                       compute=_get_procurement_count)

    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('provided', 'Previsto'),
            ('confirmed', 'Confirmado'),
            ('done', 'Realizado')
        ],
        "Estado", required=True, default='draft')

    type = fields.Selection(
        [
            ('sale', 'Ventas'),
            ('purchase', 'Compras'),
        ],
        "Tipo", default='sale')

    @api.one
    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        if self.date_from >= self.date_to:
            raise exceptions.Warning(_('Error! Date to must be lower '
                                       'than date from.'))

    @api.multi
    def create_procurements(self):
        procurement_obj = self.env['procurement.order']
        procure_lst = []
        for record in self:
            for product_line in record.forecast_lines:
                if product_line.product_id and not product_line.procurement_id:
                    format_date_planned = datetime.strptime(product_line.date, DEFAULT_SERVER_DATE_FORMAT)
                    date_planned = format_date_planned + relativedelta(hours=4.0)
                    procure_id = procurement_obj.create({
                        'name': (
                            'MPS: ' + record.name + ' (' + record.date_from +
                            '.' + record.date_to + ') ' +
                            record.warehouse_id.name),
                        'date_planned': date_planned,
                        'product_id': product_line.product_id.id,
                        'product_qty': product_line.qty,
                        'product_uom': product_line.product_id.uom_id.id,
                        'location_id': record.warehouse_id.lot_stock_id.id,
                        'company_id': record.warehouse_id.company_id.id,
                        'warehouse_id': record.warehouse_id.id,
                    })
                    procure_id.signal_workflow('button_confirm')
                    procure_lst.append(procure_id.id)
                    product_line.procurement_id = procure_id.id
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'procurement.order',
            'res_ids': procure_lst,
            'domain': [('id', 'in', procure_lst)],
            'type': 'ir.actions.act_window',
            }

    @api.multi
    def show_all_forecast_procurements(self):
        procurement_list = []
        for record in self:
            for line in record.forecast_lines:
                if line.procurement_id:
                    procurement_list.append(line.procurement_id.id)
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'procurement.order',
            'res_ids': procurement_list,
            'domain': [('id', 'in', procurement_list)],
            'type': 'ir.actions.act_window',
            }

    @api.multi
    def create_procurements_plan(self, plan_ids=[]):
        procurement_obj = self.env['procurement.order']
        # forecast_obj = self.env['procurement.sale.forecast']
        procure_lst = []
        # forecast = forecast_obj.browse(plan_ids)
        date_actual = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        for record in plan_ids:
            for product_line in record.forecast_lines:
                if product_line.product_id and product_line.date >= date_actual and not product_line.procurement_id:
                    format_date_planned = datetime.strptime(product_line.date, DEFAULT_SERVER_DATE_FORMAT)
                    date_planned = format_date_planned + relativedelta(hours=4.0)
                    procure_id = procurement_obj.create({
                        'name': (
                            'MPS: ' + record.name + ' (' + record.date_from +
                            '.' + record.date_to + ') ' +
                            record.warehouse_id.name),
                        'origin': (
                            'MPS: ' + record.name + ' (' + record.date_from +
                            '.' + record.date_to + ') ' +
                            record.warehouse_id.name),
                        'date_planned': date_planned,
                        'product_id': product_line.product_id.id,
                        'product_qty': product_line.qty,
                        'product_uom': product_line.product_id.uom_id.id,
                        'location_id': record.warehouse_id.lot_stock_id.id,
                        'company_id': record.warehouse_id.company_id.id,
                        'warehouse_id': record.warehouse_id.id,
                    })
                    procure_id.signal_workflow('button_confirm')
                    procure_lst.append(procure_id.id)
                    product_line.procurement_id = procure_id.id
            record.state = 'done'

    @api.model
    def _create_procurements(self):
        date_actual = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        plan_ids = self.search([('state', '=', 'confirmed'), ('date_from', '>=', date_actual)])
        return self.create_procurements_plan(plan_ids)

class ProcurementSaleForecastLine(models.Model):

    _name = 'procurement.sale.forecast.line'

    @api.one
    @api.depends('unit_price', 'qty')
    def _get_subtotal(self):
        self.subtotal = self.unit_price * self.qty

    @api.one
    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.unit_price = self.product_id.list_price

    def _get_product_availability(self, cr, uid, ids, field_name, args, context=None):
        quant_obj = self.pool.get('stock.quant')
        res = dict.fromkeys(ids, False)
        for move in self.browse(cr, uid, ids, context=context):
            if move.state == 'done':
                res[move.id] = move.product_qty
            else:
                sublocation_ids = self.pool.get('stock.location').search(cr, uid, [('id', 'child_of', [move.location_id.id])], context=context)
                quant_ids = quant_obj.search(cr, uid, [('location_id', 'in', sublocation_ids), ('product_id', '=', move.product_id.id), ('reservation_id', '=', False)], context=context)
                availability = 0
                for quant in quant_obj.browse(cr, uid, quant_ids, context=context):
                    availability += quant.qty
                res[move.id] = min(move.product_qty, availability)
        return res


    @api.one
    @api.depends('product_id')
    def _compute_availability(self):
        quant_obj = self.env['stock.quant']
        if self.forecast_id.warehouse_id:
            sublocation_ids = self.env['stock.location'].search([('id', 'child_of', [self.forecast_id.warehouse_id.lot_stock_id.id])])
            loc_ids = sublocation_ids.ids
            if self.product_id:
                quant_ids = quant_obj.search([('location_id', 'in', loc_ids), ('product_id', '=', self.product_id.id),
                                              ('reservation_id', '=', False)])
                availability = 0
                for quant in quant_ids:
                    availability += quant.qty
                self.availability = availability
            else:
                self.availability = 0.0
        else:
            self.availability= 0.0

    @api.one
    @api.depends('product_id')
    def _compute_required(self):
        move_obj = self.env['stock.move']
        if self.forecast_id.warehouse_id:
            if self.product_id and self.date:
                date_from = self.date + " 00:00:00"
                date_to = self.date + " 23:59:59"

                move_ids = move_obj.search([('location_id', 'in', [self.forecast_id.warehouse_id.lot_stock_id.id]), ('product_id', '=', self.product_id.id),
                                              ('state', 'in', ('waiting', 'confirmed', 'assigned')), ('date_expected', '<=', date_to), ('date_expected', '>=', date_from)])
                required = 0
                for move in move_ids:
                    required += move.product_qty
                self.required_qty = required
            else:
                self.required_qty = 0.0
        else:
            self.required_qty = 0.0

    @api.one
    @api.depends('product_id')
    def _compute_batch(self):
        bom_obj = self.env['mrp.bom']
        for line in self:
            if line.product_id:
                bom_data = bom_obj.search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id), ('state', '=', 'active')])
                if bom_data:
                    line.batch_qty = bom_data[0].product_qty
                else:
                    line.batch_qty = 0.0

    user_id = fields.Many2one('res.users', string='Vendedor', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)
    availability = fields.Float(
        compute=_compute_availability, string='Cant. Actual', readonly=True, help=u"Cantidad disponible según almacén seleccionado en la cabezera")

    required_qty = fields.Float(
        compute=_compute_required, string='Requerido', readonly=True, help=u"Cantidad requerida en almacén ya sea para venta o producción según el campo 'Fecha'")

    batch_qty = fields.Float(
        compute=_compute_batch, string='Cantidad Batch', readonly=True, help=u"Cantidad batch si el producto tiene asignado una receta de producción")

    batch_qty_plan = fields.Float(string='Cantidad Bach Planificado')
    product_id = fields.Many2one('product.product', string='Product')
    product_category_id = fields.Many2one('product.category',
                                          string='Product Category')
    qty = fields.Float('Quantity', default=0,
                       digits_compute=dp.get_precision('Product Unit of'
                                                       ' Measure'), help=u"Ponga Cantidad 1,2,3, etc. y en función del campo 'Cantidad Batch' al regla sera Cantidad Planificada = Cantidad Planificada*Cantidad Batch")

    qty_plan = fields.Float('Quantity Plan', default=1,
                       digits_compute=dp.get_precision('Product Unit of'
                                                       ' Measure'))
    unit_price = fields.Float('Unit Price',
                              digits_compute=dp.get_precision('Product Price'))
    subtotal = fields.Float('Subtotal', compute=_get_subtotal, store=True,
                            digits_compute=dp.get_precision('Product Price'))
    partner_id = fields.Many2one("res.partner", string="Partner", domain=[('customer', '=', True)])
    date_from = fields.Date(string="Date from", store=True,
                            related="forecast_id.date_from")
    date_to = fields.Date(string="Date to", related="forecast_id.date_to",
                          store=True)
    forecast_id = fields.Many2one('procurement.sale.forecast',
                                  string='Forecast')
    procurement_id = fields.Many2one('procurement.order', string="Procurement")
    date = fields.Date("Date", required=True)
    type = fields.Selection(string=u"Tipo", related="forecast_id.type")
    state = fields.Selection(string=u"Tipo", related="forecast_id.state", default='draft')
    _order = 'date asc'

    @api.model
    def create(self, vals):
        res = super(ProcurementSaleForecastLine, self).create(vals)
        if vals.get('batch_qty_plan') is not None:
            res.qty = res.batch_qty_plan * res.batch_qty
        return res

    @api.multi
    def write(self, vals):
        res = super(ProcurementSaleForecastLine, self).write(vals)
        if vals.get('batch_qty_plan') is not None:
            self.qty = vals['batch_qty_plan'] * self.batch_qty
        return res


    @api.onchange('batch_qty_plan')
    def onchange_batch_qty_plan(self):
        for line in self:
            if line.batch_qty_plan > 0 and line.batch_qty:
                line.qty = line.batch_qty_plan * line.batch_qty

    @api.multi
    def request_procurement(self):
        self.ensure_one()
        value_dict = {'product_id': self.product_id.id,
                      'uom_id': self.product_id.uom_id.id,
                      'date_planned': self.date,
                      'qty': self.qty,
                      'warehouse_id': self.forecast_id.warehouse_id.id
                      }
        res_id = self.env['make.procurement'].create(value_dict)
        return {'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'make.procurement',
                'res_id': res_id.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                }
