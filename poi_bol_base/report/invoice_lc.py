##############################################################################
#
#    Copyright (C) 2012 Poiesis Consulting
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.report import report_sxw

class lcv_data(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(lcv_data, self).__init__(cr, uid, name, context=context)
        print time.localtime()
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
        if 'lcv_filter' in context:
            where_query = context['lcv_filter']
            #Preparar tabla resumen de sumatorias principales
            lines_dict = False
            qry_resumen = """select SUM(monto) as "monto", SUM(importe) as "importe", SUM(monto_neto) as "monto_neto", SUM(monto_iva) as "monto_iva", SUM(exento) as "exento", SUM(ice) as "ice"
                                    , SUM(descuento) as "descuento", SUM(subtotal_c) as "subtotal_c", SUM(subtotal_v) as "subtotal_v", SUM(exporta) as "exporta", SUM(origen_monto) as "origen_monto",COUNT(id) as "count"
                             from poi_bol_lcv_report
                             %s """ % (where_query)
            cr.execute(qry_resumen)
            for record in cr.dictfetchall():
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
        # if 'lcv_ids' in context:
        #     for lib in self.pool.get('poi_bol.lcv.report').browse(cr, uid, context['lcv_ids'], context=context):
        #         sum_monto += lib.monto
        #         sum_importe += lib.importe
        #         sum_ice += lib.ice
        #         sum_exento += lib.exento
        #         sum_descuento += lib.descuento
        #         sum_subtot_c += lib.subtotal_c
        #         sum_subtot_v += lib.subtotal_v
        #         sum_exporta += lib.exporta
        #         sum_monto_neto += lib.monto_neto
        #         sum_iva += lib.monto_iva
        #         sum_origen_monto += lib.origen_monto

        periodo = str(context.get('lcv_month','')) + '/' + str(context.get('lcv_year',''))
        razon_social = context.get('lcv_razon','')
        nit = context.get('lcv_nit','')

        user_obj = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        direccion = (user_obj.company_id.street or '') + (user_obj.company_id.street2 and ', ' or '') + (user_obj.company_id.street2 or '')
        usuario = user_obj.name
        self.localcontext.update({
            'time': time,
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
            'enumerate': enumerate,
        })
        print time.localtime()

report_sxw.report_sxw('report.report.lcv.1', 'poi_bol.lcv.report', 'addons/poi_bol_base/report/lcv_1_pdf.rml', parser=lcv_data , header=False)
report_sxw.report_sxw('report.report.lcv.2', 'poi_bol.lcv.report', 'addons/poi_bol_base/report/lcv_2_pdf.rml', parser=lcv_data , header=False)
report_sxw.report_sxw('report.report.lcv.3', 'poi_bol.lcv.report', 'addons/poi_bol_base/report/lcv_3_pdf.rml', parser=lcv_data , header=False)
report_sxw.report_sxw('report.report.lcv.7', 'poi_bol.lcv.report', 'addons/poi_bol_base/report/lcv_7_pdf.rml', parser=lcv_data , header=False)


class invoice_lct(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(invoice_lct, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.invoice.lct', 'poi_bol.lcv.report', 'addons/poi_bol_base/report/invoice_lc_t.rml', parser=invoice_lct , header=False)

#class invoice_lvt(report_sxw.rml_parse):
#    def __init__(self, cr, uid, name, context=None):
#        super(invoice_lvt, self).__init__(cr, uid, name, context=context)
#        self.localcontext.update({
#            'time': time,
#        })

#report_sxw.report_sxw('report.invoice.lvt', 'poi_bol.lcv.report', 'addons/poi_bol_base/report/invoice_lv_t.rml', parser=invoice_lvt , header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

