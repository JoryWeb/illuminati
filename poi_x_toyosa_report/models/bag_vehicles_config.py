import logging
from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class BagVehiclesConfig(models.Model):
    _name = 'bag.vehicles.config'

    date = fields.Date('Fecha', default=fields.Date.today())
    list_ids = fields.One2many('bag.list.price', 'config_id', 'Listas de Precios')

class BagListPrice(models.Model):
    _name = 'bag.list.price'

    config_id = fields.Many2one('bag.vehicles.config', 'Confirguracion')
    pricelist_id = fields.Many2one('product.pricelist', 'Lista de Precios')
