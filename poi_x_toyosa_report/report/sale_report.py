from odoo import models, fields, api
# TODO: Informe de Ventas Nativo Agregado de Campos Segmento

class SaleReport(models.Model):
    _inherit = 'sale.report'

    segment_id = fields.Many2one('account.segment', 'Segmento')

    def _select(self):
        select_str = super(SaleReport, self)._select()
        select_str += """,
            seg.id as segment_id"""
        return select_str

    def _from(self):
        from_str = super(SaleReport, self)._from()
        from_str += """
            left join account_segment seg on seg.id = t.segment_id
        """
        return from_str

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        group_by_str += """,
            seg.id
        """
        return group_by_str

    @api.model_cr
    def init(self):
        super(SaleReport, self).init()
