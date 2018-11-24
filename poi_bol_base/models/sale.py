# -*- encoding: utf-8 -*-
from odoo import models, api, fields, registry, _

import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_nr = fields.Char(u'Nr. de contrato', help=u"El número de contrato registrado para fines de Bancarización.")

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        inv_ids = super(SaleOrder, self).action_invoice_create(grouped=grouped, final=final)
        invoice_obj = self.env['account.invoice']
        for inv in invoice_obj.browse(inv_ids):
            inv.write({'nit': self.partner_id.nit or self.partner_id.ci, 'razon': self.partner_id.razon})
        return inv_ids
