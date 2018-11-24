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
import time

from openerp.report import report_sxw
from openerp.osv import osv
from openerp.tools.translate import _
import logging
from datetime import datetime
from openerp.addons.report_webkit import webkit_report

_logger = logging.getLogger(__name__)

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
    cents_number = int(list[1])
    return cents_number

class account_moverep(report_sxw.rml_parse):
    
    

    def __init__(self, cr, uid,  ids, context):
        super(account_moverep, self).__init__(cr, uid, ids, context=context)
        
       #for acc in self.browse(cr,uid, ids, context=context):
        acc_move = context.get('active_id')
        move_id = self.pool.get('account.voucher').browse(cr, uid, acc_move)
        move_line = self.pool.get('account.move.line').search(cr, uid, [('move_id', '=', move_id.id)])
        nit = ''
        # Actualziado para pretensa no utilizan el dato maestro de proveedor
        nombre_facturar = move_id.proveedor
        monto = ''
        concepto = move_id.name
        razon_social = ''
        cuenta_analitica = ''
        numero = move_id.number
        date = move_id.date

        for field in move_id.move_id.line_ids:
            if field.analytic_account_id:
                cuenta_analitica = field.analytic_account_id.name
            # monto1=field.monto
            # if monto1 != 00:
            #     nit = field.nit
            #     nombre_facturar = field.name
            #     monto = field.monto
            #     concepto = field.move_id.ref
            #     razon_social = field.razon
            #     cuenta_analitica = field.analytic_account_id.name
            #     numero = field.move_id.name
            #     date = field.date
            #     continue
        #monto=move_id.amount
        #for field in self.pool.get('account.move.line').browse(self.cr,self.uid,move_line):
        #    monto+=field.monto

        monto = move_id.amount
        account_move = self.pool.get('account.move').browse(self.cr, self.uid, move_id.move_id.id)
        journal_id = account_move.journal_id
        currency = journal_id.currency_id
        
        if not currency or currency == '' or currency == False:
            compania = self.pool.get('res.users').browse(cr, uid, uid).company_id
            currency = compania.currency_id.symbol
        else:
            currency = currency.symbol
        
            
        try:
            if (nit==False)or not nit:
                nit=''
            if (nombre_facturar==False):
                nombre_facturar=''
            if (monto==False):
                monto=''
            if (concepto==False):
                concepto=''
            if (razon_social==False):
                razon_social=''
            if (cuenta_analitica==False):
                cuenta_analitica=''
            if (numero==False):
                numero=''
        except Exception:  
            raise osv.except_osv(_('Error!'), _('No puede imprimir el Recibo porque no tiene un monto'))
            return False
        
        i=monto
        lang = 'en'
        literal=amount_to_text2(i, lang)
        centavos=monto_centavos(i, lang)
        
        #now = time.strftime("%c")
        date=datetime.strptime(date, '%Y-%m-%d').date()
        mes=date.strftime('%B')
        dia=date.strftime('%d')
        ano=date.strftime('%Y')
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

        
        monto='{:,.2f}'.format(monto)   
          
        self.localcontext.update({
                                  'nit': nit,
                                  'nombre_facturar': nombre_facturar,
                                  'monto': monto,
                                  'concepto': concepto,
                                  'razon_social':razon_social,
                                  'cuenta_analitica':cuenta_analitica,
                                  'numero':numero,
                                  'currency': currency,
                                  'literal': literal,
                                  'mes': mes,
                                  'dia': dia,
                                  'ano': ano,
                                  'centavos': centavos,
                                  })
    

     
         
#webkit_report.WebKitParser('report.account.reciborepegreso.webkit',
#                      'account.move',
#                      'addons/poi_x_pretensa/report/recibo_move.mako',
#                      parser=account_moverep)

webkit_report.WebKitParser('report.account.recibovoucher.webkit',
                      'account.voucher',
                      'addons/poi_x_pretensa/report/recibo_move_voucher.mako',
                      parser=account_moverep)
