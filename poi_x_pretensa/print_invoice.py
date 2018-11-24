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
from openerp.addons.report_webkit import webkit_report
from openerp.osv import fields, osv
import logging
from datetime import datetime
from openerp.exceptions import UserError
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# ENGLISH
# -------------------------------------------------------------

to_19 = ('Cero', 'Uno', 'Dos', 'Tres', 'Cuatro', 'Cinco', 'Seis',
         'Siete', 'Ocho', 'Nueve', 'Diez', 'Once', 'Doce', 'Trece',
         'Catorce', 'Quince', 'Dieciseis', 'Diecisiete', 'Dieciocho', 'Diecinueve')
tens = ('Veinte', 'Treinta', 'Cuarenta', 'Cincuenta', 'Sesenta', 'Setenta', 'Ochenta', 'Noventa')
hundreds = (
'Ciento', 'Doscientos', 'Trescientos', 'Cuatrocientos', 'Quinientos', 'Seiscientos', 'Setecientos', 'Ochocientos',
'Novecientos')
denom = ('',
         'Mil', 'Millon', 'Billon', 'Trillon', 'Quadrillion',
         'Quintillion', 'Sextillion', 'Septillion', 'Octillion', 'Nonillion',
         'Decillion', 'Undecillion', 'Duodecillion', 'Tredecillion', 'Quattuordecillion',
         'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Novemdecillion', 'Vigintillion')


def _convert_nn2(val):
    """convert a value < 100 to English.
    """
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                if val > 20 and val < 30:
                    if val % 10 == 1:
                        return "Veintiun"
                    else:
                        return "Veinti" + to_19[val % 10]
                else:
                    if val % 10 == 1:
                        return dcap + ' Y un'
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
        if val == 100:
            word = "Cien"
        else:
            word = hundreds[rem - 1]
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
            if l == 1:
                ret = 'Un' + ' ' + denom[didx]
            else:
                ret = _convert_nnn2(l) + ' ' + denom[didx]
            if r > 0:
                # ret = ret + ', ' + english_number2(r)
                ret = ret + ' ' + english_number2(r)
            return ret


def amount_to_text2(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = english_number2(int(list[0])).upper()
    end_word = english_number2(int(list[1])).upper()
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and 'CENTAVOS' or 'CENTAVOS'
    final_result = start_word  # +' BOLIVIANOS' #+ end_word +' '+cents_name
    return final_result


def monto_centavos(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    # cents_number = int(list[1])
    cents_number = (list[1])
    return cents_number


class account_invoice_pret(report_sxw.rml_parse):
    def __init__(self, cr, uid, ids, context):
        super(account_invoice_pret, self).__init__(cr, uid, ids, context=context)

        # for acc in self.browse(cr,uid, ids, context=context):
        acc_invoice = context.get('active_id')
        acount_invoice = self.pool.get('account.invoice').browse(self.cr, self.uid, acc_invoice)

        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id
        nit = company_id.nit
        logo = company_id.logo

        actividad = company_id.actividad

        account_invoice_line = self.pool.get('account.invoice.line').search(cr, uid,
                                                                            [('invoice_id', '=', acount_invoice.id)])
        total_line = 0
        discount_line = 0
        i = 0
        for acc_line in self.pool.get('account.invoice.line').browse(cr, uid, account_invoice_line, context=context):
            total_line += acc_line.price_unit * acc_line.quantity
            discount_line += acc_line.discount
            i = i + 1

        total_filas_extra = 35 - i
        # if total_filas_extra<=1:
        # total_filas=1
        # n=total_filas
        # else:
        # total_filas=32-total_filas_extra
        n = total_filas_extra

        # if total_filas_extra==0:
        # total_filas=0
        # n=total_filas



        # total_filas=[total_filas]*total_filas

        if not acount_invoice.cc_dos:
            raise UserError(_('Factura sin serie de dosificación asignado, asigne una'))
        cant = i
        if acount_invoice.cc_dos.leyenda_id == None:
            leyenda = ''
        else:
            leyenda = acount_invoice.cc_dos.leyenda_id.name.upper()

        nombre_compania = company_id.partner_id.name
        direccion_compania1 = company_id.partner_id.street
        direccion_compania2 = company_id.partner_id.street2
        telefono_compania = company_id.partner_id.phone
        ciudad_compania = company_id.partner_id.city
        pais_compania = company_id.partner_id.country_id.name

        direccion_compania12 = acount_invoice.shop_id.street
        nombre_tienda = acount_invoice.shop_id.name
        nombre_sucursal = acount_invoice.shop_id.other_info
        telefono_compania2 = acount_invoice.shop_id.phone
        if acount_invoice.date_invoice:
            date = acount_invoice.date_invoice
            date = datetime.strptime(date, '%Y-%m-%d').date()
            date = date.strftime("%d/%m/%Y")
        else:
            date = time.strftime('%Y-%m-%d')
        # date=date.strftime("%d/%m/%Y")

        amount_total = acount_invoice.amount_total

        i = amount_total
        lang = 'en'
        literal = amount_to_text2(i, lang)
        centavos = monto_centavos(i, lang)

        if centavos == 0:
            centavos = '00'

        amount_total_c = amount_total

        amount_total = '{:,.2f}'.format(amount_total)

        total_line_c = total_line

        discount_bs = ((discount_line / cant) * total_line_c) / 100

        total_line = '{:,.2f}'.format(total_line)

        discount_line = '{:,.2f}'.format(discount_line)

        discount_bs = '{:,.2f}'.format(discount_bs)

        date_invoice = acount_invoice.date_invoice
        if date_invoice == False:

            mes = ''
            dia = ''
            ano = ''
        else:
            date = datetime.strptime(date_invoice, '%Y-%m-%d').date()
            mes = date.strftime('%B')
            dia = date.strftime('%d')
            ano = date.strftime('%Y')

            if mes == 'Jan' or mes == 'January':
                mes = 'Enero'
            if mes == 'Feb' or mes == 'February':
                mes = 'Febrero'
            if mes == 'Mar' or mes == 'March':
                mes = 'Marzo'
            if mes == 'Apr' or mes == 'April':
                mes = 'Abril'
            if mes == 'May' or mes == 'May':
                mes = 'Mayo'
            if mes == 'June':
                mes = 'Junio'
            if mes == 'July':
                mes = 'Julio'
            if mes == 'Aug' or mes == 'August':
                mes = 'Agosto'
            if mes == 'Sep' or mes == 'September':
                mes = 'Septiembre'
            if mes == 'Oct' or mes == 'October':
                mes = 'Octubre'
            if mes == 'Nov' or mes == 'November':
                mes = 'Noviembre'
            if mes == 'Dec' or mes == 'December':
                mes = 'Diciembre'

            if dia == False:
                dia = ''
            if ano == False:
                ano = ''

        discount_bs = total_line_c - amount_total_c
        discount_bs = '{:,.2f}'.format(discount_bs)

        self.localcontext.update({
            'nit': nit,
            'date_invoice': date,
            'amount_total_c': amount_total_c,
            'amount_total': amount_total,
            'literal': literal,
            'centavos': centavos,
            'nombre_compania': nombre_compania,
            'direccion_compania1': direccion_compania1,
            'direccion_compania2': direccion_compania2,
            'telefono_compania': telefono_compania,
            'ciudad_compania': ciudad_compania,
            'pais_compania': pais_compania,
            'nombre_tienda': nombre_tienda,
            'nombre_sucursal': nombre_sucursal,
            'direccion_compania12': direccion_compania12,
            'telefono_compania2': telefono_compania2,
            'actividad': actividad,
            'leyenda': leyenda,
            'total_line_c': total_line_c,
            'total_line_3': total_line,
            'discount_line': discount_line,
            'logo': logo,
            # 'total_filas':total_filas,
            'discount_bs': discount_bs,
            'numero_filas': n,
            'mes': mes,
            'dia': dia,
            'ano': ano,
        })


webkit_report.WebKitParser('report.invoice.pretensa.webkit',
                           'account.invoice',
                           'addons/poi_x_pretensa/report/print_invoice_pret.mako',
                           parser=account_invoice_pret)

webkit_report.WebKitParser('report.invoice.pretensacopia.webkit',
                           'account.invoice',
                           'addons/poi_x_pretensa/report/print_invoice_pret_copia.mako',
                           parser=account_invoice_pret)


class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def invoice_print_pret(self, cr, uid, ids, context=None):
        datas = {}

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'invoice.pretensa.webkit',
            'datas': datas,
        }


account_invoice()
