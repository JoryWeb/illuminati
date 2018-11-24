##############################################################################
#
#   Copyright (c) 2013 Poiesis Consulting (http://www.poiesisconsulting.com)
#   @author Carlos Iturri
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
from openerp.report import report_sxw
from openerp.osv import osv
import logging
from openerp.addons.report_webkit import webkit_report
import time
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#_logger = logging.getLogger(__name__)

#-------------------------------------------------------------
#ENGLISH
#-------------------------------------------------------------

to_19 = ( 'Cero',  'Uno', 'Dos',  'Tres', 'Cuatro',   'Cinco',   'Seis',
          'Siete', 'Ocho', 'Nueve', 'Diez',   'Once', 'Doce', 'Trece',
          'Catorce', 'Quince', 'Dieciseis', 'Diecisiete', 'Dieciocho', 'Diecinueve' )
tens  = ( 'Veinte', 'Treinta', 'Cuarenta', 'Cincuenta', 'Sesenta', 'Setenta', 'Ochenta', 'Noventa')
hundreds = ('Ciento','Doscientos','Trescientos','Cuatrocientos','Quinientos','Seiscientos','Setecientos','Ochocientos','Novecientos')
denom = ( '',
          'Mil',     'Millon',         'Billon',       'Trillon',       'Quadrillion',
          'Quintillion',  'Sextillion',      'Septillion',    'Octillion',      'Nonillion',
          'Decillion',    'Undecillion',     'Duodecillion',  'Tredecillion',   'Quattuordecillion',
          'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Novemdecillion', 'Vigintillion' )

def _convert_nn2(val):
    """convert a value < 100 to English.
    """
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                if val>20 and val<30:
                    return "Veinti"+to_19[val % 10]
                else:
                    return dcap + ' Y ' + to_19[val % 10]
            return dcap
def _convert_nnn2(val):
    """
        convert a value < 1000 to english, special cased because it is the level that kicks 
        off the < 100 special case.  The rest are more general.  This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        if val==100:
            word="Cien"
        else:
            word = hundreds[rem-1]
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn2(mod)
    return word

def english_number2(val):
    if val < 100:
        return _convert_nn2(val)
    if val < 1000:
         return _convert_nnn2(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn2(l) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ', ' + english_number2(r)
            return ret
        
def amount_to_text2(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = english_number2(int(list[0])).upper()
    end_word = english_number2(int(list[1])).upper()
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and 'CENTAVOS' or 'CENTAVOS'
    final_result = start_word #+' BOLIVIANOS' #+ end_word +' '+cents_name
    return final_result

def monto_centavos(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    cents_number = str(list[1])
    return cents_number

class sale_order(osv.osv):
    _inherit = "sale.order"

    def view_oferta(self, cr, uid, ids, context=None):
        if context==None:
            context={}
        tipo_producto=self.browse(cr, uid, ids[0]).product_type.name
        
        if (tipo_producto=='CUBIERTAS'):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.cubiertas.webkit',
                'webkit_header': 'poi_webkit.base_reports_cotizacion_pretensa_header',
               # 'datas': datas,
            }
        if (tipo_producto=='VIGUETAS'):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.ofertaproductoviguetassolo.webkit',
                'webkit_header': 'poi_webkit.base_reports_cotizacion_pretensa_header',
               # 'datas': datas,
            }
        if (tipo_producto=='REJILLA DE JARDIN' or tipo_producto=='BARRERA DE AUTOPISTA'):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.ofertaproductorejilla.webkit',
                'webkit_header': 'poi_webkit.base_reports_cotizacion_pretensa_header',
               # 'datas': datas,
            }
        if (tipo_producto=='TABIPLAST'):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.ofertaproductotabiplast.webkit',
                'webkit_header': 'poi_webkit.base_reports_cotizacion_pretensa_header',
               # 'datas': datas,
            }

        if (tipo_producto=='EPS' or
            tipo_producto=='PLACA Y/O POSTE' or tipo_producto=='CORDON DE ACERA' or 
            tipo_producto=='CUBIERTAS'):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.ofertaproductoviguetas.webkit',
                'webkit_header': 'poi_webkit.base_reports_cotizacion_pretensa_header',
               # 'datas': datas,
            }
        if (tipo_producto=='VIGUETAS + EPS'):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.ofertaproductoviguetaseps.webkit',
                'webkit_header': 'poi_webkit.base_reports_cotizacion_pretensa_header',
               # 'datas': datas,
            }
        if (tipo_producto=='LOSA HUECA'):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.ofertaproductolosahueca.webkit',
                'webkit_header': 'poi_webkit.base_reports_cotizacion_pretensa_header',
               # 'datas': datas,
            }    
            
        else:
            return False
            
class oferta_producto(report_sxw.rml_parse):
    
    def __init__(self, cr, uid,  ids, context):
        super(oferta_producto, self).__init__(cr, uid, ids, context=context)
        
       #for acc in self.browse(cr,uid, ids, context=context):
       #list_field=order.product_type.fields
        for order in self.pool.get('sale.order').browse(cr, uid, context.get('active_id'), context=context):
            try:
                altura_compresion = order.x_carpeta_compresion
                altura_eps = order.x_altura_eps
                total_eps = int(altura_compresion) + int(altura_eps)
            except Exception:
                altura_compresion = False
                altura_eps = False
                total_eps = 0
            try:
                eje=order.x_eje
            except Exception:
                eje = False

            try:
                peso_propio = order.x_calidad_hormigon
                sobrecarga = order.x_sobrecarga
                carga_muerta = order.x_carga_muerta
                carga_total = int(peso_propio) + int(sobrecarga) + int(carga_muerta)
            except Exception:
                peso_propio = False
                sobrecarga = False
                carga_muerta = False
                carga_total = 0
            try:
                vh=order.x_v_h
            except Exception:
                vh=False
            try:
                area_referencial=order.x_area_refentcial
            except Exception:
                area_referencial = False

            try:
                altura_vigueta=order.x_altura_vigueta
            except Exception:
                altura_vigueta=False

            try:
                carpeta_compresion=order.x_carpeta_compresion
            except Exception:
                carpeta_compresion = False
            try:
                densidad=order.x_densidad
            except Exception:
                densidad=False

            try:
                ancho=order.x_ancho
            except Exception:
                ancho=False
            try:
                altura=order.x_altura
            except Exception:
                altura=False
            try:
                densidad1=order.x_densidad1
            except Exception:
                densidad1=False
            try:
                color=order.x_color
            except Exception:
                color=False

            try:
                dato_pie_pagina=order.warehouse_id.name
            except Exception:
                dato_pie_pagina = False
            try:
                hormigon=order.x_hormigon
            except Exception:
                hormigon = False
            try:
                cemento=order.x_cemento
            except Exception:
                cemento = False
            try:
                arena=order.x_arena
            except Exception:
                arena = False
            try:
                grava=order.x_grava
            except Exception:
                grava = False
            try:
                acero=order.x_acero
            except Exception:
                acero = False
            try:
                espesor=order.x_espesor
            except Exception:
                espesor = False
            try:
                tipo_eps=order.x_tipoeps
            except Exception:
                tipo_eps = False
            try:
                lugar_entrega=order.x_lugarentrega
            except Exception:
                lugar_entrega = False
            try:
                tipo_producto=order.product_type.name
            except Exception:
                tipo_producto = False

            if lugar_entrega==False:
                lugar_entrega=''
            if tipo_eps==False:
                tipo_eps=''
            if densidad1==False:
                densidad1=''
            if espesor==False:
                espesor=''
            if color==False:
                color=''

            direccion=order.warehouse_id.street
            nombre_tienda=order.warehouse_id.name
            nombre=order.warehouse_id.name
            telefono=order.warehouse_id.phone
            date=order.date_order
            fax=order.warehouse_id.fax
            email=order.warehouse_id.email
            mobile=self.pool.get('res.users').browse(self.cr,self.uid,self.uid).mobile
            amount_total=order.amount_total
            sale_order=self.pool.get('sale.order').browse(self.cr,self.uid,context.get('active_id'))
            pricelist_id=sale_order.pricelist_id
            currency=pricelist_id.currency_id.symbol

            i=amount_total
            lang = 'en'

            literal=amount_to_text2(i, lang)
            centavos=monto_centavos(i, lang)

            if (direccion==False):
                direccion=''
            if (nombre==False):
                nombre=''
            if (telefono==False):
                telefono=''
            if (fax==False):
                fax=''
            if (email==False):
                email=''
            if (mobile==False):
                mobile=''

            pie_sucursal=str(nombre)+': '+str(direccion)+' Tel.'+str(telefono)+' - Fax.'+str(fax)
            mail_sucursal='Email.'+str(email)
            puesto=self.pool.get('res.users').browse(self.cr,self.uid,self.uid).function
            if puesto==False:
                puesto=''

            #date = datetime.strptime(date, '%Y-%m-%d').date()
            date = time.strftime("%Y-%m-%d")
            mes=time.strftime('%B')
            dia=time.strftime('%d')
            ano=time.strftime('%Y')

            if mes=='Jan' or mes=='January':
                mes='Enero'
            if mes=='Feb' or mes=='February':
                mes='Febrero'
            if mes=='Mar' or mes=='March':
                mes='Marzo'
            if mes=='Apr' or mes=='April':
                mes='Abril'
            if mes=='May' or mes=='May':
                mes='Mayo'
            if mes=='June':
                mes='Junio'
            if mes=='July':
                mes='Julio'
            if mes=='Aug' or mes=='August':
                mes='Agosto'
            if mes=='Sep' or mes=='September':
                mes='Septiembre'
            if mes=='Oct' or mes=='October':
                mes='Octubre'
            if mes=='Nov' or mes=='November':
                mes='Noviembre'
            if mes=='Dec' or mes=='December':
                mes='Diciembre'
        
        self.localcontext.update({
                            'color':color,
                            'user_name': self.pool.get('res.users').browse(self.cr,self.uid,self.uid).name,
                            'mobile': mobile,
                            'puesto': puesto,
                            'altura':int(altura),      
                            'ancho':int(ancho),
                            'densidad':int(densidad),
                            'currency':currency,
                            'carpeta_compresion':int(carpeta_compresion),      
                            'altura_vigueta':int(altura_vigueta),
                            'area_referencial':int(area_referencial),      
                            'sobrecarga':int(sobrecarga),
                            'vh':float(vh),
                            'altura_compresion':int(altura_compresion),
                            'altura_eps':int(altura_eps),
                            'eje':int(eje),
                            'total_eps':total_eps,
                            'carga_total':carga_total,
                            'pie_sucursal':pie_sucursal,
                            'mail_sucursal':mail_sucursal,
                            'carga_muerta': int(carga_muerta),
                            'peso_propio': int(peso_propio),
                            'literal': literal,
                            'centavos': centavos,
                            'dia': dia,
                            'mes': mes,
                            'ano': ano,
                            'planta_industrial': str(direccion),
                            'telefono': str(telefono),
                            'fax': str(fax),
                            'nombre_tienda': nombre_tienda.upper(),
                            'hormigon':float(hormigon),
                            'cemento':float(cemento),
                            'arena':float(arena),
                            'grava':float(grava),
                            'acero':float(acero),
                            'tipo_eps':str(tipo_eps),
                            'lugar_entrega':str(lugar_entrega),
                            'tipo_producto':str(tipo_producto),
                            'densidad1':str(densidad1),
                            'espesor':str(espesor),
                            })

    def _get_currecy_USD(self, cr, uid, date_move):
        
        cr.execute(""" select get_last_currency_rate('USD','"""+date_move+"""')""")
       
        if cr.fetchall():  
             cr.execute(""" select get_last_currency_rate('USD','"""+date_move+"""')""")    
             return [x[0] for x in cr.fetchall()]
        else:
             raise osv.except_osv('Porfavor Configure','el tipo de cambio a la fecha: '+date_move)
             return False  

webkit_report.WebKitParser('report.account.ofertaproductoviguetas.webkit',
                      'sale.order',
                      'addons/poi_x_pretensa/report/oferta_producto.mako',
                      parser=oferta_producto)

webkit_report.WebKitParser('report.account.ofertaproductotabiplast.webkit',
                      'sale.order',
                      'addons/poi_x_pretensa/report/oferta_productotabiplast.mako',

                      parser=oferta_producto)
webkit_report.WebKitParser('report.account.ofertaproductoviguetassolo.webkit',
                      'sale.order',
                      'addons/poi_x_pretensa/report/oferta_productoviguetas.mako',

                      parser=oferta_producto)
webkit_report.WebKitParser('report.account.ofertaproductorejilla.webkit',
                      'sale.order',
                      'addons/poi_x_pretensa/report/oferta_productorejilla.mako',
                      parser=oferta_producto)

webkit_report.WebKitParser('report.account.cubiertas.webkit',
                      'sale.order',
                      'addons/poi_x_pretensa/report/cubiertas.mako',
                      parser=oferta_producto)

webkit_report.WebKitParser('report.account.ofertaproductoviguetaseps.webkit',
                      'sale.order',
                      'addons/poi_x_pretensa/report/oferta_productoviguetaseps.mako',
                      parser=oferta_producto)

webkit_report.WebKitParser('report.account.ofertaproductolosahueca.webkit',
                      'sale.order',
                      'addons/poi_x_pretensa/report/oferta_productolosahueca.mako',
                      parser=oferta_producto)


