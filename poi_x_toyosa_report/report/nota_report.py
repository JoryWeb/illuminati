#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api
from odoo.addons.poi_bol_base.models.amount_to_text_es import to_word, MONEDAS
from odoo.exceptions import Warning, ValidationError

class NotaeReport(models.AbstractModel):
    _name = 'report.poi_x_toyosa_report.notae_report_template'

    @api.multi
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        order_obj = self.env['sale.order']
        tipo = "--"
        report = report_obj._get_report_from_name('poi_x_toyosa_report.notae_report_template')
        picking_id = self.env[report.model].browse(docids)
        lot_id = False
        order_id = order_obj.search([('procurement_group_id', '=', picking_id.group_id.id)]) if picking_id.group_id else []
        invoice_id = self.env['account.invoice']
        if order_id:
            order_id = order_id[0]
            for l in order_id.order_line:
                if l.lot_id:
                    lot_id = l.lot_id
                    break

        if order_id.invoice_ids:
            for i in order_id.invoice_ids:
                if i.estado_fac == 'V':
                    invoice_id = i
                    break
        # for a in lot_id.product_id.atributo_line:
        #     if a.name == 'TIPO':
        #         tipo = a.atributo_ids and a.atributo_ids[0].name

        if not lot_id:
            raise Warning("No se puede Imprimir la nota de entrega por que la venta realizada no contiene Chasis/Serie.")
        checklist = lot_id.product_id.checklist_line
        # FIXME: campo warranty no existe en el dato maestr producto
        insurance = False
        # insurance = lot_id.product_id.warranty
        if insurance > 0:
            insurance = int(insurance / 12)
        elif insurance == 0 or insurance <= 0 or insurance == False:
            insurance = False
        km = lot_id.product_id.garantia_km
        if km == 0 or km == False or km == '' or km <0:
            km = False
        if insurance == False or km == False:
            insurance = False
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': picking_id,
            'order_id': order_id,
            'lot_id': lot_id,
            'checklist': checklist,
            'invoice_id': invoice_id,
            'insurance': insurance,
        }
