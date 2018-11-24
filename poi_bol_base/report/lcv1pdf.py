#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from openerp import api, models, fields, api, _, tools

class ReportAccountInvoice(models.AbstractModel):
    _name = 'report.poi_bol_base.lcv1pdf_template'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_bol_base.lcv1pdf_template')
        if data.get('data', False):
            data = data['data']
        lcv_ids = self.env[report.model].search([('id','in',data.get('lcv_ids', False))], order="date_invoice asc")

        sum_monto = 0.0
        sum_iva = 0.0
        sum_ice = 0.0
        sum_exento = 0.0
        sum_descuento = 0.0
        sum_monto_neto = 0.0
        sum_subtot_c = 0.0
        sum_subtot_v = 0.0
        sum_exporta = 0.0
        sum_importe = 0.0
        sum_origen_monto = 0.0
        if 'lcv_filter' in data:
            where_query = data['lcv_filter']
            #Preparar tabla resumen de sumatorias principales
            lines_dict = False
            qry_resumen = """select SUM(monto) as "monto", SUM(importe) as "importe", SUM(monto_neto) as "monto_neto", SUM(monto_iva) as "monto_iva", SUM(exento) as "exento", SUM(ice) as "ice"
                                    , SUM(descuento) as "descuento", SUM(subtotal_c) as "subtotal_c", SUM(subtotal_v) as "subtotal_v", SUM(exporta) as "exporta", SUM(origen_monto) as "origen_monto",COUNT(id) as "count"
                             from poi_bol_lcv_report
                             %s """ % (where_query)
            self.env.cr.execute(qry_resumen)
            for record in self.env.cr.dictfetchall():
                if record['count'] > 0:
                    sum_monto += record['monto']
                    sum_importe += record['importe']
                    sum_ice += record['ice']
                    sum_exento += record['exento']
                    sum_descuento += record['descuento']
                    sum_subtot_c += record['subtotal_c']
                    sum_subtot_v += record['subtotal_v']
                    sum_exporta += record['exporta']
                    sum_monto_neto += record['monto_neto']
                    sum_iva += record['monto_iva']
                    sum_origen_monto += record['origen_monto']
       

        periodo = str(data.get('lcv_month','')) + '/' + str(data.get('lcv_year',''))
        razon_social = data.get('lcv_razon','')
        nit = data.get('lcv_nit','')

        user_obj = self.env['res.users'].browse(self.env.uid)
        direccion = (user_obj.company_id.street or '') + (user_obj.company_id.street2 and ', ' or '') + (user_obj.company_id.street2 or '')
        usuario = user_obj.name
        docargs = {}
        docargs.update({
            'sum_monto': '{:20,.2f}'.format(sum_monto),
            'sum_importe': '{:20,.2f}'.format(sum_importe),
            'sum_ice': '{:20,.2f}'.format(sum_ice),
            'sum_exento': '{:20,.2f}'.format(sum_exento),
            'sum_exporta': '{:20,.2f}'.format(sum_exporta),
            'sum_descuento': '{:20,.2f}'.format(sum_descuento),
            'sum_monto_neto': '{:20,.2f}'.format(sum_monto_neto),
            'sum_iva': '{:20,.2f}'.format(sum_iva),
            'sum_subtot_c': '{:20,.2f}'.format(sum_subtot_c),
            'sum_subtot_v': '{:20,.2f}'.format(sum_subtot_v),
            'razon_social': razon_social,
            'nit': nit,
            'direccion': direccion,
            'periodo': periodo,
            'usuario': usuario,
            'sum_origen_monto': '{:20,.2f}'.format(sum_origen_monto),
        })


        docargs.update({
                    'doc_ids': self._ids,
                    'doc_model': report.model,
                    'docs': lcv_ids,
                })

        report_name = 'poi_bol_base.lcv1pdf_template'
        return report_obj.render(report_name, docargs)
