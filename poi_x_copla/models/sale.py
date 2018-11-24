
from odoo import api, fields, models, osv, _

class SaleConditionPayment(models.Model):
    _name = 'sale.condition.payment'

    name = fields.Char(string=u"Nombre")

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_condition = fields.Many2one("sale.condition.payment", u'Cóndicion de pago')

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        inv_ids = super(SaleOrder, self).action_invoice_create(grouped=grouped, final=final)
        if self.sale_condition:
            invoice_obj = self.env['account.invoice']
            for inv in invoice_obj.browse(inv_ids):
                inv.sale_condition = self.sale_condition.id
        return inv_ids
