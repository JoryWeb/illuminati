##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2004-TODAY odoo S.A. <http://www.odoo.com>
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

class UpdateFobPickingWizard(models.TransientModel):
    _name = 'update.fob.picking.wizard'
    _description = 'Actualizar Orden'

    move_line_id = fields.Many2one("stock.move", string=u"Movimiento de Existencia")
    price_unit_fob = fields.Float("Precio Unidad")
    price_flete = fields.Float("Costo Flete")
    price_seguro = fields.Float("Costo Seguro")
    price_unit = fields.Float("Precio Unidad Compra")
    currency_id = fields.Many2one('res.currency', 'Moneda', required=True, readonly=True)

    @api.onchange('price_unit_fob')
    def onchange_price_unit_fob(self):
        for move in self:
            move.price_unit = move.price_unit_fob + move.price_flete + move.price_seguro

    @api.onchange('price_flete')
    def onchange_price_unit_flete(self):
        for move in self:
            move.price_unit = move.price_unit_fob + move.price_flete + move.price_seguro

    @api.onchange('price_seguro')
    def onchange_price_unit_seguro(self):
        for move in self:
            move.price_unit = move.price_unit_fob + move.price_flete + move.price_seguro

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(UpdateFobPickingWizard, self).default_get(cr, uid, fields, context=context)
        line_id = context.get('active_ids', [])
        if not line_id or len(line_id) != 1:
            return res
        move = self.pool.get('stock.move').browse(cr, uid, line_id, {})
        res.update(move_line_id=move.id)
        res.update(price_unit_fob=move.purchase_line_id.price_unit)
        res.update(price_unit=move.purchase_line_id.price_unit)
        res.update(currency_id=move.purchase_line_id.order_id.currency_id.id)
        return res

    @api.multi
    def update_line(self):
        """
        Actualizar los datos con el respectivo precio unitario
        """
        context = self._context or {}
        line = self.env['stock.move'].browse(context.get('active_ids', []))

        price_unit_purchase = self.currency_id.compute(self.price_unit, line.company_id.currency_id , round=False)
        price_unit_flete = self.currency_id.compute(self.price_flete, line.company_id.currency_id, round=False)
        price_unit_seguro = self.currency_id.compute(self.price_seguro, line.company_id.currency_id, round=False)

        line.price_unit = price_unit_purchase
        line.price_flete = price_unit_flete
        line.price_seguro = price_unit_seguro

        price_unit_purchase = self.currency_id.compute(self.price_unit, line.purchase_line_id.order_id.currency_id, round=False)
        price_unit_flete = self.currency_id.compute(self.price_flete, line.purchase_line_id.order_id.currency_id, round=False)
        price_unit_seguro = self.currency_id.compute(self.price_seguro, line.purchase_line_id.order_id.currency_id, round=False)

        line.purchase_line_id.price_unit = price_unit_purchase
        line.purchase_line_id.price_transporte = price_unit_flete + price_unit_seguro
        line.purchase_line_id.price_fabrica = price_unit_purchase - price_unit_flete - price_unit_seguro
        line.purchase_line_id.price_flete = price_unit_flete
        line.purchase_line_id.price_seguro = price_unit_seguro

        # Buscar los packs que corresponden y actualizar el costo para una correcta división de los packs
        move_pack = self.env['stock.move.operation.link'].search([('move_id', '=', line.id)])
        for m_p in move_pack:
            m_p.price_unit = line.price_unit
        return {'type': 'ir.actions.act_window_close'}


