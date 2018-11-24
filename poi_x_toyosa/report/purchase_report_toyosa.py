from odoo import tools
from odoo import api, fields, models


class PurchaseReportToyosa(models.Model):
    _name = "purchase.report.toyosa"
    _description = "Ordenes de Compra Toyosa"
    _auto = False
    date = fields.Datetime('Fecha Pedido', readonly=True, help="Date on which this document has been created")
    state = fields.Selection([('draft', 'Draft RFQ'),
                               ('sent', 'RFQ Sent'),
                               ('to approve', 'To Approve'),
                               ('purchase', 'Purchase Order'),
                               ('done', 'Done'),
                               ('cancel', 'Cancelled')
                              ],'Estado', readonly=True)
    product_id =fields.Many2one('product.product', 'Producto', readonly=True)
    price_unit = fields.Float('Precio Unitario', readonly=True)
    order_id =fields.Many2one('purchase.order', 'Orden de Compra', readonly=True)
    picking_type_id = fields.Many2one('stock.warehouse', 'Almacén', readonly=True)
    partner_id =fields.Many2one('res.partner', 'Proveedor', readonly=True)
    date_approve =fields.Date('Fecha de Aprobación', readonly=True)
    product_uom = fields.Many2one('product.uom', 'Unidad de Medida', required=True)
    company_id =fields.Many2one('res.company', 'Compañia', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True)
    user_id =fields.Many2one('res.users', 'Responsable', readonly=True)
    delay =fields.Float('Dias de Valides', digits=(16,2), readonly=True)
    delay_pass =fields.Float('Dias para entregar', digits=(16,2), readonly=True)
    quantity = fields.Float('Cantidad', readonly=True)  # TDE FIXME master: rename into unit_quantity
    price_total = fields.Float('Precio Total', readonly=True)
    price_average = fields.Float('Precio promedio', readonly=True, group_operator="avg")
    negociation = fields.Float('Precio Compra Estandar', readonly=True, group_operator="avg")
    price_standard = fields.Float('Valor Producto', readonly=True, group_operator="sum")
    nbr = fields.Integer('# de Linea', readonly=True)  # TDE FIXME master: rename into nbr_lines
    category_id = fields.Many2one('product.category', 'Categoria de Producto', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Plantilla Producto', readonly=True)
    country_id = fields.Many2one('res.country', 'Ciudad Proveedor', readonly=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Posición Fiscal', oldname='fiscal_position', readonly=True)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Cuenta Analítica', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Responsable Comercial', readonly=True)

    _order = 'date desc, price_total desc'

    @api.model_cr
    def init(self):
        tools.sql.drop_view_if_exists(self.env.cr, 'purchase_report_toyosa')
        self.env.cr.execute("""
            create or replace view purchase_report_toyosa as (
                WITH currency_rate as (%s)
                select
                    min(l.id) as id,
                    s.date_order as date,
                    s.state,
                    s.date_approve,
                    s.dest_address_id,
                    spt.warehouse_id as picking_type_id,
                    s.partner_id as partner_id,
                    s.create_uid as user_id,
                    s.company_id as company_id,
                    s.fiscal_position_id as fiscal_position_id,
                    l.product_id,
                    l.price_unit,
                    l.order_id,
                    p.product_tmpl_id,
                    t.categ_id as category_id,
                    s.currency_id,
                    t.uom_id as product_uom,
                    sum(l.product_qty/u.factor*u2.factor) as quantity,
                    extract(epoch from age(s.date_approve,s.date_order))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from age(l.date_planned,s.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
                    count(*) as nbr,
                    sum(l.price_unit / COALESCE(cr.rate, 1.0) * l.product_qty)::decimal(16,2) as price_total,
                    avg(100.0 * (l.price_unit / COALESCE(cr.rate,1.0) * l.product_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2) as negociation,
                    sum(ip.value_float*l.product_qty/u.factor*u2.factor)::decimal(16,2) as price_standard,
                    (sum(l.product_qty * l.price_unit / COALESCE(cr.rate, 1.0))/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    analytic_account.id as account_analytic_id
                from purchase_order_line l
                    join purchase_order s on (l.order_id=s.id)
                    join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                            LEFT JOIN ir_property ip ON (ip.name='standard_price' AND ip.res_id=CONCAT('product.template,',t.id) AND ip.company_id=s.company_id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join stock_picking_type spt on (spt.id=s.picking_type_id)
                    left join account_analytic_account analytic_account on (l.account_analytic_id = analytic_account.id)
                    left join currency_rate cr on (cr.currency_id = s.currency_id and
                        cr.company_id = s.company_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
                group by
                    s.company_id,
                    s.create_uid,
                    s.partner_id,
                    u.factor,
                    s.currency_id,
                    l.price_unit,
                    l.order_id,
                    s.date_approve,
                    l.date_planned,
                    l.product_uom,
                    s.dest_address_id,
                    s.fiscal_position_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id,
                    s.date_order,
                    s.state,
                    spt.warehouse_id,
                    u.uom_type,
                    u.category_id,
                    t.uom_id,
                    u.id,
                    u2.factor,
                    partner.country_id,
                    partner.commercial_partner_id,
                    analytic_account.id
            )
        """ % self.env['res.currency']._select_companies_rates())
