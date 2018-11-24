#!/usr/bin/env python
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import config

from openerp.addons.web.controllers.main import ExcelExport
import datetime
import codecs
import os
import base64
import contextlib
import csv
import re
#from cStringIO import StringIO
from io import StringIO
try:
    import xlwt
except ImportError:
    xlwt = None

#Tipos no soportados aun: ('4','Libro de Ventas: Estaciones de servicio'),('5','Libro de Ventas: Prevaloradas Agrupadas'),('6','Libro de Ventas: Reintegros')
LCV_TYPES = [('1','Libro de Compras'),('2',u'Libro de Compras: Notas de Crédito-Débito'),('3','Libro de Ventas'),('7',u'Libro de Ventas: Notas de Crédito-Débito')]


def gen_xls(fields, rows, context=None):
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet('LCV')

    if context:
        title_style = xlwt.easyxf('font: bold on, height 240; align: wrap off, horiz center')
        label_style = xlwt.easyxf('font: bold on; align: wrap off, horiz right')
        value_style = xlwt.easyxf('font: bold off; align: wrap off, horiz left; borders: bottom thin, top thin, left thin, right thin')


        if context.get('lcv_spec','') != '':
            title = [item[1] for item in LCV_TYPES if item[0] == context.get('lcv_spec','')][0].upper()
        else:
            title = ""
        worksheet.write(0, 7, title, title_style)

        worksheet.write(2, 2, u"AÑO:", label_style)
        worksheet.write(2, 3, context.get('lcv_year',''), value_style)
        worksheet.write(2, 4, "MES:", label_style)
        worksheet.write(2, 5, context.get('lcv_month',''), value_style)

        worksheet.write(4, 2, "NOMBRE O RAZON SOCIAL:", label_style)
        worksheet.write(4, 3, context.get('lcv_razon',''), value_style)
        worksheet.write(4, 9, "NIT:", label_style)
        worksheet.write(4, 10, context.get('lcv_nit',''), value_style)

    header_style = xlwt.easyxf('font: bold on; align: wrap yes; borders: bottom medium, top medium, left medium, right medium')
    for i, fieldname in enumerate(fields):
        worksheet.write(6, i, fieldname, header_style)
        if i==0:
            worksheet.col(i).width = 1000
        elif u'RAZÓN' in fieldname.upper():
            worksheet.col(i).width = 9000
        else:
            worksheet.col(i).width = 3700

    base_style = xlwt.easyxf('align: wrap off')
    date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
    datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')
    float_style = xlwt.easyxf('', num_format_str='####.00')

    sum_totals = []
    for row_index, row in enumerate(rows):
        for cell_index, cell_value in enumerate(row):
            cell_style = base_style
            if isinstance(cell_value, basestring):
                cell_value = re.sub("\r", " ", cell_value)
            elif isinstance(cell_value, float):
                cell_style = float_style
                if row_index == 1:
                    sum_totals.append(cell_index)
            elif isinstance(cell_value, datetime.datetime):
                cell_style = datetime_style
            elif isinstance(cell_value, datetime.date):
                cell_style = date_style
            worksheet.write(row_index + 7, cell_index, cell_value, cell_style)

    #Agregar formulas de sumatoria al final
    alpha_index = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U']
    for sum_index in sum_totals:
        worksheet.write(row_index + 8, sum_index, xlwt.Formula("SUM(%s8:%s%s)" %(alpha_index[sum_index], alpha_index[sum_index],row_index+8)), header_style)

    fp = StringIO()
    workbook.save(fp)
    fp.seek(0)
    data = fp.read()
    fp.close()
    return data

class libro_cv_1(models.TransientModel):

    _name = "poi_bol_base.libro_cv.criteria"
    _description = "Seleccionar criterios"

    @api.model
    def _prev_month_m(self):

        today = datetime.date.today()
        first = today.replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)

        return lastMonth.strftime("%m")

    @api.model
    def _prev_month_y(self):

        today = datetime.date.today()
        first = today.replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)

        return int(lastMonth.strftime("%Y"))

    month = fields.Selection([('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'), ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'), ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')],
                             string='Mes', required=True, default=_prev_month_m)
    year = fields.Integer(u'Año', size=4, required=True, default=_prev_month_y)
    spec= fields.Selection(LCV_TYPES,
                           string='Caso', required=True)
    company_id = fields.Many2one('res.company',string='Empresa', default=lambda self: self._context.get('company_id', self.env.user.company_id.id))
    shop_id = fields.Many2one('stock.warehouse', 'Sucursal', help=u"Criterio para filtrar Facturas de una Sucursal específica.")
    cc_dos = fields.Many2one('poi_bol_base.cc_dosif', u'Dosificación', help=u"Criterio para filtrar Facturas de una Dosificación específica.")

    @api.multi
    def action_next(self):

        data = self[0]
        self._cr.execute("REFRESH MATERIALIZED VIEW poi_bol_lcv_report")
        context_wiz = dict(self._context, lcv_month=int(data.month), lcv_year=data.year, lcv_company=data.company_id.id, lcv_spec=data.spec)
        #Armar las condiciones 'WHERE' para el query de la vista sql "poi_bol_lcv_report" y sus respectivos campos
        lcv_filter = """ WHERE month_invoice = %s AND year_invoice = %s AND "spec" = '%s' """ % (int(data.month), data.year, data.spec)
        if data.shop_id:
            context_wiz = dict(context_wiz, lcv_shop=data.shop_id.id)
            lcv_filter += " AND shop_id = %s " % (data.shop_id.id)
        if data.cc_dos:
            context_wiz = dict(context_wiz, lcv_dos=data.cc_dos.id)
            lcv_filter += " AND cc_dos = %s " % (data.cc_dos.id)
        context_wiz = dict(context_wiz, lcv_filter=lcv_filter)

        return {
            'name': 'Resumen preliminar',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'poi_bol_base.libro_cv.summary',
            'domain': [],
            'context': context_wiz,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class libro_cv_2(models.TransientModel):

    _name = "poi_bol_base.libro_cv.summary"
    _description = "Resumen preliminar"


    export = fields.Selection([('pdf','Formato impresión PDF'),('txt','Archivo de texto'),('xls','Libro Excel')], 'Opción de exportación', default='pdf')
    lines = fields.One2many('poi_bol_base.libro_cv.summary.line', 'summary_id', string="Resumen totalizado", ondelete="cascade")
    no_lines = fields.Boolean('No records')

    @api.multi
    def default_get(self, fields):

        res = super(libro_cv_2, self).default_get(fields)

        if 'lcv_filter' in self._context:
            where_query = self._context['lcv_filter']
            #Preparar tabla resumen de sumatorias principales
            lines_dict = False
            qry_resumen = """select SUM(monto) as "monto", SUM(monto_neto) as "neto", SUM(monto_iva) as "iva", SUM(exento) as "exento", SUM(ice) as "ice"
                                    ,COUNT(id) as "count", MIN(cc_nro_int) as "range_min",MAX(cc_nro_int) as "range_max"
                             from poi_bol_lcv_report
                             %s """ % (where_query)
            self._cr.execute(qry_resumen)
            for record in self._cr.dictfetchall():
                if record['count'] > 0:
                    lines_dict = record
                    lines_dict['range'] = str(record['range_min']) + " - " + str(record['range_max'])
                    lines_dict['label'] = "TOTALES: "
                    no_lines = False
                else:
                    lines_dict = {'label': 'NO HAY REGISTROS!', 'count': 0}
                    no_lines = True

            if lines_dict:
                res.update({'lines': [(0, 0,  lines_dict) ],'no_lines': no_lines})   #

        return res

    @api.multi
    def action_screen_view(self):

        if 'lcv_filter' not in self._context:
            raise except_orm(u'Error', 'Filtro de contexto no identificado.')

        data = self[0]

    @api.multi
    def action_next(self):

        if 'lcv_filter' not in self._context:
            raise except_orm(u'Error', 'Filtro de contexto no identificado.')
        if 'lcv_company' not in self._context:
            raise except_orm(u'Error', 'Empresa de contexto no identificada.')

        data = self[0]
        company = self.env['res.company'].browse(self._context['lcv_company'])
        context_exp = dict(self._context, lcv_nit=company.nit, lcv_razon=company.razon)
        #Especificar orden de columnas según caso de Libro
        spec = self._context['lcv_spec']
        order_query = "id"
        headers = []
        if spec in '1':
            spec_order = ['spec','nr','cc_fecha','nit','razon','cc_nro','imp_pol','cc_aut','importe','monto_nosujeto','subtotal_c','descuento','monto_neto','monto_iva','cc_cod','tipo_com_val']
            headers = ['SPEC',u'N°',u'FECHA DE LA FACTURA O DUI',u'NIT PROVEEDOR',u'NOMBRE O RAZÓN SOCIAL',u'N° DE LA FACTURA',u'N° DE DUI',u'N° DE AUTORIZACIÓN',u'IMPORTE TOTAL DE LA COMPRA \n (A)',
                       u'IMPORTE NO SUJETO A CRÉDITO FISCAL \n (B)',u'SUBTOTAL \n (C = A-B)',u'DESCUENTOS, BONIFICACIONES Y REBAJAS OBTENIDAS \n (D)',u'IMPORTE BASE PARA CRÉDITO FISCAL \n (E = C-D)',u'CRÉDITO FISCAL \n (F = E*13%)',u'CÓDIGO DE CONTROL',u'TIPO DE COMPRA']
            order_query = "date_invoice,id"
        elif spec in '2':
            spec_order = ['spec','nr','cc_fecha','cc_nro','cc_aut','estado_fac','nit','razon','importe','monto_iva','cc_cod','origen_cc_fecha','origen_cc_nro','origen_cc_aut','origen_monto']
            order_query = "date_invoice,id"
        elif spec in '3':
            spec_order = ['spec','nr','cc_fecha','cc_nro','cc_aut','estado_fac','nit','razon','importe','ice', 'exporta','exento','subtotal_v','descuento','monto_neto','monto_iva','cc_cod']
            headers = ['SPEC', u'N°', u'FECHA DE LA FACTURA', u'N° DE LA FACTURA', u'N° DE AUTORIZACIÓN', u'ESTADO', u'NIT/CI CLIENTE', u'NOMBRE O RAZÓN SOCIAL',
                       u'IMPORTE TOTAL DE LA VENTA \n (A)', u'IMPORTE ICE / IEHD / TASAS \n (B)', u'EXPORTACIONES Y OPERACIONES EXENTAS \n (C)', u'VENTAS GRAVADAS A TASA CERO \n (D)', u'SUBTOTAL \n (C = A-B-C-D)', u'DESCUENTOS, BONIFI­CACIONES Y REBAJAS OTORGADAS \n (F)', u'IMPORTE BASE PARA DÉBITO FISCAL \n (G = E-F)', u'DEBITO FISCAL \n (H = G*13%)', u'CÓDIGO DE CONTROL']
            order_query = "cc_aut,cc_nro_int,date_invoice,id"
        elif spec in '7':
            spec_order = ['spec','nr','cc_fecha','cc_nro','cc_aut','nit','razon','importe','monto_iva','cc_cod','origen_cc_fecha','origen_cc_nro','origen_cc_aut','origen_monto']
            order_query = "cc_aut,cc_nro_int,date_invoice,id"
        else:
            raise except_orm(u'Error', 'Tipo de Libro no soportado.')

        #Definir base de nombre de archivo a exportar
        odoo_data_dir = config['data_dir']
        if not os.access(odoo_data_dir, os.W_OK):
            raise except_orm(u'Error de configuración', "No es posible hacer escrituras al directorio configurado 'data_dir' (%s). Contacte al administrador de servidor." % (odoo_data_dir,))
        spec_names = {'1':'COMPRAS','2':'COMPRASNOTAS','3':'VENTAS','6':'VENTASREINTEG','7':'VENTASNOTAS'}
        filename_relative = spec_names.get(spec,'') + "_" + str(self._context['lcv_month']) + str(self._context['lcv_year']) + "_" + str(company.nit or '')
        filename_base = odoo_data_dir + "/" + filename_relative


        export_case = data.export
        if export_case == 'pdf':
            filename = filename_base + ".pdf"
            filename_relative = filename_relative + ".pdf"
            lcv_ids = []
        elif export_case == 'xls':
            filename = filename_base + ".xls"
            filename_relative = filename_relative + ".xls"
            spec_order.remove('spec')
            if 'SPEC' in headers:
                headers.remove('SPEC')

            if len(headers) == 0:
                col_desc = self.env['poi_bol.lcv.report']._columns
                for col in spec_order:
                    if col == 'nr':
                        headers.append(u'N°')
                    else:
                        headers.append(unicode(col_desc[col].string.upper()))

            if len(headers) != len(spec_order):
                raise except_orm(u'Error', 'Cabecera de formato inconsistente con datos .')

            cells = [] #array of arrays
            file = codecs.open(filename, "w","utf-8")

        elif export_case == 'txt':
            filename = filename_base + ".txt"
            filename_relative = filename_relative + ".txt"
            file = codecs.open(filename, "w","utf-8")

        else:
            raise except_orm(u'Error', 'Formato de exportación no soportado.')

        output = False
        where_query = self._context['lcv_filter']



        #ToDo: Update/Refresh (materialized) view before querying it. Ensure PoS is included if applicable
        if export_case == 'pdf':
            #get only ids to be parsed by rml
            qry_export = """SELECT array_to_string(array(select id FROM poi_bol_lcv_report %s ORDER BY %s), ',')
                          AS lcv_ids""" % (where_query,order_query)
            self._cr.execute(qry_export)
            lcv_ids_str = self._cr.fetchone()
            if lcv_ids_str:
                lcv_ids = map(int, lcv_ids_str[0].split(','))
            else:
                lcv_ids = []
            #lcv_ids = list(lcv_ids)[0]
        else:
            qry_export = """SELECT ROW_NUMBER() OVER (order by %s) AS nr,*
                         FROM poi_bol_lcv_report
                         %s
                         ORDER BY %s""" % (order_query,where_query,order_query)
            self._cr.execute(qry_export)
            for record in self._cr.dictfetchall():

                #build data according to order of case
                cols_index = ()
                for col in spec_order:

                    if col == 'razon':
                        data = unicode(record.get(col,'').strip())    #Razon Social puede contener caracteres unicode (Ñ, É, etc.)
                    else:
                        if record[col] is None:
                            data = ""
                        elif isinstance(record[col],float):
                            data = float(record[col])
                        else:
                            data = str(record[col])
                    cols_index += (data,)


                if export_case == 'xls':
                    row = []
                    for cell in cols_index:
                        row.append(cell)

                    cells.append(row)

                elif export_case == 'txt':
                    txt_row = ""
                    for i,txt in enumerate(cols_index):
                        txt_row += str(txt)
                        if i < len(cols_index) - 1:
                            txt_row += "|"
                        else:
                            txt_row += "\r\n"
                    file.write(txt_row)

        if export_case == 'txt':
            file.close()
            filename_out = filename.replace(filename_relative,"out_" + filename_relative)
            base64.encode(codecs.open(filename),codecs.open(filename_out, "w"))
            output64 = codecs.open(filename_out).read()
        elif export_case == 'xls':
            outputxls = gen_xls(headers,cells, context_exp)
            output64 = base64.encodestring(outputxls)
        elif export_case == 'pdf':
            #ToDo: Especificar por separado casos 2,6 y 7
            if spec in '1':
                report_name = 'report.lcv.1'
                context_exp = dict(context_exp, lcv_ids=lcv_ids)
                data = {'data': context_exp}
                return self.env['report'].get_action(self, 'poi_bol_base.lcv1pdf_template', data=data)
            elif spec in '2':
                report_name = 'report.lcv.2'
            elif spec in '3':
                report_name = 'report.lcv.3'
            elif spec in '7':
                report_name = 'report.lcv.7'


            context_exp = dict(context_exp, lcv_ids=lcv_ids)
            datas = {
                'ids': lcv_ids,
                'model': 'poi_bol.lcv.report',
                'context':context_exp,
            }
            return {
                   'type': 'ir.actions.report.xml',
                   'report_name': report_name,
                   'datas': datas,
                   'string' : filename,
                   'context': context_exp,
            }


        if output64:
            exporter = self.env['poi_bol_base.libro_cv.export']
            export_id = exporter.create({'name': filename_relative, 'filename': filename, 'file': output64})
            if export_id:
                return {
                    'name': 'Descargar Libro',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': False,
                    'res_model': 'poi_bol_base.libro_cv.export',
                    'domain': [],
                    'res_id': export_id.id,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                }


        return {}

    @api.multi
    def action_screen_view(self):

        if 'lcv_filter' not in self._context:
            raise except_orm(u'Error', 'Filtro de contexto no identificado.')

        data = self[0]

        spec = self._context['lcv_spec']
        month = self._context['lcv_month']
        year = self._context['lcv_year']
        if spec in ('1','2'):
            view_xml_id = 'poi_bol_base.invoice_tree_lc'
        else:
            #libro de Ventas
            view_xml_id = 'poi_bol_base.invoice_tree_lv'

        view_id = self.env.ref(view_xml_id, False)
        if not view_id:
            raise except_orm(u'System Error', u'No se encontró la Vista relacionada.')
        view_id = view_id.id

        search_view_id = self.env.ref('poi_bol_base.view_account_lc_filter', False).id

        #Get domain from context
        domain_lcv = [('spec','=',spec),('month_invoice','=', month),('year_invoice','=', year)]
        if 'lcv_shop' in self._context:
            domain_lcv.append(('shop_id','=',self._context['lcv_shop']))
        if 'lcv_dos' in self._context:
            domain_lcv.append(('cc_dos','=',self._context['lcv_dos']))


        return {
            'name': 'Libro CV',
            'type': 'ir.actions.act_window',
            'res_model': 'poi_bol.lcv.report',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': view_id,
            'search_view_id': False,
            'context': {'spec': spec},
            'domain': domain_lcv,
        }

class libro_cv_2_lines(models.TransientModel):

    _name = "poi_bol_base.libro_cv.summary.line"
    _description = "Líneas Resumen preliminar"

    summary_id = fields.Many2one('poi_bol_base.libro_cv.summary', string="Resumen")
    label = fields.Char('', required=True)
    count = fields.Integer('Conteo')
    range = fields.Char('Rango Nr.')
    monto = fields.Float('Total Monto')
    ice = fields.Float('Total ICE')
    exento = fields.Float('Total Exento')
    neto = fields.Float('Total Neto')
    iva = fields.Float('Total IVA')


class libro_cv_3(models.TransientModel):

    _name = "poi_bol_base.libro_cv.export"
    _description = "Descargar Libro"


    file = fields.Binary(string='Descargar')
    name = fields.Char('File Name')
    filename = fields.Char('File Name')
