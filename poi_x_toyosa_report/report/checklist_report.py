#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api
from odoo.addons.poi_bol_base.models.amount_to_text_es import to_word, MONEDAS
from odoo.exceptions import Warning, ValidationError

class ReportAccountInvoice(models.AbstractModel):
    _name = 'report.poi_x_toyosa_report.checklist_report_template'

    @api.multi
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        order_obj = self.env['sale.order']
        tipo = "--"
        report = report_obj._get_report_from_name('poi_x_toyosa_report.checklist_report_template')
        picking_id = self.env[report.model].browse(docids)
        lot_id = False
        order_id = order_obj.search([('procurement_group_id', '=', picking_id.group_id.id)]) if picking_id.group_id else []
        if order_id:
            order_id = order_id[0]
            for l in order_id.order_line:
                if l.lot_id:
                    lot_id = l.lot_id
                    break

        if not lot_id:
            raise Warning("No se puede Imprimir la nota de entrega por que la venta realizada no contiene Chasis/Serie.")
        checklist = lot_id.product_id.checklist_line
        for a in lot_id.product_id.atributo_line:
            if a.name == 'TIPO':
                tipo = a.atributo_ids

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': picking_id,
            'order_id': order_id,
            'lot_id': lot_id,
            'checklist': checklist,
            'tipo': tipo,
        }
