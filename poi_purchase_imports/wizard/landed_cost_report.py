##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.odoo.com>
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

from odoo import models, fields, api, exceptions, _
from odoo.tools.translate import _
from datetime import datetime, timedelta
class LandedCostReport(models.TransientModel):
    _name = 'landed.cost.report'
    _description = 'Costos en destino aplicado al picking'

    picking_id = fields.Many2one('stock.picking',string='Transferencia')
    item_ids = fields.One2many('landed.cost.report.line', 'landed_id', 'Lista de Costos en Destino')

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(LandedCostReport, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('poi.purchase.imports.picking'), 'Bad context propagation'
        picking_id, = picking_ids
        picking = self.pool.get('poi.purchase.imports.picking').browse(cr, uid, picking_id, context=context)
        if not picking.picking_id.move_lines_related:
            raise exceptions.Warning(
            _('Error! \n No existe lotes asignados'))
        cr.execute("select * from stock_landed_cost_stock_picking_rel where stock_picking_id = "+str(picking.picking_id.id)+"")
        result = cr.fetchall()
        items = []
        for result_line in result:
            landed = self.pool.get('stock.landed.cost').browse(cr, uid, result_line[0], context=context)
            items2 = {
                'cost_id': landed.id,
                'date': landed.date,
                'amount_total': landed.amount_total,
                'state': landed.state,
            }
            items.append((0, 0, items2))
        res.update(picking_id = picking.picking_id.id)
        res.update(item_ids = items)
        return res

class LandedCostReportLine(models.TransientModel):
    _name = 'landed.cost.report.line'
    landed_id = fields.Many2one('landed.cost.report', 'Padre Costos')
    cost_id = fields.Many2one('stock.landed.cost', 'Costes en Destino')
    date = fields.Date(string="Fecha")
    amount_total = fields.Float(string="Monto Total")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Posted'), ('cancel', 'Cancelled')], string="Estado")

