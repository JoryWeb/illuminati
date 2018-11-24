# © 2016 Eficent Business and IT Consulting Services S.L.
#   (<http://www.eficent.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api

class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    analytic_account_id = fields.Many2one(
        string=u'Cuenta analítica',
        comodel_name='account.analytic.account',
    )

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    analytic_account_id = fields.Many2one(
        string=u'Cuenta analítica',
        comodel_name='account.analytic.account',
    )

    @api.multi
    def product_id_change(self, product_id, product_qty=0):
        result = super(MrpProduction, self).product_id_change(
            product_id, product_qty=product_qty)
        if product_id:
            bom_obj = self.env['mrp.bom']
            bom_id = bom_obj._bom_find(product_id=product_id, properties=[])
            if bom_id:
                bom_point = bom_obj.browse(bom_id)
                result['value'].update(
                    {
                        'analytic_account_id': bom_point.analytic_account_id.id,
                     })
        return result

    @api.model
    def _make_consume_line_from_data(self, production, product, uom_id, qty):

        move_id = super(MrpProduction, self)._make_consume_line_from_data(
            production, product, uom_id, qty)
        obj_move = self.env["stock.move"]
        move = obj_move.browse(move_id)
        move.write(
            {"analytic_account_id": production.analytic_account_id.id}
        )
        return move_id

    @api.model
    def _make_production_produce_line(self, production):
        move = super(MrpProduction,
                     self)._make_production_produce_line(production)
        move_data = self.env['stock.move'].browse(move)
        move_data.analytic_account_id = production.analytic_account_id.id
        return move