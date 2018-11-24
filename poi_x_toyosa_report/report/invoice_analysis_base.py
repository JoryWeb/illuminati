from odoo import models, fields, api, _, tools
from datetime import datetime
import time
import odoo.addons.decimal_precision as dp
from odoo.osv import expression

class AccountInvoiceAnalysis(models.Model):
    _inherit = "account.invoice.report"

    segment_id = fields.Many2one('account.segment', 'Segmento')


    def _select(self):
        select_str = super(AccountInvoiceAnalysis, self)._select()
        select_str += """,
                sub.segment_id
        """
        return select_str

    def _sub_select(self):
        select_str = super(AccountInvoiceAnalysis, self)._sub_select()
        select_str += """,
                seg.id as segment_id
        """
        return select_str

    def _from(self):
        from_str = super(AccountInvoiceAnalysis, self)._from()
        from_str += """
                LEFT JOIN account_segment seg on seg.id = pt.segment_id
        """
        return from_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceAnalysis, self)._group_by()
        group_by_str += """,
            seg.id
        """
        return group_by_str

    @api.model_cr
    def init(self):
        super(AccountInvoiceAnalysis, self).init()
