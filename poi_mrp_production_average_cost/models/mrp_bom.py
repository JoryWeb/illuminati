# © 2014-2015 Avanzosc
# © 2014-2015 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api, fields


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    product_standard_price = fields.Float(string="Costo",
                                          related="product_id.standard_price")


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    product_standard_price = fields.Float(string="Costo",
                                          related="product_id.standard_price")
