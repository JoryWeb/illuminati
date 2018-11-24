##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.model
    def _batch_equivalente(self):
        for production in self:
            if production.bom_id.product_qty > 0:
                production.batch = round(production.product_qty / production.bom_id.product_qty, 2)
            else:
                production.batch = 0.0

    batch = fields.Float(string=u"Batch equivalente", compute='_batch_equivalente')

class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.production.workcenter.line'

    date_init_real = fields.Datetime(string="Fecha inicio reportado")
    date_stop_real = fields.Datetime(string="Fecha fin reportado")
    code = fields.Char(string=u"Código", related="workcenter_id.code")
