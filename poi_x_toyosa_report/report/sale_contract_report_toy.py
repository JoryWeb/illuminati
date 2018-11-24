#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api, _, tools
from odoo.addons.poi_bol_base.models.amount_to_text_es import to_word, MONEDAS
from odoo.exceptions import Warning, ValidationError
from datetime import datetime

class report_rciva_payroll(models.AbstractModel):
    _name = 'report.poi_x_toyosa_report.sale_contract_template_toy'

    @api.multi
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        order_obj = self.env['sale.order']
        payment_obj = self.env['account.payment']
        report = report_obj._get_report_from_name('poi_x_toyosa_report.sale_contract_template_toy')
        lot_id = False
        order_id = self.env[report.model].browse(docids)
        if not order_id.lot_id:
            raise Warning('La cotizacion debe contener un chasis seleccionado en caso contrario no se podra imprimir el contrato.')
        else:
            lot_id = order_id.lot_id

        if not lot_id.product_id:
            raise Warning('El chasis seleccionado no se encuentra correctamente configurado falta especificar el campo Producto/Master.')


        moneda = next(filter(lambda x: x['currency'] == order_id.pricelist_id.currency_id.name, MONEDAS))
        moneda = moneda['plural']
        valor_i = ""
        name_i = ''
        config_id = self.env['sale.report.config'].search([('report_id', '=', report.id)])
        if config_id:
            name_i = config_id[0].item_ids[0].name
            id_i = config_id[0].item_ids[0] and config_id[0].item_ids[0].item_id.id
            atrib = self.env['atributo.toyosa'].search([('name', '=', id_i), ('product_id', '=', lot_id.product_id.product_tmpl_id.id)], limit=1)
            if atrib:
                valor_i = atrib.atributo_ids
            else:
                valor_i = config_id[0].item_ids[0].default


        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': order_id,
            'lot_id': lot_id,
            'to_word': to_word,
            'moneda': moneda,
            'name_i': name_i,
            'valor_i': valor_i,
        }
