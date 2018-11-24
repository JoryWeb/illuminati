# © 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2015-2016 AvanzOSC
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, exceptions, models, _

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('state')
    def _get_warehouse(self):
        if self.cc_dos and self.type == 'out_invoice':
            self.warehouse_id = self.cc_dos.warehouse_id.id

    warehouse_id = fields.Many2one('stock.warehouse', 'Almacén', compute="_get_warehouse", store=True)
