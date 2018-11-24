from odoo import tools
from odoo import api, fields, models

class ChasisPaymentHistoryReport(models.Model):
    _name = "chasis.payment.history.report"
    _description = "Reporte de historia de pagos"
    _auto = False

    lot_id = fields.Many2one('stock.production.lot', string=u'Serie/Chasis', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'Cliente', readonly=True)
    sale_id = fields.Many2one('sale.order', string="Pedido de Ventas", readonly=True)
    invoice_id = fields.Many2one('account.invoice', string="Factura", readonly=True)
    date = fields.Date(string=u"Fecha de Pago")
    payment_request_id = fields.Many2one('account.payment.request', string="Solicitud de Cobro", readonly=True)
    payment_id = fields.Many2one('account.payment', string="Registro de Pago", readonly=True)
    amount_bs = fields.Float(u'Monto Bs.', digits=(16, 2), readonly=True)
    amount_usd = fields.Float(u'Monto $us', digits=(16, 2), readonly=True)
    currency_id = fields.Many2one('res.currency', string="Moneda", readonly=True)
    state = fields.Char('Estado', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'chasis_payment_history_report')
        self.env.cr.execute("""
        create or replace view chasis_payment_history_report as (
        select row_number() over() as id, * from (
/*SELECT
  t2.lot_id as lot_id,
  t3.id as sale_id,
  0 as invoice_id,
  0 as payment_request_id,
  t1.id as payment_id,
  t1.amount,
  t1.currency_id,
  t1.state
FROM account_move_line t0
  INNER JOIN account_payment t1 ON t1.id = t0.payment_id
  INNER JOIN sale_order_line t2 ON t2.order_id = t1.order_id
  INNER JOIN sale_order t3 ON t3.id = t2.order_id
WHERE
  t2.lot_id is not null
group by
  t2.lot_id,
  t3.id,
  invoice_id,
  payment_request_id,
  t1.id,
  t1.amount,
  t1.currency_id,
  t1.state

UNION ALL

SELECT
  t3.lot_id as chasis_id,
  0 as sale_id,
  t4.id as invoice_id,
  0 as payment_request_id,
  t1.id as payment_id,
  t1.amount,
  t1.currency_id,
  t1.state
FROM account_move_line t0
  INNER JOIN account_payment t1 ON t1.id = t0.payment_id
  INNER JOIN account_invoice_payment_rel t2 ON t2.payment_id = t1.id
  INNER JOIN account_invoice_line t3 ON t3.invoice_id = t2.invoice_id
  INNER JOIN account_invoice t4 on t4.id = t3.invoice_id
WHERE
  t3.lot_id is not null
group by
  t3.lot_id,
  sale_id,
  t4.id,
  payment_request_id,
  t1.id,
  t1.amount,
  t1.currency_id,
  t1.state

UNION ALL*/
SELECT
  t2.lot_id,
  t1.partner_id,
  0 as sale_id,
  0 as invoice_id,
  t1.payment_date as date,
  t2.id as payment_request_id,
  t1.id as payment_id,
  CASE WHEN t1.currency_id = 3 THEN
  t1.amount/(select rate from res_currency_rate where currency_id = 3
order by name desc limit 1)
  ELSE
  t1.amount
  END
  AS amount_bs,

  CASE WHEN t1.currency_id = 62 THEN
  (select rate from res_currency_rate where currency_id = 3
order by name desc limit 1)*t1.amount
  ELSE
  t1.amount
  END
  AS amount_usd,

  t1.currency_id,

  t1.state
FROM account_move_line t0
  INNER JOIN account_payment t1 ON t1.id = t0.payment_id
  INNER JOIN account_payment_request t2 ON t2.id = t1.payment_request_id
WHERE
  t2.lot_id is not null
GROUP BY
  t2.lot_id,
  t1.partner_id,
  sale_id,
  invoice_id,
  t1.payment_date,
  t2.id,
  t1.id,
  t1.amount,
  t1.currency_id,
  t1.state
  ) as foo
order by 2
        )""")
