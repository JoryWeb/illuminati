#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
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

import os.path
from io import BytesIO
import base64

from Crypto.Cipher import ARC4
import binascii
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

try:
    import qrcode as qrcode
except ImportError:
    _logger.debug('addon poi_bol_cc no puede importar libreria qrcode`.')


def __init__():
    return 0


def qr_gen(nro, nit, tot, fec, aut, cc, nit_co, fecha, ice, vng, exe, desc):
    # Genera la imagen del código QR lista para guardar en un campo binario de OpenERP
    fec_str = datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y')
    tot_str = "%.2f" % round(tot or 0, 2)
    base_str = "%.2f" % round((tot - exe or 0.0 - ice or 0.0) or 0, 2)
    ice_str = ice and "%.2f" % round(ice or 0, 2) or False
    vng_str = vng and "%.2f" % round(vng or 0, 2) or False
    exe_str = exe and "%.2f" % round(exe or 0, 2) or False
    desc_str = desc and "%.2f" % round(desc or 0, 2) or False
    qr_str = "%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % (
    nit_co or '0', nro and str(nro) or '0', aut and str(aut) or '0', fec_str, tot_str, base_str, cc or '0', nit or '0',
    ice_str or '0', vng_str or '0', exe_str or '0', desc_str or '0',)

    img = qrcode.make(qr_str)
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    qr_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return qr_data


def cc_gen(nro, nit, tot, fec, aut, key):
    """Genera el Codigo de control (version 7) de acuerdo a

    la especificacion dada en http://www.impuestos.gov.bo/facturacion/CodigoControlV7.pdf"""
    if not key:
        raise Exception('CC', 'Llave de dosificación nula no valida.')
        return -1

    # Prep & Validate
    tot = Decimal(tot).quantize(0,
                                ROUND_HALF_UP)  # Python 3 redondea los .5 hacia abajo por defecto. Debe hacerlo hacia arriba
    key = key.strip()

    if not nit and nit != 0:
        raise Exception('CC', 'No se ha especificado un NIT.')
        return -1
    else:
        if len(str(nit)) > 12:
            raise Exception('CC', 'El NIT contiene mas de 12 digitos')
            return -1

    try:
        # Paso 1
        vh_nro = generateVerhoeff(generateVerhoeff(nro))
        vh_nit = generateVerhoeff(generateVerhoeff(nit))
        vh_tot = generateVerhoeff(generateVerhoeff(tot))
        vh_fec = generateVerhoeff(generateVerhoeff(fec))
        vh_aut = generateVerhoeff(generateVerhoeff(aut))
        sum = int(vh_nro) + int(vh_nit) + int(vh_tot) + int(vh_fec)

        lst_vh1 = []
        vh_5 = ""
        vh_sum = sum
        for i in range(5):
            vh_num = calcsum(vh_sum)
            vh_5 = "%s%s" % (vh_5, vh_num)
            vh_sum = "%s%s" % (vh_sum, vh_num)
            # Paso 2
            lst_vh1.append(vh_num + 1)

        # Paso 2.1
        lDatLla = []
        lDatVhf = [str(aut), str(vh_nro), str(vh_nit), str(vh_fec), str(vh_tot)]
        index = 0
        sub_key = ''
        full_key = ''
        for i in range(5):
            sub_key = str(key)[index:lst_vh1[i] + index]
            index = index + lst_vh1[i]
            lDatLla.append(lDatVhf[i] + sub_key)
            full_key = full_key + lDatLla[i]

        # Paso 3
        llave_cifrado = key + vh_5
        arc4 = ARC4.new(llave_cifrado)
        crypt_arc = arc4.encrypt(full_key)
        string_arc4 = binascii.hexlify(crypt_arc).upper()
        string_arc42 = binascii.b2a_hex(crypt_arc)

        # Paso 4
        lst_sa = []
        sa_tot = sum_ascii(string_arc4, 1, 1)
        lst_sa.append(sum_ascii(string_arc4, 1, 5))
        lst_sa.append(sum_ascii(string_arc4, 2, 5))
        lst_sa.append(sum_ascii(string_arc4, 3, 5))
        lst_sa.append(sum_ascii(string_arc4, 4, 5))
        lst_sa.append(sum_ascii(string_arc4, 5, 5))

        # Paso 5
        sum_base64 = 0
        dic_base64 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/'
        for i in range(5):
            sum_base64 = sum_base64 + int(sa_tot * lst_sa[i] / lst_vh1[i])
        str_base64 = base64_encode(sum_base64)

        # Paso 6
        i = 0
        cc = ''
        arc64 = ARC4.new(llave_cifrado)
        crypt_arc64 = arc64.encrypt(str_base64)
        cc_arc64 = binascii.hexlify(crypt_arc64).upper()
        cc_arc64 = cc_arc64.decode("utf-8")
        for i in range(len(cc_arc64)):
            if (i + 1) % 2 or i + 1 == len(cc_arc64):
                cc = cc + cc_arc64[i]
            else:
                cc = cc + cc_arc64[i] + '-'

        res = cc
        return res

    except Exception as e:
        if len(key) < 3:
            raise Exception('CC', 'Llave de dosificación no valida:' + key)
        else:
            raise Exception('CC', str(e))


# ----------- VERHOEFF --------------
verhoeff_table_d = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0))
verhoeff_table_p = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8))
verhoeff_table_inv = (0, 4, 3, 2, 1, 5, 6, 7, 8, 9)


def calcsum(number):
    """For a given number returns a Verhoeff checksum digit"""
    c = 0
    for i, item in enumerate(reversed(str(number))):
        c = verhoeff_table_d[c][verhoeff_table_p[(i + 1) % 8][int(item)]]
    return verhoeff_table_inv[c]


def checksum(number):
    """For a given number generates a Verhoeff digit and
    returns number + digit"""
    c = 0
    for i, item in enumerate(reversed(str(number))):
        c = verhoeff_table_d[c][verhoeff_table_p[i % 8][int(item)]]
    return c


def generateVerhoeff(number):
    """For a given number returns number + Verhoeff checksum digit"""
    return "%s%s" % (number, calcsum(number))


def validateVerhoeff(number):
    """Validate Verhoeff checksummed number (checksum is last digit)"""
    return checksum(number) == 0


# --------------- ALLEGED RC4 ------------------------
# DEPRECATED. Taken from: https://www.dlitz.net/software/pycrypto/api/current/Crypto.Cipher.ARC4-module.html

def rc4_crypt(data: str, key: bytes) -> str:
    """RC4 algorithm"""
    x = 0
    box = list(range(256))
    for i in range(256):
        x = (x + int(box[i]) + ord(key[i % len(key)])) % 256
        box[i], box[x] = box[x], box[i]
    x = y = 0
    out = []
    for char in data:
        x = (x + 1) % 256
        y = (y + box[x]) % 256
        box[x], box[y] = box[y], box[x]
        out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))

    return ''.join(out)


class CC_ARC4:
    def __init__(self, key=None):
        self.state = list(range(256))  # Initialize state array with values 0 .. 255
        self.x = self.y = 0  # Our indexes. x, y instead of i, j

        if key is not None:
            self.init(key)

    # KSA
    def init(self, key):
        for i in range(256):
            self.x = (ord(key[i % len(key)]) + self.state[i] + self.x) & 0xFF
            self.state[i], self.state[self.x] = self.state[self.x], self.state[i]
        self.x = 0

    # PRGA
    def crypt(self, input):
        output = [None] * len(input)
        for i in range(len(input)):
            self.x = (self.x + 1) & 0xFF
            self.y = (self.state[self.x] + self.y) & 0xFF
            self.state[self.x], self.state[self.y] = self.state[self.y], self.state[self.x]
            r = self.state[(self.state[self.x] + self.state[self.y]) & 0xFF]
            output[i] = chr(ord(input[i]) ^ r)
        return ''.join(output)


# ---------------- ASCII -----------------
def sum_ascii(str_sum, start, interval):
    sum_tot = 0
    index = start - 1
    while index < len(str_sum):
        char_i = str_sum[index:index + 1]
        sum_tot = sum_tot + ord(char_i)
        index = index + interval

    return sum_tot


# ---------------- BASE 64 ---------------
base64_dict = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/'


def base64_encode(number):
    word = ''
    coc = 1
    while coc > 0:
        coc = int(number / 64)
        rest = base64_mod64(number, 64)
        word = base64_dict[rest] + word
        number = coc

    return word


def base64_mod64(div_d, div_s):
    coc = int(div_d / div_s)
    result = div_d - (div_s * coc)
    return result


# ---------------- TESTER ----------------
if __name__ == '__main__':
    # Caso de prueba. Para testear el modulo independientemente, en base al ejemplo del documento
    # http://www.impuestos.gov.bo/facturacion/CodigoControlV7.pdf
    nit_x = 4189179011
    nro_x = 1503
    aut_x = 29040011007
    tot_x = 2500
    fec_x = 20070702
    key_x = '9rCB7Sv4X29d)5k7N%3ab89p-3(5[A'
    expected_res = '6A-DC-53-05-14'
    cc_x = cc_gen(nro_x, nit_x, tot_x, fec_x, aut_x, key_x)
    if expected_res != cc_x:
        print("Error en CC: " + cc_x)

    nit_x = 1026469026
    nro_x = 152
    aut_x = 79040011859
    tot_x = 135
    fec_x = 20070728
    key_x = 'A3Fs4s$)2cvD(eY667A5C4A2rsdf53kw9654E2B23s24df35F5'
    expected_res = 'FB-A6-E4-78'
    cc_x = cc_gen(nro_x, nit_x, tot_x, fec_x, aut_x, key_x)
    if expected_res != cc_x:
        print("Error en CC: " + cc_x)

    file_casos = 'test/5000CasosPruebaCCVer7.txt'
    if file_casos:
        ftests = open(os.path.join(os.path.dirname(__file__),
                                   file_casos), 'r')
        ftests.readline()  # Discard first line

        for line in ftests:
            data = line.strip().strip('|').split('|')
            (aut_l, nro_l, nit_l, fec_l, tot_l, key_l) = data[:6]
            real_cc = data[-1]

            # Fix decimal separator
            tot_l = float(tot_l.replace(',', '.'))
            fec_l = int(fec_l.replace('/', ''))
            gen_cc = cc_gen(nro_l, nit_l, tot_l, fec_l, aut_l, key_l)
            if gen_cc != real_cc:
                print("Error en CC: " + cc_x)
            assert gen_cc == real_cc, 'The Control Code is incorrect, %s line' % ftests.tell()

    print("Test finalizado")
