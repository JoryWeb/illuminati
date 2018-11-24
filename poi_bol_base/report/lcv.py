# -*- encoding: utf-8 -*-
##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>). All Rights Reserved.
#    Autor: Nicolas Bustillos
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api, _
import logging

#from openerp.addons.poi_bol_payment_request.models.account_expenses_rendition import LCV_QUERY_INDIVIDUAL as LCV_QUERY_REND
#from openerp.addons.poi_purchase_imports.report.lcv import LCV_QUERY_INDIVIDUAL as LCV_QUERY_IMP

_logger = logging.getLogger(__name__)

#El reporte jala facturas abiertas o pagadas ó impositivamente Anuladas (que pueden ser draft o cancel)
#Este query representa la parte INDIVIDUAL del modulo poi_bol_base, que sera creado como una Vista SQL independiente. Posteriormente se armara un query general UNION con los reportes independientes de cada modulo
#    ¡OJO!. Actualmente los módulos poi_bol_pos,poi_purchase_import,poi_bol_payment_request trabajan sobre este mismo query. Cualquier cambio en la estructura del query debe contemplarse también en estos módulos
LCV_QUERY_INDIVIDUAL = """
select *,(monto + descuento) as importe ,(monto + descuento - exento - ice) as subtotal_c,(monto + descuento - ice - exporta - exento) as subtotal_v,(ice + exento) as monto_nosujeto 
FROM
(
    select case when ai.type = 'out_invoice' then 'out' when (ai.type = 'in_refund' and ai.tipo_fac in ('5')) then 'out' when ai.type='in_invoice' then 'in' when (ai.type = 'out_refund' and ai.tipo_fac in ('6')) then 'in' else 'NA' end as case
        ,case when ai.type = 'out_invoice' then '3' when (ai.type = 'in_refund' and ai.tipo_fac in ('5')) then '7' when ai.type='in_invoice' then '1' when (ai.type = 'out_refund' and ai.tipo_fac in ('6')) then '2' else 'NA' end as spec
        ,ai.tipo_com,case when ai.estado_fac = 'A' then '0' else ai.nit end as nit,case when ai.estado_fac = 'A' then 'ANULADA' else coalesce(ai.razon,'') end as razon,ai.cc_nro,ai.cc_nro::bigint as cc_nro_int,coalesce(ai.imp_pol,'0') as imp_pol,ai.cc_aut,to_char(coalesce(ai.cc_date,ai.date_invoice),'DD/MM/YYYY') as cc_fecha,coalesce(ai.cc_date,ai.date_invoice) as date_invoice,Extract('year' from coalesce(ai.cc_date,ai.date_invoice)) as year_invoice,Extract('month' from coalesce(ai.cc_date,ai.date_invoice)) as month_invoice
        ,case when ai.estado_fac = 'A' then 0 else round(cast(coalesce(ai.total_bs,0) as numeric),2) end as monto,case when ai.estado_fac = 'A' then 0 else round(cast(coalesce(ai.ice,0) as numeric),2) end as ice,case when ai.estado_fac = 'A' then 0 else round(cast(coalesce(ai.exento,0) as numeric),2) end as exento,case when ai.estado_fac = 'A' then 0 else round(cast(coalesce(ai.exporta,0) as numeric),2) end as exporta,case when ai.estado_fac = 'A' then 0 else round(cast(coalesce(ai.sum_desc,0) as numeric),2) end as descuento
        ,case when ai.estado_fac = 'A' then 0 else round(cast((coalesce(ai.total_bs,0) - coalesce(ai.ice,0) -  coalesce(ai.exento,0)) as numeric),2) end as monto_neto,case when ai.estado_fac = 'A' then 0 else round(cast(((ai.total_bs - coalesce(ai.ice,0) -  coalesce(ai.exento,0)) * 0.13) as numeric),2) end as monto_iva,case when ai.estado_fac = 'A' then '0' else coalesce(ai.cc_cod,'0') end as cc_cod,coalesce(ai.cc_dos,0) as cc_dos, coalesce(dos.name,'') as cc_dos_name 
        ,ai.state,coalesce(ai.tipo_com,'1') as tipo_com_val,ai.estado_fac,ai.estado_fac as estado_fac_val,ai.company_id
        ,ai.id as res_id,'account.invoice'::varchar as res_obj,ai.number as res_name,'Factura'::varchar as res_type,coalesce(dos.warehouse_id,0) as shop_id, ai.move_id as move_id
        ,to_char(coalesce(origen.cc_date,origen.date_invoice),'DD/MM/YYYY') as origen_cc_fecha,coalesce(origen.cc_date,origen.date_invoice) as origen_date_invoice,origen.cc_nro as origen_cc_nro, origen.cc_aut as origen_cc_aut, (coalesce(origen.total_bs,0) + coalesce(origen.sum_desc,0)) as origen_monto, ai.create_uid as user_id
    from account_invoice ai
        left outer join poi_bol_base_cc_dosif dos on dos.id=ai.cc_dos
        left outer join account_invoice origen on ai.note_from_id=origen.id
    where (ai.state in ('open','paid') or (ai.state in ('draft','cancel') and ai.estado_fac = 'A')) 
        and ai.tipo_fac != '12' 
        and ai.estado_fac = ANY(CASE WHEN ai.type = 'out_invoice' THEN ARRAY['V','A','C','E','N'] ELSE ARRAY['V'] END)
        and (ai.id in (select il.invoice_id from account_invoice_line il inner join account_invoice_line_tax ilt on il.id = ilt.invoice_line_id inner join account_tax tx on ilt.tax_id = tx.id
                                                                    where tx.apply_lcv = True group by il.invoice_id))

) as lcv where lcv.case in ('in','out') order by lcv.cc_nro_int,lcv.date_invoice
            """

class PoiLcvIndex(models.Model):
    #Objeto creado para listar las Vistas SQL de diferentes modulos instalados. Sobre cada instalacion/actualizacion se recosntruye el query general mediante UNIONs entre estas Vistas SQL
    _name = "poi_bol.lcv.report.index"
    _description = "Indice de Reportes LCV"

    name = fields.Char('Name', help="Nombre de la vista SQL que contiene los datos LCV a ser consolidado con los demas reportes")
    module = fields.Text('Module')
    notes = fields.Text('Notes')


class PoiLcv(models.Model):
    _name = "poi_bol.lcv.report"
    _description = "Libro de Compras y Ventas"
    _auto = False

    case = fields.Char('Caso', size=3, readonly=True)
    spec = fields.Selection([('1','Libro de Compras'),('2','Libro de Compras - Notas C/D'),('3','Libro de Ventas'),('6','Libro de Ventas - Reintegros'),('7','Libro de Ventas - Notas C/D'),('NA','NO APLICA')],
                            string=u'Especificación', help=u"Tipificación de especificación predeterminada para Libros CV según Impuestos Internos")
    tipo_com = fields.Selection([('1','Mercado Interno'),('2','Mercado Interno NO gravadas'),('3','Sujetas a proporcionalidad'),('4','Destino Exportaciones'),('5','Interno y Exportaciones')], 'Tipo de Compra', help=u"Tipificación de facturas de Compra según Impuestos Internos", readonly=True)
    tipo_com_val = fields.Char('Tipo de Compra', size=1, readonly=True)
    nit = fields.Char('NIT', size=11, readonly=True)
    razon = fields.Char(u'Razón Social',size=124, readonly=True)
    importe = fields.Float('Importe Total', digits=(16,2), readonly=True, help=u"Importe total antes del descuento.")
    monto = fields.Float('Monto', digits=(16,2), readonly=True)
    monto_iva = fields.Float('IVA', digits=(16,2), readonly=True)
    monto_neto = fields.Float('Neto', digits=(16,2), readonly=True)
    monto_nosujeto = fields.Float(u'Importe no sujeto a crédito fiscal', digits=(16, 2), readonly=True)
    date_invoice = fields.Date('Fecha factura', readonly=True)
    month_invoice = fields.Integer('Mes factura', readonly=True)
    year_invoice = fields.Integer(u'Año factura', readonly=True)
    cc_fecha = fields.Char('Fecha', size=13, readonly=True)
    cc_nro = fields.Char(u'N° Factura', readonly=True)
    cc_nro_int = fields.Integer('Nro. Factura Entero', readonly=True)
    cc_aut = fields.Char(u'Nro. Autorización', readonly=True)
    cc_cod = fields.Char(u'Código control', size=14, readonly=True)
    cc_dos = fields.Many2one('poi_bol_base.cc_dosif', u'Dosificación', readonly=True)
    cc_dos_name = fields.Char(u'Dosificación nombre', readonly=True)
    estado_fac = fields.Selection([('V','Válida'),('A','Anulada'),('E','Extraviada'),('N','No Utilizada'),('C','En Contingencia')],'Estado Factura')
    estado_fac_val = fields.Char('Estado Factura', size=1)
    ice = fields.Float('Importe ICE', digits=(16,2), readonly=True)
    exento = fields.Float('Importe Exentos', digits=(16,2), readonly=True)
    exporta = fields.Float('Exportaciones', digits=(16,2), readonly=True)
    descuento = fields.Float('Descuentos obtenidos', digits=(16,2), readonly=True)
    subtotal_c = fields.Float('Subtotal', digits=(16,2), readonly=True, help="Subtotal E = A - B")
    subtotal_v = fields.Float('Subtotal', digits=(16,2), readonly=True, help="Subtotal E = A - B -C -D")
    imp_pol = fields.Char(u'Nro. Poliza Import.', size=16, readonly=True)
    state = fields.Char('Estado', size=20)
    company_id = fields.Many2one('res.company',string='Empresa')
    shop_id =fields.Many2one('stock.warehouse', 'Shop')
    res_id = fields.Integer('id interno')
    res_obj = fields.Char('objeto interno')
    res_name = fields.Char(u'Nombre transacción')
    res_type = fields.Char(u'Tipo transacción')
    origen_monto = fields.Float('Monto Original', digits=(16,2), readonly=True)
    origen_date_invoice = fields.Date('Fecha Factura Original')
    origen_cc_fecha = fields.Char('Fecha Factura Original', size=13, readonly=True)
    origen_cc_nro = fields.Char(u'N° Factura Original', readonly=True)
    origen_cc_aut = fields.Char(u'N° Autorización Original', readonly=True)
    user_id = fields.Many2one('res.users', string='Usuario', readonly=True)
    user_shop = fields.Many2one('stock.warehouse', string='Sucursal usuario', related='user_id.shop_assigned', readonly=True)
    move_id = fields.Many2one('account.move', string='Asiento contable', readonly=True)

    _order = "cc_nro_int,date_invoice"

    @api.model_cr
    def init(self):
        #Al momento de iniciar el addon SOLO se crea una Vista SQL que contiene el query individual de este modulo unicamente. Esta vista no estara vinculada a este objeto poi_lcv
        cr = self._cr
        table = "poi_bol_lcv_report_base"

        individual_query_to_exe = LCV_QUERY_INDIVIDUAL

        try:
            cr.execute("""

            DROP VIEW IF EXISTS %s CASCADE;
            CREATE VIEW %s as ((
            SELECT *
                FROM ((
                    %s
                )) as base
            ))""" % (table, table, individual_query_to_exe))

        except Exception as e:
            _logger.exception('ERROR en la creación del LCV!')
            return True

    @api.model
    def rebuild_view_union(self):
        #Esta funcion es la que crea la Vista SQL final asociada a este objeto poi_lcv
        #Esta funcion es llamada desde un archivo xml DESPUES de registrar su Vista SQL especifica a este modulo en la tabla de Indices, de donde se saca todas las demas Vistas SQL de otros modulos y se ensamblan aqui

        cr = self._cr
        table = "poi_bol_lcv_report"
        union_query_to_exe = ""
        cr.execute("""
                    SELECT name
                    FROM poi_bol_lcv_report_index
                    ORDER BY id;
                    """)
        indexes = cr.fetchall()
        for i,index in enumerate(indexes):
            if i > 0:
                union_query_to_exe += """
                    UNION
                """
            q = index[0]
            union_query_to_exe += ("""SELECT 
                                            "case"::varchar,	spec::varchar, 	tipo_com::varchar, 	nit::varchar, 	razon::varchar, 	cc_nro::varchar, 	cc_nro_int::bigint, 	imp_pol::varchar, 	cc_aut::varchar
                                            , 	cc_fecha::varchar, 	date_invoice::date, 	year_invoice::integer, 	month_invoice::integer
                                            , 	COALESCE(monto,0) as monto, 	COALESCE(ice,0) as ice, 	COALESCE(exento,0) as exento, 	COALESCE(exporta,0) as exporta, 	COALESCE(descuento,0) as descuento, 	COALESCE(monto_neto,0) as monto_neto, 	COALESCE(monto_iva,0) as monto_iva
                                            , 	cc_cod::varchar, 	cc_dos::integer, cc_dos_name::varchar, 	state::varchar, 	tipo_com_val::varchar, 	estado_fac::varchar, 	estado_fac_val::varchar
                                            , 	company_id::integer, 	res_id::integer, 	res_obj::varchar, 	res_name::varchar, 	res_type::varchar, move_id::integer, 	shop_id::integer, 	origen_cc_fecha::varchar, 	origen_date_invoice::date, 	origen_cc_nro::varchar, 	origen_cc_aut::varchar, 	COALESCE(origen_monto,0) as origen_monto
                                            , 	user_id::integer, 	COALESCE(importe,0)::numeric as importe, 	subtotal_c::numeric, 	subtotal_v::numeric, 	monto_nosujeto::numeric 
                                        FROM %s """ % q)

        try:
            cr.execute("""
                        DROP MATERIALIZED VIEW IF EXISTS %s CASCADE;
                        CREATE MATERIALIZED VIEW %s as ((
                            SELECT row_number() over() as id, *
                            FROM ((
                                %s
                            )) as lcv order by lcv.cc_nro_int,lcv.date_invoice
                        ))""" % (table, table, union_query_to_exe))
        except Exception as e:
            _logger.exception('ERROR en la creación del LCV!')
            # table = "poi_bol_lcv_report_rendition"

            #AccountExpensesRenditionInvoice.init(cr)
            #self.pool.get('poi_bol.import.lcv.report').init(cr)
            return True

    def hook_union_append(self, cr):
        #DEPRECADO. Esta funcion ya no es llamada para armar el query
        return ""

    @api.multi
    def open_doc(self):

        for doc in self:

            return {
                'name': '',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': doc.res_obj,
                'res_id': doc.res_id,
                'type': 'ir.actions.act_window',
            }

    @api.multi
    def open_move(self):

        for doc in self:
            return {
                'name': '',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'account.move',
                'res_id': doc.move_id.id,
                'type': 'ir.actions.act_window',
            }