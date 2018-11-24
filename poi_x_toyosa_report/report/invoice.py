# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api
from odoo.addons.poi_bol_base.models.amount_to_text_es import to_word, MONEDAS

class ReportAccountInvoice(models.AbstractModel):
    _name = 'report.account.report_invoice_with_payments'

    @api.multi
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('account.report_invoice')
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)[0]
        invoice_id = self.env[report.model].browse(docids)

        report = (invoice_id.sale_type_id and invoice_id.sale_type_id.print_invoice and invoice_id.sale_type_id.print_invoice) or report


        config_id = self.env['sale.report.config'].search([('report_id', '=', report.id)])


        attrib = {}

        if config_id:
            for line in invoice_id.invoice_line_ids:
                if line.lot_id:
                    lot_id = line.lot_id
                    break
            for a in lot_id.product_id.atributo_line:
                attrib.update({a.name.id: a.atributo_ids})


        report_name = (invoice_id.sale_type_id and invoice_id.sale_type_id.print_invoice and invoice_id.sale_type_id.print_invoice.report_name) or 'report.account.report_invoice'

        if invoice_id.type == 'out_refund' and invoice_id.tipo_fac == '6':
            report_name = 'invoice'
        if (invoice_id.sale_type_id and invoice_id.sale_type_id.print_invoice and invoice_id.sale_type_id.print_invoice.report_name):
            report_name = report.report_name
        else:
            report_name = 'poi_x_toyosa_report.invoice_template_mrva'


        return  {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': invoice_id,
            'attrib': attrib,
            'item_ids': config_id.item_ids,
            'to_word': to_word,
            'usd': usd_currency,
            'report': report_name,
        }
