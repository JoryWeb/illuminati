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

class PurchaseLineUpdateWizard(models.TransientModel):
    _name = 'poi.purchase.line.update.wizard'
    _description = 'Actualizar Orden'

    order_line_id = fields.Many2one("purchase.order.line", string=u"Linea de orden")
    edicion = fields.Char("ED")
    partida = fields.Char(string="Partida Arancelaria")


    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(PurchaseLineUpdateWizard, self).default_get(cr, uid, fields, context=context)
        line_id = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not line_id or len(line_id) != 1:
            return res

        res.update(order_line_id=line_id)

        return res


    @api.multi
    def update_line(self):
        """
        Actualizar los datos correspondientes y el respectivo lote
        """

        context = self._context or {}
        line = self.env['purchase.order.line'].browse(context.get('active_ids', []))
        line.edicion = self.edicion
        line.partida = self.partida

        return {'type': 'ir.actions.act_window_close'}


