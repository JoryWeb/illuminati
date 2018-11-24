##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import models, api, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    embarque = fields.Char(string=u"N° Embarque", states={'done': [('readonly', True)]}, copy=False)

