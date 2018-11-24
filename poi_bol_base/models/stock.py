##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
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
##############################################################################AIzaSyBiaYluG8pVYxgKRGcc4uEbtgE9q8la0dw

from openerp import models, fields, api
from lxml import etree


# No aplicable a V11 no existe el campo move_history_ids
# class stock_move(models.Model):
#     _inherit = 'stock.move'
#
#     def _get_accounting_data_for_valuation(self):
#         """Overrides function in order to cover Returns scenarios when working with Anglo-Saxon accounting"""
#         journal_id, acc_src, acc_dest, acc_variation = super(stock_move, self)._get_accounting_data_for_valuation()
#         if self.move_history_ids:
#             if len(self.move_history_ids) == 1 and self.move_history_ids[0].picking_id.type != self.picking_id.type and move.picking_id.type in ('internal', 'in'):
#                 acc_src, acc_dest = acc_dest, acc_src
#         return journal_id, acc_src, acc_dest, acc_variation


class stock_location(models.Model):
    _inherit = 'stock.location'

    @api.model
    def name_search(self, cr, user, name='', args=None, operator='ilike', limit=100):

        if not args:
            args = []
        if limit == 0 and operator == 'ilike':
            limit = 80

        if name:
            ids = []
            ids.extend(self.search([('name', operator, name)] + args, limit=limit))
            if len(ids) < limit:
                # we may underrun the limit because of dupes in the results, that's fine
                ids.extend(self.search([('location_id.name', operator, name)] + args, limit=limit))

        else:
            ids = self.search(args, limit=limit)

        result = ids.name_get()
        return result
