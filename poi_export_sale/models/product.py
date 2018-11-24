
from odoo import api, fields, models, _

class ProductoTemplate(models.Model):
    _inherit = 'product.template'

    state_id = fields.Many2one("res.country.state", string='Origen Producto', ondelete='restrict')
    country_id = fields.Many2one('res.country', string=u'País', ondelete='restrict')

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            return {'domain': {'state_id': [('country_id', '=', self.country_id.id)]}}
        else:
            return {'domain': {'state_id': []}}
