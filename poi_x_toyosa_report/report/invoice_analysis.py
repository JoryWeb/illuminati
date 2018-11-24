from odoo import models, fields, api, _, tools
from datetime import datetime
import time
import odoo.addons.decimal_precision as dp
from odoo.osv import expression

class AccountInvoiceAnalysis(models.Model):
    _name = 'account.invoice.analysis'
    _description = 'Reporte de Analisis de Factura'
    _auto = False

    invoice_id = fields.Many2one('account.invoice', 'Factura')
    user_id = fields.Many2one('res.users', 'Vendedor')
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen')
    date_invoice = fields.Date('Mes de Facturacion')
    product_id = fields.Many2one('product.product', 'Producto')
    lot_id = fields.Many2one('stock.production.lot', 'Serie')
    state = fields.Char('Estado')
    quantity = fields.Float('Cantidad')
    price_unit = fields.Float('Precio Unitario')
    price_subtotal = fields.Float('Subtotal')
    price_subtotal_with_tax = fields.Float('Total con Impuesto')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):

        self.env.cr.execute("REFRESH MATERIALIZED VIEW account_invoice_analysis");

        res = super(AccountInvoiceAnalysis, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        return res


    def _select(self):

        select_str ="""
            select
            	ai.id as invoice_id,
            	ai.user_id,
            	ai.warehouse_id,
            	ai.date_invoice,
            	ail.product_id,
            	ail.lot_id,
            	ai.state,
            	ail.quantity,
            	ail.price_unit,
            	ail.price_subtotal,
            	ail.price_subtotal_with_tax
            from
            	account_invoice ai
            	left join account_invoice_line ail on ail.invoice_id = ai.id
            where
            	ai.type = 'out_invoice'
        """
        return select_str

    @api.model_cr
    def init(self):
        table = "account_invoice_analysis"
        self.env.cr.execute("""
            SELECT table_type
            FROM information_schema.tables
            WHERE table_name = 'account_invoice_analysis';
            """)
        vista = self.env.cr.fetchall()
        for v in vista:
            if v[0] == 'VIEW':
                self.env.cr.execute("""
                    DROP VIEW IF EXISTS %s;
                    """ % table);
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS account_invoice_analysis;
            CREATE MATERIALIZED VIEW account_invoice_analysis as (
            SELECT row_number() over() as id, *
                FROM(%s) as asd
            )""" % (self._select()))
