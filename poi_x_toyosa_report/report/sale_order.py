#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api, _, tools
from odoo.osv import osv
from odoo.addons.poi_bol_base.models.amount_to_text_es import to_word, MONEDAS
from odoo.exceptions import Warning, ValidationError

class ReportSaleOrder(models.AbstractModel):
    _name = 'report.sale.report_saleorder'

    @api.multi
    def get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('sale.report_saleorder')
        order_id = self.env[report.model].browse(docids)
        if order_id.sale_type_id.discount_flag and  not order_id.discount_flag:
            raise Warning('No se Imprimir la cotizacion aun no se ha validado el Descuento.')

        report = (order_id.sale_type_id and order_id.sale_type_id.print_order and order_id.sale_type_id.print_order) or report

        config_id = self.env['sale.report.config'].search([('report_id', '=', report.id)])


        attrib = {}

        if config_id:
            for a in order_id.lot_id.product_id.atributo_line:
                attrib.update({a.name.id: a.atributo_ids})

        #total_accessory = 0
        # for l in order_id.order_line:
        #     if l.product_id.accessory:
        #         total_accessory = total_accessory + l.price_total

        if order_id.lot_id and order_id.lot_id.product_id.categ_id and order_id.lot_id.product_id.categ_id.name:
            serie = order_id.lot_id.product_id.categ_id.name
        else:
            serie = ''

        report_name = (order_id.sale_type_id and order_id.sale_type_id.print_order and order_id.sale_type_id.print_order.report_name) or 'report.sale.report_saleorder'

        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'proforma': True,
            'docs': order_id,
            'attrib': attrib,
            'item_ids': config_id.item_ids,
            'to_word': to_word,
            'today': fields.Datetime.now(),
            #'total_accessory': total_accessory,
            'serie': serie,
            'report': report_name,
        }
