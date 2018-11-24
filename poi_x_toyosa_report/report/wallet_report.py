from openerp import models, fields, api, _, tools
from datetime import datetime
import time
import openerp.addons.decimal_precision as dp
from openerp.osv import expression
from datetime import date, datetime
import calendar


class WalletReport(models.Model):
    _name = 'wallet.report'
    _description = 'Reporte de Cartera'
    _auto = False

    invoice_id = fields.Many2one('account.invoice', 'Factura')
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen')
    agency_id = fields.Many2one('res.agency', 'Regional')
    number = fields.Char('Factura')
    cc_nro = fields.Char('Nro. SIN')
    partner_id = fields.Many2one('res.partner', 'Cliente')
    order_id = fields.Many2one('sale.order', 'Orden de Venta')
    order_type_id = fields.Many2one('sale.order.type', 'Tipo de OV')
    date_invoice = fields.Date('Fecha de Facturacion')
    amount_total = fields.Float('Monto Total')
    residual_before = fields.Float('Saldo Anterior al Mes', compute="_compute_days")
    residual = fields.Float('Saldo Actual', compute="_compute_days")
    amount_pay = fields.Float('Total Pagado', compute='_compute_days')
    #amount_pay = fields.Float('Total Pagado', compute='_compute_amount_pay')
    last_date_pay = fields.Date(
        string="Ultima Fecha de Pago",
        compute='_compute_last_date_pay',
    )
    days = fields.Float('Dias de Antiguedad', compute='_compute_days')
    days30 = fields.Float('Vigente', compute='_compute_days')
    days90 = fields.Float('90 dias Morosidad', compute='_compute_days')
    days180 = fields.Float('180 dias Morosidad', compute='_compute_days')
    days270 = fields.Float('270 dias Morosidad', compute='_compute_days')
    days360 = fields.Float('360 dias Morosidad', compute='_compute_days')
    days720 = fields.Float('720 dias Morosidad', compute='_compute_days')
    days1080 = fields.Float('1080 dias Morosidad', compute='_compute_days')
    days1080more = fields.Float('+1080 dias Morosidad', compute='_compute_days')
    amount_total_m = fields.Float('Total Morosidad', compute="_compute_days")

    days90p = fields.Float('90 dias Prevision 0%', compute='_compute_days')
    days180p = fields.Float('180 dias Prevision 30%', compute='_compute_days')
    days270p = fields.Float('270 dias Prevision 45%', compute='_compute_days')
    days360p = fields.Float('360 dias Prevision 60%', compute='_compute_days')
    days720p = fields.Float('720 dias Prevision 75%', compute='_compute_days')
    days1080p = fields.Float('1080 dias Prevision 90%', compute='_compute_days')
    days1080morep = fields.Float('+1080 dias Prevision 100%', compute='_compute_days')
    amount_total_p = fields.Float('Total Prevision', compute="_compute_days")


    @api.multi
    def _compute_days(self):
        date_cut = self.env.context.get('date_cut', False)
        today = datetime.strptime(date_cut, "%Y-%m-%d").date()
        caledar_today = calendar.monthrange(today.year, today.month)
        if today.month == 1:
            before_month = 12
            before_year = today.year - 1
        else:
            before_month = today.month - 1
            before_year = today.year
        if today.month > 9:
            month = str(today.month)

        else:
            month = '0'+str(today.month)
        caledar_before_month = calendar.monthrange(before_year, before_month)
        last_day_before = str(before_year)+'-'+str(before_month)+'-'+str(caledar_before_month[1])
        last_day_before = datetime.strptime(last_day_before, "%Y-%m-%d").date()
        for s in self:
            amount_pay_before_month = 0
            date_invoice = datetime.strptime(s.date_invoice, "%Y-%m-%d").date()
            if date_cut:
                today = datetime.strptime(date_cut, "%Y-%m-%d").date()
            else:
                today = datetime.now().date()
            delta = today - date_invoice
            s.days =  delta.days
            total = 0
            for p in s.invoice_id.payment_ids.filtered(lambda r: datetime.strptime(r.payment_date, "%Y-%m-%d").date() <= today and r.state == 'posted'):
                total = p.currency_id.compute(p.amount, s.invoice_id.company_id.currency_id) + total

            for p in s.order_id.payment_advanced_ids.filtered(lambda r: datetime.strptime(r.payment_date, "%Y-%m-%d").date() <= last_day_before):
                amount_pay_before_month += p.currency_id.compute(p.amount, s.order_id.company_id.currency_id)
            s.residual_before = s.amount_total - amount_pay_before_month
            s.amount_pay = total
            s.residual = s.amount_total - s. amount_pay
            total = s.residual
            s.days30 = 0
            s.days90 = 0
            s.days180 = 0
            s.days270 = 0
            s.days360 = 0
            s.days720 = 0
            s.days1080 = 0
            s.days1080more = 0
            s.amount_total_m = total
            s.days90p = 0
            s.days180p = 0
            s.days270p = 0
            s.days360p = 0
            s.days720p = 0
            s.days1080p = 0
            s.days1080morep = 0
            s.amount_total_p = 0

            if delta.days <= 30:
                s.days30 = total
            elif delta.days <= 90:
                s.days90 = total
                s.days30p = total * 0.00
                s.amount_total_p = total * 0.00
            elif delta.days <= 180:
                s.days180 = total
                s.days180p = total * 0.30
                s.amount_total_p = total * 0.30
            elif delta.days <= 270:
                s.days270 = total
                s.days270p = total * 0.45
                s.amount_total_p = total * 0.45
            elif delta.days <= 360:
                s.days360 = total
                s.days360p = total * 0.60
                s.amount_total_p = total * 0.60
            elif delta.days <= 720:
                s.days720 = total
                s.days720p = total * 0.75
                s.amount_total_p = total * 0.75
            elif delta.days <= 1080:
                s.days1080 = total
                s.days30p = total * 0.90
                s.amount_total_p = total * 0.90
            elif delta.days > 1080:
                s.days1080more = total
                s.days30p = total * 1
                s.amount_total_p = total * 1
            # pay_ids = s.invoice_id.payment_ids.sorted(key=lambda r: r.payment_date, reverse=True)
            # for p in pay_ids:
            #     s.last_date_pay = p.payment_date
            #     break


    @api.multi
    def _compute_last_date_pay(self):
        for s in self:
            pay_ids = s.invoice_id.payment_ids.sorted(key=lambda r: r.payment_date, reverse=True)
            for p in pay_ids:
                s.last_date_pay = p.payment_date
                break

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(WalletReport, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        for r in res:
            group_ids = self.search(r['__domain'])
            days30 = 0
            days90 = 0
            days180 = 0
            days270 = 0
            days360 = 0
            days720 = 0
            days1080 = 0
            days1080more = 0
            amount_total_m = 0
            days90p = 0
            days180p = 0
            days270p = 0
            days360p = 0
            days720p = 0
            days1080p = 0
            days1080morep = 0
            amount_total_p = 0
            residual_before = 0
            for g in group_ids:
                days30 = days30 + g.days30
                days90 = days90 + g.days90
                days180 = days180 + g.days180
                days270 = days270 + g.days270
                days360 = days360 + g.days360
                days720 = days720 + g.days720
                days1080 = days1080 + g.days1080
                days1080more = days1080more + g.days1080more
                amount_total_m = amount_total_m + g.amount_total_m
                days90p = days90p + g.days90p
                days180p = days180p + g.days180p
                days270p = days270p + g.days270p
                days360p = days360p + g.days360p
                days720p = days720p + g.days720p
                days1080p = days1080p + g.days1080p
                days1080morep = days1080morep + g.days1080morep
                amount_total_p = amount_total_p + g.amount_total_p
                residual_before = residual_before + g.residual_before
            r.update({
                'days30': days30,
                'days90': days90,
                'days180': days180,
                'days270': days270,
                'days360': days360,
                'days720': days720,
                'days1080': days1080,
                'days1080more': days1080more,
                'amount_total_m': amount_total_m,
                'days90p': days90p,
                'days180p': days180p,
                'days270p': days270p,
                'days360p': days360p,
                'days720p': days720p,
                'days1080p': days1080p,
                'days1080morep': days1080morep,
                'amount_total_p': amount_total_p,
                'residual_before': residual_before,
            })
        return res

    @api.model
    def _update_report(self):
        self.env.cr.execute("REFRESH MATERIALIZED VIEW wallet_report");

    def _select(self):
        select_str ="""
            select
            	ai.id as invoice_id,
            	ai.warehouse_id,
                w.agency_id,
            	ai.number,
            	ai.cc_nro,
            	ai.partner_id,
            	ai.order_id,
                ai.date_invoice,
                ai.amount_total,
            	s.order_type_id
            from
            	account_invoice ai
            	left join sale_order s on s.id = ai.order_id
                left join stock_warehouse w on w.id = ai.warehouse_id
            where
            	ai.type = 'out_invoice'

        """
        return select_str

    @api.model_cr
    def init(self):
        table = "wallet_report"
        self.env.cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = 'wallet_report';
            """)
        vista = self.env.cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                self.env.cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS wallet_report;
            CREATE MATERIALIZED VIEW wallet_report as (
            SELECT row_number() over() as id, *
                FROM(%s) as asd
            )""" % (self._select()))
