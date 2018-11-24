
from odoo import api, exceptions, fields, models, _
import operator

ops = {'=': operator.eq,
       '!=': operator.ne,
       '<=': operator.le,
       '>=': operator.ge,
       '>': operator.gt,
       '<': operator.lt}

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def _default_location(self):
        for lot in self:
            if lot.product_id.tracking == 'serial':
                if lot.quant_ids:
                    for quant in lot.quant_ids:
                        location_id = quant.location_id.id
                    lot.location_id = location_id
                else:
                    lot.location_id = False

    @api.multi
    def _search_location_lot(self, operator, value):
        if operator not in ops.keys():
            raise exceptions.Warning(
                _(
                    'Operador %s no permito para el valor %s, puede hacer clic sobre la flecha -> para ver las resultados y seleccionar uno especifico')
                % (operator, value)
            )
        found_ids = []
        val = value
        self.env.cr.execute("""
                select lot_id from stock_quant where location_id = """ + str(val) + """ and lot_id NOTNULL group by lot_id
                        """)
        for lot_id in self.env.cr.fetchall():
            found_ids.append(lot_id[0])

        return [('id', 'in', found_ids)]

    location_id = fields.Many2one('stock.location', string=u"Ubicación Actual", compute='_default_location',
                                  search="_search_location_lot")

    #
    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for lot in self:
            if lot.location_id:
                name = lot.name + ' [' + lot.location_id.name + '] '
                result.append((lot.id, name))
            else:
                name = lot.name
                result.append((lot.id, name))
        return result

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        " Overwrite the read_group in order to sum the function field 'inventory_value' in group by "
        # TDE NOTE: WHAAAAT ??? is this because inventory_value is not stored ?
        # TDE FIXME: why not storing the inventory_value field ? company_id is required, stored, and should not create issues
        res = super(StockProductionLot, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                         orderby=orderby, lazy=lazy)
        if 'location_id' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    location_id = 0
                    for line2 in lines:
                        location_id = line2.location_id.id
                    line['location_id'] = location_id

        return res