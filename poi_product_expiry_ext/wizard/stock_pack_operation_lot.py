# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import fields, models

class StockPackOperationLot(models.Model):
    _inherit = "stock.pack.operation.lot"
    use_date = fields.Datetime(string='Consumir antes de', help='Fecha antes de que el producto se empieze a malograr')
    life_date = fields.Datetime(string='Fecha Caducidad', help='Normalmente la fecha de vencimiento del producto')
