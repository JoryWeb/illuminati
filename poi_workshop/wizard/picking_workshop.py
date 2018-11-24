##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2016 CodUP (<http://codup.com>).
#
##############################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class PickingWorkshop(models.TransientModel):
    _name = 'picking.workshop'
    _description = 'Picking Route Workshop'

    route_id = fields.Many2one('stock.location.route', string='Usar Ruta')
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacen')
    sucursal_id = fields.Many2one('stock.warehouse', string='Sucursal PDS o Taller', required=True)

    @api.model
    def default_get(self, fields):
        res = super(PickingWorkshop, self).default_get(fields)
        res['active_model'] = self._context.get('active_model')
        res['active_id'] = self._context.get('active_id')
        picking = self.env['stock.picking'].browse(res['active_id'])
        res['warehouse_id'] = picking.picking_type_id.warehouse_id.id
        if 'domain' not in res:
            res['domain'] = {}
        #active_record = self.env[res['active_model']].browse(res['active_id'])
        #if res['active_model'] == 'stock.picking':
        #    all_routes += active_record.picking_type_id.warehouse_id.get_all_routes_for_wh(active_record.picking_type_id.warehouse_id)
        #    res['domain']['route_id'] = [('warehouse_id', '=', 1056)]
        return res

    @api.multi
    def procurement_create(self):
        active_id = self._context.get('active_id')
        if active_id:
            picking = self.env['stock.picking'].browse(self._context.get('active_id'))
            proc_obj = self.env['procurement.group'].search([('name', '=', picking.name)])

            # Verificamos si los picking del abastecimiento han sido cancelados
            # para generar o no un nueva solicitud del chasis al almacén de taller
            picks = []
            if proc_obj:
                picks = self.env['stock.picking'].search([('group_id', '=', proc_obj[0].id)])
            pick_ok = False
            if not picks:
                pick_ok = True
            for pick in picks:
                if pick.state in ('cancel'):
                    pick_ok = True
                else:
                    pick_ok = False

            ot_ids = self.env['workshop.order'].search([('origin', '=', picking.origin)])
            ot_ok = False
            if not ot_ids:
                ot_ok = True
            for ot_id in ot_ids:
                if ot_id.state in ('cancel'):
                    ot_ok = True
                else:
                    ot_ok = False

            sale = False
            work_data = False
            if pick_ok:
                group_ab = self.env["procurement.group"].create({'name': picking.name})
                for line in picking.move_lines:
                    #Obtener pedido de ventas
                    sale = line.procurement_id.sale_line_id.order_id
                    pull_id = False
                    if len(self.route_id.pull_ids) <= 1:
                        for pulls in self.route_id.pull_ids:
                            pull_id = pulls.id
                        vals = {
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'product_qty': line.product_uom_qty,
                            'warehouse_id': picking.picking_type_id.warehouse_id.id,
                            'location_id': picking.picking_type_id.warehouse_id.lot_stock_id.id,
                            'name': picking.name,
                            'route_ids': [(4, self.route_id.id)],
                            'group_id': group_ab.id,
                            'rule_id': pull_id,
                            'date_planned': picking.min_date,
                            'restrict_lot_id': line.restrict_lot_id.id,
                        }
                    else:
                        vals = {
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'product_qty': line.product_uom_qty,
                            'warehouse_id': picking.picking_type_id.warehouse_id.id,
                            'location_id': picking.picking_type_id.warehouse_id.lot_stock_id.id,
                            'name': picking.name,
                            'route_ids': [(4, self.route_id.id)],
                            'group_id': group_ab.id,
                            'origin': picking.name,
                            'date_planned': picking.min_date,
                            'restrict_lot_id': line.restrict_lot_id.id,
                        }
                    procu = self.env['procurement.order'].create(vals)
                    procu.run()
                    if ot_ok:
                        # Aqui creamos la solicitud de Mantenimiento en Taller
                        vehicle = self.env['poi.vehicle'].search([('chasis_id', '=', line.restrict_lot_id.id)])
                        if vehicle:
                            value_workshop = {
                                'asset_id': vehicle[0].id,
                                'description': 'Pedido de ventas' + line.origin,
                                'origin': line.origin,
                                'partner_id': line.restrict_lot_id.partner_id.id,
                                'email': line.restrict_lot_id.partner_id.email,
                                'phone': line.restrict_lot_id.partner_id.phone or line.restrict_lot_id.partner_id.mobile,
                                'marca': line.restrict_lot_id.marca.id,
                                'modelo': line.restrict_lot_id.modelo.id,
                                'n_chasis': line.restrict_lot_id.name,
                                'pricelist_id': picking.partner_id.property_product_pricelist and picking.partner_id.property_product_pricelist.id or False,
                                'warehouse_id': self.sucursal_id.id,
                            }
                            work_data = self.env['workshop.order'].create(value_workshop)
                        else:
                            vehicle_data = {
                                'name': line.restrict_lot_id.placa or line.restrict_lot_id.name,
                                'texto': 'SO: ' + line.origin,
                                'vendor_id': line.restrict_lot_id.partner_id.id,
                                'modelo': line.restrict_lot_id.modelo.id,
                                'anio_modelo': line.restrict_lot_id.anio_modelo.id,
                                'anio_fabricacion': line.restrict_lot_id.anio_fabricacion.id,
                                'edicion': line.restrict_lot_id.edicion,
                                'colorinterno': line.restrict_lot_id.colorinterno.id,
                                'colorexterno': line.restrict_lot_id.colorexterno.id,
                                'marca': line.restrict_lot_id.marca.id,
                                'n_motor': line.restrict_lot_id.n_motor,
                                'n_llaves': line.restrict_lot_id.n_llaves,
                                'cant_llaves': line.restrict_lot_id.cant_llaves,
                                'chasis_id': line.restrict_lot_id.id,
                                'n_chasis': line.restrict_lot_id.name,
                            }
                            vehicle_obj = self.env['poi.vehicle'].create(vehicle_data)
                            value_workshop = {
                                'asset_id': vehicle_obj.id,
                                'description': 'Por Pedido: ' + line.origin,
                                'origin': line.origin,
                                'partner_id': line.restrict_lot_id.partner_id.id,
                                'email': line.restrict_lot_id.partner_id.email,
                                'phone': line.restrict_lot_id.partner_id.phone or line.restrict_lot_id.partner_id.mobile,
                                'marca': line.restrict_lot_id.marca.id,
                                'modelo': line.restrict_lot_id.modelo.id,
                                'n_chasis': line.restrict_lot_id.name,
                                'pricelist_id': picking.partner_id.property_product_pricelist and picking.partner_id.property_product_pricelist.id or False,
                                'warehouse_id': self.sucursal_id.id,
                            }
                            work_data = self.env['workshop.order'].create(value_workshop)

                if sale and work_data:
                    for parts in sale.order_line_a:
                        val_parts = {
                            'parts_id': parts.product_id.id,
                            'parts_qty': parts.product_uom_qty,
                            'parts_uom': parts.product_uom.id,
                            'price_unit': parts.price_unit,
                            'maintenance_id': work_data.id,
                            'cargo': 'interno',
                            'origin': sale.name,
                        }
                        self.env['workshop.order.parts.line'].create(val_parts)
                picking.group_maintenance = group_ab.id
            elif ot_ok:
                for line in picking.move_lines:
                    sale = line.procurement_id.sale_line_id.order_id
                    # Aqui creamos la solicitud de Mantenimiento en Taller
                    vehicle = self.env['poi.vehicle'].search([('chasis_id', '=', line.restrict_lot_id.id)])
                    if vehicle:
                        value_workshop = {
                            'asset_id': vehicle[0].id,
                            'description': 'Pedido de ventas' + line.origin,
                            'origin': line.origin,
                            'partner_id': line.restrict_lot_id.partner_id.id,
                            'email': line.restrict_lot_id.partner_id.email,
                            'phone': line.restrict_lot_id.partner_id.phone or line.restrict_lot_id.partner_id.mobile,
                            'marca': line.restrict_lot_id.marca.id,
                            'modelo': line.restrict_lot_id.modelo.id,
                            'n_chasis': line.restrict_lot_id.name,
                            'pricelist_id': picking.partner_id.property_product_pricelist and picking.partner_id.property_product_pricelist.id or False,
                            'warehouse_id': self.sucursal_id.id,
                        }
                        work_data = self.env['workshop.order'].create(value_workshop)
                    else:
                        vehicle_data = {
                            'name': line.restrict_lot_id.placa or line.restrict_lot_id.name,
                            'texto': 'SO: ' + line.origin,
                            'vendor_id': line.restrict_lot_id.partner_id.id,
                            'modelo': line.restrict_lot_id.modelo.id,
                            'anio_modelo': line.restrict_lot_id.anio_modelo.id,
                            'anio_fabricacion': line.restrict_lot_id.anio_fabricacion.id,
                            'edicion': line.restrict_lot_id.edicion,
                            'colorinterno': line.restrict_lot_id.colorinterno.id,
                            'colorexterno': line.restrict_lot_id.colorexterno.id,
                            'marca': line.restrict_lot_id.marca.id,
                            'n_motor': line.restrict_lot_id.n_motor,
                            'n_llaves': line.restrict_lot_id.n_llaves,
                            'cant_llaves': line.restrict_lot_id.cant_llaves,
                            'chasis_id': line.restrict_lot_id.id,
                            'n_chasis': line.restrict_lot_id.name,
                        }
                        vehicle_obj = self.env['poi.vehicle'].create(vehicle_data)
                        value_workshop = {
                            'asset_id': vehicle_obj.id,
                            'description': 'Por Pedido: ' + line.origin,
                            'origin': line.origin,
                            'partner_id': line.restrict_lot_id.partner_id.id,
                            'email': line.restrict_lot_id.partner_id.email,
                            'phone': line.restrict_lot_id.partner_id.phone or line.restrict_lot_id.partner_id.mobile,
                            'marca': line.restrict_lot_id.marca.id,
                            'modelo': line.restrict_lot_id.modelo.id,
                            'n_chasis': line.restrict_lot_id.name,
                            'pricelist_id': picking.partner_id.property_product_pricelist and picking.partner_id.property_product_pricelist.id or False,
                            'warehouse_id': self.sucursal_id.id,
                        }
                        work_data = self.env['workshop.order'].create(value_workshop)

                    if sale and work_data:
                        for parts in sale.order_line_a:
                            val_parts = {
                                'parts_id': parts.product_id.id,
                                'parts_qty': parts.product_uom_qty,
                                'parts_uom': parts.product_uom.id,
                                'price_unit': parts.price_unit,
                                'maintenance_id': work_data.id,
                                'cargo': 'interno',
                                'origin': sale.name,
                            }
                            self.env['workshop.order.parts.line'].create(val_parts)
            else:
                raise Warning('Ya se solicito Orden de Trabajo y Transferencia a Taller para esta entrega')

        return {'type': 'ir.actions.act_window_close',}
