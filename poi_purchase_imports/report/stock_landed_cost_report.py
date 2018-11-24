from odoo import fields, models, tools


class StockLandedCostReport(models.Model):
    _name = "stock.landed.cost.report"
    _description = "Reporte de Costes en Destino"
    _auto = False
    landed_id = fields.Many2one('stock.landed.cost', string=u'Coste en Destino', readonly=False)
    name = fields.Char(string="Nombre", readonly=True)
    amount_total = fields.Float(string='Monto', readonly=True)
    description = fields.Char(string="Nombre", readonly=True)
    account_journal_id = fields.Many2one('account.journal', string=u'Diario', readonly=True)
    account_move_id = fields.Many2one('account.move', string=u'Asiento Contable', readonly=True)
    stock_picking_id = fields.Many2one('stock.picking', string=u'Transferencia', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_landed_cost_report')
        cr.execute("""
        create or replace view stock_landed_cost_report as (
        select
          row_number() OVER () as id,
          t0.id as landed_id,
          t0.name,
          t0.amount_total,
          t0.description,
          t0.account_journal_id,
          t0.account_move_id,
          t1.stock_picking_id
        from stock_landed_cost t0
        inner join stock_landed_cost_stock_picking_rel t1 on t1.stock_landed_cost_id = t0.id
        )""")
