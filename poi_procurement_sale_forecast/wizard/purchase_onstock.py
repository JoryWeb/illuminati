##############################################################################
#
#    Odoo
#    Copyright (C) 2013-2016 CodUP (<http://codup.com>).
#
##############################################################################

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError, Warning
import time

class PurchaseOnStock(models.TransientModel):
    _name = 'purchase.onstock'
    _description = 'Compras'
    partner_id = fields.Many2one('res.partner', string='Proveedor')
    date_purchase = fields.Date(string='Fecha Prevista')

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOnStock, self).default_get(fields)
        return res

    @api.multi
    def purchase_create(self):

        context = dict(self._context or {})
        active_ids = context.get('active_ids')
        self._cr.execute(
            """select product_id, location_id, sum(cant_solicitada) as total_solicitado
                            from poi_prevision_insumos_report
                            where id IN %s and cant_solicitada > 0
                            group by product_id, location_id""", (tuple(active_ids), ))
        res = self._cr.dictfetchall()
        locations_id = []
        for r in res:
            locations_id.append(r['location_id'])

        # Borrar duplicados en ubicaciones
        locations_id = list(set(locations_id))
        # hacer for por las ubicaciones
        for loc_id in locations_id:
            type_pick = self.env['stock.picking.type'].search([('default_location_dest_id', '=', loc_id), ('code', '=', 'incoming')])
            val_purchase = {
                'partner_id': self.partner_id.id,
                'company_id': self.partner_id.company_id.id,
                'currency_id': self.partner_id.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id,
                'origin': 'Reporte Prevision stocks',
                'payment_term_id': self.partner_id.property_supplier_payment_term_id.id,
                'date_order': self.date_purchase,
                'picking_type_id': type_pick[0].id
            }
            po = self.env['purchase.order'].create(val_purchase)
            self._cr.execute("""select product_id, location_id, sum(cant_solicitada) as total_solicitado
                                from poi_prevision_insumos_report
                                where id IN %s and cant_solicitada > 0 and location_id = %s
                                group by product_id, location_id;""", (tuple(active_ids), loc_id))
            res_prod = self._cr.dictfetchall()
            for r_p in res_prod:
                product_obj = self.env['product.product'].browse(r_p['product_id'])
                line_po = {
                    'name': product_obj.name,
                    'product_qty': r_p['total_solicitado'],
                    'product_id': product_obj.id,
                    'product_uom': product_obj.uom_po_id.id,
                    'price_unit': 1,
                    'date_planned': self.date_purchase,
                    #'taxes_id': [(6, 0, taxes_id.ids)],
                    #'procurement_ids': [(4, self.id)],
                    'order_id': po.id,
                }
                self.env['purchase.order.line'].create(line_po)
        return {'type': 'ir.actions.act_window_close',}


