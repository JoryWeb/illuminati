# © 2015 Akretion (http://www.akretion.com).
# @author Valentin CHEMIERE <valentin.chemiere@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None,
                                  owner_id=None, strict=True):
        if self.sale_line_id.lot_id:
            lot_id_req = self.sale_line_id.lot_id
            res = super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id,
                                                                   lot_id=lot_id_req, package_id=package_id,
                                                                   owner_id=owner_id, strict=strict)
        else:
            res = super(StockMove, self)._update_reserved_quantity(need, available_quantity, location_id,
                                                                   lot_id=lot_id, package_id=package_id,
                                                                   owner_id=owner_id,
                                                                   strict=strict)
        return res
