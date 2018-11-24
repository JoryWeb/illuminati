##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import logging
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


def _convert_nn(val):
    """convert a value < 100 to English.
    """
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                if val > 20 and val < 30:
                    return "Veinti" + to_19[val % 10]
                else:
                    return dcap + ' Y ' + to_19[val % 10]
            return dcap


def _convert_nnn(val):
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
        word = word + _convert_nn(mod)
    return word


def english_number(val):
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
        return _convert_nnn(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            if l == 1:
                ret = 'Un' + ' ' + denom[didx]
            else:
                ret = _convert_nnn(l) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ' ' + english_number(r)
            return ret


def amount_to_text(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = english_number(int(list[0])).upper()
    end_word = english_number(int(list[1])).upper()
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and '' or ''
    prefix_cents = ''
    if not cents_number:
        cents_number = 0
    if cents_number >= 0 and cents_number < 10:
        prefix_cents = '0'
    final_result = start_word + ' ' + prefix_cents + str(cents_number) + '/100 BOLIVIANOS'
    return final_result


def amount_to_text_invoice(number, currency):
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = english_number(int(list[0])).upper()
    end_word = english_number(int(list[1])).upper()
    cents_number = int(list[1])
    prefix_cents = ''
    if not cents_number:
        cents_number = 0
    if cents_number >= 0 and cents_number < 10:
        prefix_cents = '0'
    final_result = start_word + ' ' + prefix_cents + str(cents_number) + '/100 BOLIVIANOS'
    return final_result


# -------------------------------------------------------------
# Generic functions
# -------------------------------------------------------------

_translate_funcs = {'en': amount_to_text}


# TODO: we should use the country AND language (ex: septante VS soixante dix)
# TODO: we should use en by default, but the translation func is yet to be implemented
def amount_to_text(nbr, lang='en', currency='euro'):
    """ Converts an integer to its textual representation, using the language set in the context if any.

        Example::

            1654: thousands six cent cinquante-quatre.
    """
    import openerp.loglevels as loglevels
    #    if nbr > 10000000:
    #        _logger.warning(_("Number too large '%d', can not translate it"))
    #        return str(nbr)

    if not _translate_funcs.has_key(lang):
        _logger.warning(_("no translation function found for lang: '%s'"), lang)
        # TODO: (default should be en) same as above
        lang = 'en'
    return _translate_funcs[lang](abs(nbr), currency)


if __name__ == '__main__':
    from sys import argv

    lang = 'nl'
    if len(argv) < 2:
        for i in range(1, 200):
            print(i, ">>", amount_to_text(i, lang))
        for i in range(200, 999999, 139):
            print(i, ">>", amount_to_text(i, lang))
    else:
        print(amount_to_text(int(argv[1]), lang))

UNIDADES = (
    '',
    'UN ',
    'DOS ',
    'TRES ',
    'CUATRO ',
    'CINCO ',
    'SEIS ',
    'SIETE ',
    'OCHO ',
    'NUEVE ',
    'DIEZ ',
    'ONCE ',
    'DOCE ',
    'TRECE ',
    'CATORCE ',
    'QUINCE ',
    'DIECISEIS ',
    'DIECISIETE ',
    'DIECIOCHO ',
    'DIECINUEVE ',
    'VEINTE '
)

DECENAS = (
    'VENTI',
    'TREINTA ',
    'CUARENTA ',
    'CINCUENTA ',
    'SESENTA ',
    'SETENTA ',
    'OCHENTA ',
    'NOVENTA ',
    'CIEN '
)

CENTENAS = (
    'CIENTO ',
    'DOSCIENTOS ',
    'TRESCIENTOS ',
    'CUATROCIENTOS ',
    'QUINIENTOS ',
    'SEISCIENTOS ',
    'SETECIENTOS ',
    'OCHOCIENTOS ',
    'NOVECIENTOS '
)

MONEDAS = (
    {'country': u'Bolivia', 'currency': 'BOB', 'singular': u'BOLIVIANO', 'plural': u'BOLIVIANOS', 'symbol': u'Bs.'},
    {'country': u'USA', 'currency': 'USD', 'singular': u'DOLAR', 'plural': u'D�~SLARES', 'symbol': u'$us.'},
)


def to_word(amount, moneda='BOB'):
    number = int(amount)
    mi_moneda = moneda
    if mi_moneda != None:
        try:
            moneda = next(filter(lambda x: x['currency'] == mi_moneda, MONEDAS))
            if number < 2:
                moneda = moneda['singular']
            else:
                moneda = moneda['plural']
        except:
            return "Tipo de moneda inválida"
    else:
        moneda = ""
    """Converts a number into string representation"""
    converted = ''

    if not (0 < number < 999999999):
        moneda = next(filter(lambda x: x['currency'] == mi_moneda, MONEDAS))
        if number == 0:
            return 'Cero 00/100' + ' ' + moneda['plural']
        return 'No es posible convertir el numero a letras'

    number_str = str(number).zfill(9)
    millones = number_str[:3]
    miles = number_str[3:6]
    cientos = number_str[6:]

    if (millones):
        if (millones == '001'):
            converted += 'UN MILLON '
        elif (int(millones) > 0):
            converted += '%sMILLONES ' % __convert_group(millones)

    if (miles):
        if (miles == '001'):
            converted += 'MIL '
        elif (int(miles) > 0):
            converted += '%sMIL ' % __convert_group(miles)

    if (cientos):
        if (cientos == '001'):
            converted += 'UN '
        elif (int(cientos) > 0):
            converted += '%s ' % __convert_group(cientos)

    decimal = _total_decimal2(amount)

    return converted.title() + ' ' + decimal + ' ' + moneda


def __convert_group(n):
    """Turn each group of numbers into letters"""
    output = ''

    if (n == '100'):
        output = "CIEN "
    elif (n[0] != '0'):
        output = CENTENAS[int(n[0]) - 1]

    k = int(n[1:])
    if (k <= 20):
        output += UNIDADES[k]
    else:
        if ((k > 30) & (n[2] != '0')):
            output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
        else:
            output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

    return output


def _total_decimal2(amount_total):
    val = str(amount_total).split(".")
    if val[1] and val[1] != '0':
        if int(val[1]) < 10:
            if len(val[1]) > 1:
                val = val[1] + '/100'
            else:
                val = str(int(val[1])) + '0/100'

        else:
            val = str(int(val[1])) + '/100'
    else:
        val = '00/100'

    return val
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
