# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    property_stock_account_outinvoice = fields.Many2one(
        'account.account', 'Cuenta de salida de facturas',
        company_dependent=True, domain=[('deprecated', '=', False)],
        help="Aplicable a productos con contabilidad anglosajona "
             "Esta es una cuenta puente que permitirá registrar el costo de venta ya en la Factura de cliente. Complementariamente, esta cuenta puente quedará neteada al hacer la Salida de inventario.")

    @api.multi
    def _get_product_accounts(self):
        """ Add the stock accounts related to product to the result of super()
        @return: dictionary which contains information regarding stock accounts and super (income+expense accounts)
        """
        accounts = super(ProductTemplate, self)._get_product_accounts()
        accounts.update({
            'stock_outinvoice': self.property_stock_account_outinvoice or self.categ_id.property_stock_account_outinvoice or False,
        })
        return accounts


class ProductCategory(models.Model):
    _inherit = 'product.category'
    property_stock_account_outinvoice = fields.Many2one(
        'account.account', 'Cuenta de salida de facturas',
        company_dependent=True, domain=[('deprecated', '=', False)],
        help="Aplicable a productos con contabilidad anglosajona "
             "Esta es una cuenta puente que permitirá registrar el costo de venta ya en la Factura de cliente. Complementariamente, esta cuenta puente quedará neteada al hacer la Salida de inventario.")

