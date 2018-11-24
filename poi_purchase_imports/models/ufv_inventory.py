# © 2013 Joaquín Gutierrez
# © 2014-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3


from odoo import models, fields, exceptions, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class PoiUfvInventory(models.Model):
    _inherit = "poi.ufv.inventory"

    @api.multi
    def import_stock(self):
        if self.ufv_final <= 0:
            raise UserError(_('Considere actualizar el valor UFV en la fecha %s.') % (self.date))
        self.product_lines.unlink()
        lines = self.product_lines.browse([])
        # El costo de aplicar UFV no se aplica a ubicación que son consideras transito sin valoración
        # De esta forma se evita actualizar producto en ubicaciones solo inventariables y contabilizables para la empresa
        quants = self.env['stock.quant'].search([('location_id.usage', '=', 'internal'), ('product_id.ufv_value', '=', True), ('location_id.account_import', '=', False)])
        for quant in quants:
            if quant.location_id.usage == 'internal' and quant.qty > 0:
                value_line = {
                    'ufv_final': self.ufv_final,
                    'ufv_inicial': self.get_ufv_date(quant.product_id.id),
                    'product_id': quant.product_id.id,
                    'lot_id': quant.lot_id.id,
                    'quant_id': quant.id,
                    'location_id': quant.location_id.id,
                    'qty': quant.qty,
                    'method': quant.product_id.cost_method,
                    'price_unit': quant.inventory_value/quant.qty,
                    'total_price': quant.inventory_value,
                    'ufv_import': 0,
                    'new_price': 0,
                    'date': self.date,
                }
                lines += lines.new(value_line)

        self.product_lines = lines
        self.state = 'calculated'
        return True
