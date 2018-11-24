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
import time
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

class account_moverep_oficial(report_sxw.rml_parse):

    def __init__(self, cr, uid,  ids, context):
        super(account_moverep_oficial, self).__init__(cr, uid, ids, context=context)
        
       #for acc in self.browse(cr,uid, ids, context=context):
        acc_move=context.get('active_id')
        account_payment = self.pool.get('account.payment').browse(self.cr, self.uid, acc_move)
        total_amount = 0
        total_amount_sus = 0
        #for account_line in account_payment.line_cr_ids:
        #    total_amount = account_line.amount+total_amount
        #    total_amount_sus = self.pool.get('res.currency').compute(cr, uid, 62, 3, total_amount,context=context)

        currency_journal = account_payment.journal_id.currency_id.id


        compania=self.pool.get('res.users').browse(cr, uid, uid).company_id
        currency_company=compania.currency_id.id

        if not currency_journal or currency_journal=='' or currency_journal==False:
            currency_journal=currency_company



        amount_recibo=account_payment.amount
        move_line_obj = self.pool.get('account.move.line')
        move_line_ids = move_line_obj.search(self.cr, self.uid, [('payment_id', '=', acc_move)], {})
        move_line = move_line_obj.browse(self.cr, self.uid, move_line_ids[0], {})
        #number=account_payment.name
        number = move_line.move_id.name
        cliente=account_payment.partner_id.name
        telefono=account_payment.partner_id.phone
        mobile=account_payment.partner_id.mobile
        monto_num=account_payment.amount
        #monto_num = 0
        nit=account_payment.partner_id.nit

        #####Bolivianos#####
        monto_num=self.pool.get('res.currency').compute(cr, uid,currency_journal, currency_company, monto_num,context=context)
        amount_recibo=self.pool.get('res.currency').compute(cr, uid, currency_journal, currency_company, amount_recibo,context=context)

        #####Fin Bolivianos#####

        amount_recibo_2=account_payment.amount
        monto_num_2=account_payment.amount
        #monto_num_2 = 0.0
        #####Dolares#####
        monto_num_sus=self.pool.get('res.currency').compute(cr, uid, currency_journal, 3, monto_num_2, context=context)
        amount_recibo_sus=self.pool.get('res.currency').compute(cr, uid, currency_journal, 3, amount_recibo_2, context=context)

        #####Fin Dolares#####
        efectivo=account_payment.efectivo


        cheque=''
        name_bank=''
        name_bank_label=''
        name_bank=''
        number_bank_label=''
        number_bank=''
        number_transaction_label=''
        number_transaction=''

        if account_payment.journal_id.efectivo_cheque==True:
            if efectivo==True:
                efectivo= u'Efectivo:  X'
            else:
                efectivo=''

            if account_payment.cheque==True:
                cheque= u'Cheque:  X'
                name_bank_label=u'Banco :'
                name_bank=account_payment.bank.name
                number_bank_label=u'Número de Cheque :'
                number_bank=account_payment.bank_account_number
                number_transaction_label=u'Número de Transacción :'
                number_transaction=account_payment.transaction_number
            else:
                cheque=''
                name_bank_label=''
                number_bank_label=''
                number_transaction_label=''
                name_bank=''
                number_bank=''
                number_transaction=''

        i=amount_recibo
        lang = 'en'
        literal=amount_to_text2(i, lang)
        centavos=monto_centavos(i, lang)

        j=amount_recibo_sus
        literal_sus=amount_to_text2(j, lang)
        centavos_sus=monto_centavos(j, lang)

        amount_recibo='{:,.2f}'.format(amount_recibo)
        amount_recibo_sus='{:,.2f}'.format(amount_recibo_sus)
        monto_num='{:,.2f}'.format(monto_num)
        monto_num_sus='{:,.2f}'.format(monto_num_sus)

        concepto=account_payment.reference

        metodo_pago=account_payment.journal_id.name

        date= account_payment.payment_date

        fecha_actual=time.strftime('%Y-%m-%d')
        # cr.execute(""" select get_last_currency_rate('USD','"""+fecha_actual+"""')""")
        # tc = 0
        # for record in cr.fetchone():
        #     tc = record
        tc = 0

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

        if nit==False:
            nit=''
        if metodo_pago==False:
            metodo_pago=''
        if telefono==False:
            telefono=''
        if mobile==False:
            mobile=''
        if cliente==False:
            cliente=''
        if total_amount==False:
            total_amount=''
        if total_amount_sus==False:
            total_amount_sus=''
        if concepto==False:
            concepto=''
        if literal==False:
            literal=''
        if literal_sus==False:
            literal_sus=''
        if mes==False:
            mes=''
        if dia==False:
            dia=''
        if ano==False:
            ano=''
        if centavos==False:
            centavos=''
        if centavos_sus==False:
            centavos_sus=''

        if amount_recibo==False:
            amount_recibo=''

        if amount_recibo_sus==False:
            amount_recibo_sus=''


        self.localcontext.update({
                                'number': number,
                                'amount_recibo': amount_recibo,
                                'amount_recibo_sus': amount_recibo_sus,
                                'total_amount': total_amount,
                                'total_amount': total_amount_sus,
                                'monto_num': monto_num,
                                'monto_num_sus': monto_num_sus,
                                'nit': nit,
                                'metodo_pago': metodo_pago,
                                'telefono': telefono,
                                'mobile': mobile,
                                'cliente': cliente,
                                 # 'monto': monto,
                                'concepto': concepto,
                                'literal': literal,
                                'literal_sus': literal_sus,
                                'mes': mes,
                                'dia': dia,
                                'ano': ano,
                                'centavos': centavos,
                                'centavos_sus': centavos_sus,
                                'efectivo': efectivo or '',
                                'cheque': cheque or '',
                                'name_bank': name_bank or '',
                                'number_bank': number_bank or '',
                                'number_transaction': number_transaction or '',
                                'name_bank_label': name_bank_label or '',
                                'number_bank_label': number_bank_label or '',
                                'number_transaction_label': number_transaction_label or '',
                                'tc': tc or '',
                                })
    


         
webkit_report.WebKitParser('report.account.reciborepoficial.webkit',
                      'account.payment',
                      'addons/poi_x_pretensa/report/recibo_move_oficial.mako',
                      parser=account_moverep_oficial)

webkit_report.WebKitParser('report.account.reciborepoficialsus.webkit',
                      'account.payment',
                      'addons/poi_x_pretensa/report/recibo_move_oficial_sus.mako',
                      parser=account_moverep_oficial)

