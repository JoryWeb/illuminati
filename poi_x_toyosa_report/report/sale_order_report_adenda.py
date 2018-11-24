#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from odoo import api, models, fields, api
from odoo.addons.poi_bol_base.models.amount_to_text_es import to_word, MONEDAS
from odoo.exceptions import Warning, ValidationError

class ReportSaleAdenda(models.AbstractModel):
    _name = 'report.poi_x_toyosa_report.sale_template_adenda'

    @api.multi
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('poi_x_toyosa_report.sale_template_adenda')
        sale_id = self.env[report.model].browse(docids)

        if not sale_id.order_id:
            raise Warning('No se puede Imprimir la adenda por no tener ninguna otra cotizacion para los antedecentes de la misma.')
        if not sale_id.state in ('sale', 'done'):
            raise Warning('No se puede Imprimir la adenda por no estar confirmada aun.')

        for l in sale_id.order_line:
            if l.lot_id:
                lot_id = l.lot_id
                break

        if not lot_id:
            raise Warning('No se puede Imprimir la adenda por no tener chasis.')

        #if lot_id.get_state_reserve()!= 'reservado_ilimitado':
            #raise Warning('El Chasis Seleccionado no se encuentra con Reserva Tipo Ilimitada.')
        ov_ids = self.env['sale.order'].search([('name', '=', lot_id.contract_ref.split('-')[0].strip())], limit=1)
        if ov_ids:
            ov_origin = ov_ids[0]
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': sale_id,
            'lot_id': lot_id,
            'ov_origin': ov_ids,
        }
