from odoo import models, fields, api
from datetime import date, datetime

class SaleMoveReport(models.Model):
    _name = 'sale.move.report'
    _description = 'Reporte Moviento de Ventas'
    _auto = False
    _order = "payment_date asc"

    payment_date = fields.Date('Fecha')
    partner_id = fields.Many2one('res.partner', 'Cliente')
    lot_id = fields.Many2one('stock.production.lot', 'N° de Chasis', compute="_compute_pays")
    model_id = fields.Many2one('modelo.toyosa', 'Modelo', compute="_compute_pays")
    payment_id = fields.Many2one('account.payment', 'Pago')
    amount_pay = fields.Float('A Cuenta de la Fecha', compute="_compute_pays")
    amount_pay_before = fields.Float('Acuenta Dias Anteriores', compute="_compute_pays")
    amount_total = fields.Float('Saldo a Cancelar a La Fecha', compute="_compute_pays")
    amount_total_before = fields.Float('Saldo a Cancelar dias Anteriores', compute="_compute_pays")

    journal_id = fields.Many2one('account.journal', 'Diario')
    # state = fields.Char('Entregado', compute="_compute_pays")
    warrant = fields.Char('Warrant', compute="_compute_pays")
    seller_id = fields.Many2one('res.users', 'Vendedor')
    partner_type = fields.Char('Tipo de Cliente', compute="_compute_pays")
    sale_type_id = fields.Many2one('sale.type', 'Tipo de Venta')
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen')
    agency_id = fields.Many2one('res.agency', 'Regional')
    order_id = fields.Many2one('sale.order', 'Orden de Venta')
    person_root_type = fields.Char('Tipo de Cliente')

    @api.multi
    def _compute_pays(self):
        date_cut = self.env.context.get('date_cut', False)
        for s in self:
            if s.order_id:
                s.lot_id = s.order_id.lot_id.id
                s.model_id = s.lot_id.modelo.id
                # s.state = s.lot_id.state
                s.warrant = s.lot_id.state_finanzas
                # if s.lot_id.state == 'done':
                #     s.state = 'Entregado'
                # if s.lot_id.state_finanzas == 'no_liberado':
                #     s.warrant = 'Warrant'
            if s.partner_id:
                if s.partner_id.partner_type == 'contact':
                    s.partner_type = 'Natural'
                else:
                    s.partner_type = 'Empresa'
            if date_cut:
                today = datetime.strptime(date_cut, "%Y-%m-%d").date()
            else:
                today = datetime.now().date()
            if s.payment_id and datetime.strptime(s.payment_id.payment_date, "%Y-%m-%d").date() == today:
                s.amount_pay = s.payment_id.currency_id.compute(s.payment_id.amount, s.payment_id.company_id.currency_id)
                s.amount_pay_before = 0
            elif s.payment_id and datetime.strptime(s.payment_id.payment_date, "%Y-%m-%d").date() < today:
                s.amount_pay_before = s.payment_id.currency_id.compute(s.payment_id.amount, s.payment_id.company_id.currency_id)
                s.amount_pay= 0
            else:
                s.amount_pay = 0
                s.amount_pay_before = 0
            if not s.payment_id and   datetime.strptime(s.order_id.order_date, "%Y-%m-%d").date() == today:
                s.amount_total = s.order_id.currency_id.compute(s.order_id.amount_total, s.order_id.company_id.currency_id)
                s.amount_total_before = 0
            elif not s.payment_id and datetime.strptime(s.order_id.order_date, "%Y-%m-%d").date() < today:
                s.amount_total_before = s.order_id.currency_id.compute(s.order_id.amount_total, s.order_id.company_id.currency_id)
                s.amount_total= 0
            else:
                s.amount_total = 0
                s.amount_total_before = 0


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(SaleMoveReport, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        for r in res:
            group_ids = self.search(r['__domain'])
            amount_pay = 0
            amount_pay_before = 0
            amount_total = 0
            amount_total_before = 0
            for g in group_ids:
                amount_pay = amount_pay + g.amount_pay
                amount_pay_before = amount_pay_before + g.amount_pay_before
                amount_total = amount_total + g.amount_total
                amount_total_before = amount_total_before + g.amount_total_before

            r.update({
                'amount_pay': amount_pay,
                'amount_pay_before': amount_pay_before,
                'amount_total': amount_total,
                'amount_total_before': amount_total_before,
            })
        return res

    @api.model
    def _update_report(self):
        self.env.cr.execute("REFRESH MATERIALIZED VIEW sale_move_report");


    def _select(self):
        select_str ="""
            select
            	ap.payment_date,
            	ap.partner_id,
            	ap.id as payment_id,
            	ap.journal_id,
            	so.user_id as seller_id,
            	so.sale_type_id,
                so.warehouse_id,
                sw.agency_id,
                so.id as order_id,
                rp.person_root_type


            from
            	account_payment ap
             	left join account_payment_request apr on ap.payment_request_id = apr.id
             	left join stock_production_lot spl on spl.id = apr.lot_id
             	left join sale_order so on so.id = ap.order_id
             	left join res_partner rp on rp.id = ap.partner_id
             	left join stock_warehouse sw on sw.id  = so.warehouse_id
            where
            	ap.order_id is not null and so.lot_id is not  null
            union all
            select
            	so.order_date as payment_date,
            	so.partner_id,
            	ap.id as payment_id,
            	ap.journal_id,
            	so.user_id as seller_id,
            	so.sale_type_id,
                so.warehouse_id,
                sw.agency_id,
                so.id as order_id,
                rp.person_root_type

            from
            	sale_order so
            	left join account_payment ap on ap.order_id = so.id
             	left join res_partner rp on rp.id = ap.partner_id
             	left join stock_warehouse sw on sw.id  = so.warehouse_id
            where
		        ap.id is null and so.state in ('sale', 'done') and so.lot_id is not null

        """
        return select_str

    @api.model_cr
    def init(self):
        table = "sale_move_report"
        self.env.cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = 'sale_move_report';
            """)
        vista = self.env.cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                self.env.cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS sale_move_report;
            CREATE MATERIALIZED VIEW sale_move_report as (
            SELECT row_number() over() as id, *
                FROM(%s) as asd
            )""" % (self._select()))
