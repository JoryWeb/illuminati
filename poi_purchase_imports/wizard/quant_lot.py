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

class QuantLotWizard(models.TransientModel):
    _name = 'quant.lot.wizard'
    _description = 'Lista de Quants Disponibles'

    picking_id = fields.Many2one('stock.picking', 'Picking')
    base_date = fields.Date('Fecha Primera Entrega', required=True)
    item_ids = fields.One2many('quant.lot.wizard.items', 'quantlot_id', 'Lista de Chasis Disponibles')

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(QuantLotWizard, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('poi.purchase.imports.picking'), 'Bad context propagation'
        picking_id, = picking_ids
        picking = self.pool.get('poi.purchase.imports.picking').browse(cr, uid, picking_id, context=context)
        items = []
        items2 = []
        if not picking.picking_id.move_lines_related:
            raise exceptions.Warning(
            _('Error! \n No existe lotes asignados'))
        for move in picking.picking_id.move_lines_related:
            for quant in move.quant_ids:
                if quant.location_id.id == picking.location_dest_id.id:
                    item2 = {
                        'move_id': move.id,
                        'quant_id': quant.id,
                        'lot_id': quant.lot_id.id,
                        'location_id': quant.location_id.id,
                        'qty': quant.qty,
                    }
                    items2.append((0, 0, item2))
        res.update(item_ids=items2)
        res.update(base_date=picking.picking_id.min_date)
        return res

class QuantLotWizardItems(models.TransientModel):
    _name = 'quant.lot.wizard.items'
    _description = 'Items para plan de entrega'

    quantlot_id = fields.Many2one('quant.lot.wizard', 'Lista de Lotes')
    move_id = fields.Many2one('stock.move', 'Movimiento', readonly=True)
    quant_id = fields.Many2one('stock.quant', 'Quant', readonly=True)
    lot_id = fields.Many2one('stock.production.lot', u'Lote', readonly=True)
    location_id = fields.Many2one('stock.location', u'Ubicación', readonly=True)
    qty = fields.Float('Cantidad', readonly=True)

