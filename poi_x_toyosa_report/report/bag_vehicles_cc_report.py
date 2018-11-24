from odoo import models, fields, api, _, tools
from datetime import date, datetime
import calendar

class BagVehiclesCcReport(models.Model):
    _name = 'bag.vehicles.cc.report'
    _description = 'Reporte de Bolsa de Vehiculos Con Cliente'
    _auto = False

    released = fields.Selection(
        string="Liberado",
        selection=[
            ('sin_warrant', 'Sin Warrant'),
            ('no_liberado', 'Con Warrant'),
            ('en_tramite', 'En Trámite'),
            ('liberado', 'Liberado'),
        ]
    )
    nationalized = fields.Selection(
        string="Nacionalizado",
        selection=[
            ('no_nacionalizado', 'No Nacionalizado'),
            ('en_tramite', 'En Tramite'),
            ('temporal', u'Internación Temporal'),
            ('nacionalizado', 'Nacionalizado'),
        ]

    )
    lot_id = fields.Many2one('stock.production.lot', u'N° de Chasis')
    model_id = fields.Many2one('modelo.toyosa', 'Tipo de Vehiculo (Master)', compute="_compute_sale_data")
    price = fields.Float('Precio del Vehiculo', compute="_compute_sale_data")
    order_line_id = fields.Many2one('sale.order.line', 'Venta')
    case = fields.Selection(
        string="Caso",
        selection=[
                ('especial', 'Especial'),
                ('multa', 'Multa'),
                ('usados', 'Usados'),
                ('entra_sale', 'Entra y Sale'),
        ],
    )
    partner_id = fields.Many2one('res.partner', 'Cliente')
    order_id = fields.Many2one('sale.order', 'Orden de Venta')
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen')
    agency_id = fields.Many2one('res.agency', 'Regional')
    seller_id = fields.Many2one('res.users', 'Vendedor')
    person_root_type = fields.Char('Tipo de Cliente')
    sale_type_id = fields.Many2one('sale.type', 'Tipo de Venta', readonly=True)

    amount_pay_before_month = fields.Float('Pagos realizados Anteriores', compute="_compute_sale_data")
    residual_before = fields.Float('Saldo Anterior', compute="_compute_sale_data")
    amount_pay_month = fields.Float('Pagos del Mes Actual', compute="_compute_sale_data")
    amount_total_pay = fields.Float('Saldo por Cobrar', compute="_compute_sale_data")




    @api.multi
    def _compute_sale_data(self):
        if self.env.context.get('date_cut', False):
            date_cut = self.env.context.get('date_cut', False)
        currency_id = self.env['res.currency'].browse(self.env.context.get('currency_id'))
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
        first_day = str(today.year)+'-'+str(month)+'-01'
        last_day = str(today.year)+'-'+str(month)+'-'+str(caledar_today[1])
        first_day_before = str(before_year)+'-'+str(before_month)+'-01'
        last_day_before = str(before_year)+'-'+str(before_month)+'-'+str(caledar_before_month[1])
        first_day = datetime.strptime(first_day, "%Y-%m-%d").date()
        last_day = datetime.strptime(last_day, "%Y-%m-%d").date()
        first_day_before = datetime.strptime(first_day_before, "%Y-%m-%d").date()
        last_day_before = datetime.strptime(last_day_before, "%Y-%m-%d").date()
        total = 0
        for s in self:
            inv_state = False
            inv_total = False
            inv_ids = s.order_id.invoice_ids.filtered(lambda r: r.state in ('open', 'paid') and r.type == 'out_invoice' and r.estado_fac == 'V')
            if inv_ids:
                inv_id = inv_ids[0]
                s.price = inv_id.currency_id.compute(inv_id.amount_total, currency_id)
                inv_state = inv_id.state
                inv_total = inv_id.amount_total
            else:
                s.price = s.order_id.currency_id.compute(s.order_id.amount_total_plus_a, currency_id)
            s.model_id = s.order_id.lot_id.modelo
            total_pay = 0
            for p in s.order_id.payment_advanced_ids:
                total_pay += p.currency_id.compute(p.amount, currency_id)
            if inv_state == 'paid':
                s.amount_total_pay = 0.00
            else:
                s.amount_total_pay = s.price - total_pay
            s.amount_pay_before_month = 0
            for p in s.order_id.payment_advanced_ids.filtered(lambda r: datetime.strptime(r.payment_date, "%Y-%m-%d").date() <= last_day_before):
                s.amount_pay_before_month += p.currency_id.compute(p.amount, currency_id)
            s.residual_before = s.price - s.amount_pay_before_month
            s.amount_pay_month = 0
            for p in s.order_id.payment_advanced_ids.filtered(lambda r: datetime.strptime(r.payment_date, "%Y-%m-%d").date() >= first_day and datetime.strptime(r.payment_date, "%Y-%m-%d").date() <= last_day):
                s.amount_pay_month += p.currency_id.compute(p.amount, currency_id)
            # invoice_id = self.env['account.invoice'].sudo().search([('order_id', '=', s.order_id.id), ('state', 'in', ['open', 'paid']), ('type', '=', 'out_invoice'),], limit=1)
            # if invoice_id:
            #     invoice_id = invoice_id[0]
            #     s.amount_total_pay = invoice_id.currency_id.compute(invoice_id.residual, currency_id)
            #     for p in invoice_id.payment_ids.filtered(lambda r: datetime.strptime(r.payment_date, "%Y-%m-%d").date() >= first_day and datetime.strptime(r.payment_date, "%Y-%m-%d").date() <= last_day):
            #         total = p.currency_id.compute(p.amount, currency_id) + total
            #     s.amount_pay_month = total
            #     for p in invoice_id.payment_ids.filtered(lambda r: datetime.strptime(r.payment_date, "%Y-%m-%d").date() >= first_day_before and datetime.strptime(r.payment_date, "%Y-%m-%d").date() <= last_day_before):
            #         total = p.currency_id.compute(p.amount, currency_id) + total
            #     s.amount_pay_before_month = total
            # else:
            #     s.amount_total_pay = s.order_id.currency_id.compute(s.order_id.amount_total, currency_id)
            #     s.amount_pay_month = 0
            #     s.amount_pay_before_month = 0

            # revisar por que no existe currency_id
            # s.residual_before = invoice_id.amount_total - s.amount_pay_before_month



    @api.multi
    def _compute_price(self):
        pricelist_id = self.env.context.get('pricelist_id', False)
        for s in self:
            product_id = s.product_id
            product_id = product_id.with_context(
                year_id=(s.year_id and s.year_id.id) or False,
                quantity=1,
                pricelist=pricelist_id,
                uom=1,
                date=fields.Date.today(),
            )
            if product_id.price:
                s.price = product_id.price
            else:
                s.price = 0.00

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(BagVehiclesCcReport, self).read_group(domain=domain, fields=fields, groupby=groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        for r in res:
            group_ids = self.search(r['__domain'])
            amount_pay_before_month = 0
            residual_before = 0
            amount_pay_month = 0
            amount_total_pay = 0
            for g in group_ids:
                amount_pay_before_month += g.amount_pay_before_month
                residual_before += g.residual_before
                amount_pay_month += g.amount_pay_month
                amount_total_pay += g.amount_total_pay
            r.update({
                'amount_pay_before_month': amount_pay_before_month,
                'residual_before': residual_before,
                'amount_pay_month': amount_pay_month,
                'amount_total_pay': amount_total_pay,
            })
        return res

    @api.model
    def _update_report(self):
        self.env.cr.execute("REFRESH MATERIALIZED VIEW bag_vehicles_cc_report");


    def _select(self):
        select_str ="""
            select
            	s.state_importaciones as nationalized,
                s.state_finanzas as released,
                s.id as lot_id,
                s.product_id,
                s.anio_modelo as year_id,
                s.colorexterno,
                s.sale_line_id as order_line_id,
                s.caso as case,
                so.id as order_id,
                so.warehouse_id,
                sw.agency_id,
                so.partner_id,
                so.user_id as seller_id,
                so.sale_type_id,
                rp.person_root_type

                /*type*/
            from
            	stock_production_lot s
                left join sale_order_line sol on sol.id = s.sale_line_id
                left join sale_order so on so.id = sol.order_id
                left join stock_warehouse sw on sw.id = so.warehouse_id
                left join res_partner rp on rp.id = so.partner_id

            where
		        sale_line_id is not null and so.state in ('sale', 'done')
        """
        return select_str

    @api.model_cr
    def init(self):
        table = "bag_vehicles_cc_report"
        self.env.cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = 'bag_vehicles_cc_report';
            """)
        vista = self.env.cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                self.env.cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS bag_vehicles_cc_report;
            CREATE MATERIALIZED VIEW bag_vehicles_cc_report as (
            SELECT row_number() over() as id, *
                FROM(%s) as asd
            )""" % (self._select()))
