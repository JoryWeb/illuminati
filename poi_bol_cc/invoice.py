#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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

from odoo import models, fields, api
from odoo.exceptions import UserError
# from itertools import ifilter

# import .cc
from .cc import cc_gen, qr_gen

UNIDADES = (
    '',
    'UNO ',
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
    {'country': u'Bolivia', 'currency': 'BO', 'singular': u'', 'plural': u'', 'symbol': u'Bs.'},
)


class cc_dosif_sector(models.Model):
    _name = 'poi_bol_base.cc_dosif.sector'
    _description = 'Sectores'

    name = fields.Char('Sector', required=True)


class cc_dosif_leyenda(models.Model):
    # """Leyendas para impresión en Facturas"""
    _name = 'poi_bol_base.cc_dosif.leyenda'
    _description = 'Leyenda Facturas'

    name = fields.Text('Leyenda', required=True, help=u"Leyenda a imprimirse en factura.")
    sector_id = fields.Many2one('poi_bol_base.cc_dosif.sector', string="Sector")


class cc_dosif(models.Model):
    _inherit = 'poi_bol_base.cc_dosif'

    llave = fields.Char('Llave Dosificación CC', size=250,
                        help="Llave de dosificación provista por el SIN para la generación del Código de control.")
    leyenda_id = fields.Many2one('poi_bol_base.cc_dosif.leyenda', string="Leyenda", required=True)
    qr_code = fields.Binary(u'Código QR', filters='*.png,*.gif,*.bmp,*.jpg',
                            help=u"Archivo imagen del código QR provisto por Impuestos Nacionales para la dosificación")


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    cc_cod = fields.Char(u'Código de control', size=14, copy=False,
                         help=u"Código de representación única para el SIN. Generación automática para Ventas (versión 7). Introducción manual para Compras.")
    qr_img = fields.Binary(u'Código QR', copy=False,
                           help=u"Código QR generado automáticamente en base a los datos específicos de la Factura.",
                           states={'open': [('readonly', True)], 'paid': [('readonly', True)]})

    @api.multi
    def invoice_validate(self):

        for obj_inv in self:
            if obj_inv.type != 'out_invoice':
                continue
            if not obj_inv.con_imp:
                continue
            if not obj_inv.cc_dos or not obj_inv.cc_dos.llave:
                continue

                # Se trata de hacer todas las validaciones antes del validate para evitar problemas de numeración de facturas
                if not obj_inv.cc_dos.activa:
                    raise UserError(u'[CC] Serie de dosificación no activa.')
                if not obj_inv.company_id.nit:
                    raise UserError(u'[CC] El NIT de la Compañía debe estar especificado para generar código QR.')
                if not obj_inv.nit and obj_inv.nit != 0:
                    raise UserError('[CC] No se ha especificado un NIT.')
                if len(str(obj_inv.nit)) > 12:
                    raise UserError('[CC] El NIT contiene mas de 12 digitos.')
                if not obj_inv.cc_dos.llave:
                    raise UserError('[CC] Llave de dosificación nula no valida.')

            ret = super(AccountInvoice, self).invoice_validate()

            self.action_cc()

            return ret

    @api.multi
    def action_cc(self):

        for obj_inv in self:

            # Sólo para facturas de venta con IVA y con una dosificación con llave
            if obj_inv.type != 'out_invoice':
                return True
            if not obj_inv.con_imp:
                return True
            if not obj_inv.cc_dos or not obj_inv.cc_dos.llave:
                return True

            # Generar Código de Control
            nit_val = obj_inv.nit
            nro_val = obj_inv.cc_nro
            aut_val = obj_inv.cc_dos.nro_orden
            dos_val = obj_inv.cc_dos.llave
            fec_val = int(obj_inv.date_invoice.replace('-', ''))
            if obj_inv.currency_id.name == 'BOB':
                tot_val = obj_inv.amount_total
            else:
                cur_bob = self.env['res.currency'].search([('name', '=', 'BOB')], limit=1)
                if cur_bob:
                    cur_bob = cur_bob[0]
                    date_rate = obj_inv.date_invoice and obj_inv.date_invoice[0:10] or False
                    tot_val = obj_inv.currency_id.with_context(date=date_rate).compute(obj_inv.amount_total, cur_bob)
                else:
                    raise UserError(u'[CC] No se pudo calcular el monto de factura en moneda BOB.')

            if not nro_val:
                self.env.cr.execute("SELECT cc_nro FROM account_invoice WHERE id = %s", (obj_inv.id,))
                rs = self.env.cr.fetchone()
                nro_val = rs and rs[0] or False
                if not nro_val:
                    raise UserError(u'[CC] No se puede generar código sin Nro de factura.')
            try:
                cc_val = cc_gen(nro_val, nit_val, tot_val, fec_val, aut_val, dos_val)

                # Generar código QR
                ice = False  # ToDo. Cómo implementar el impuesto ICE, vng y exe!!
                vng = False  # Ventas No Gravadas
                exe = False  # Exento de credito fiscal
                sum_desc = obj_inv.sum_desc or False
                nit_company = obj_inv.company_id.nit
                razon_company = obj_inv.company_id.razon
                fecha_val = obj_inv.date_invoice[0:10]
                fecha_fin_val = obj_inv.cc_dos.fecha_fin[0:10]
                razon_cliente = obj_inv.razon or (obj_inv.partner_id and obj_inv.partner_id.name) or ''

                qr_val = qr_gen(nro_val, nit_val, tot_val, fec_val, aut_val, cc_val, nit_company, fecha_val, ice, vng,
                                exe, sum_desc)

            except Exception as e:
                raise UserError(str(e))

            # Actualizar datos en Factura
            ret = self.write({'cc_cod': cc_val, 'qr_img': qr_val})

            return ret

    @api.multi
    def pop_qr(self):

        if not isinstance(self._ids, (int)):
            res_id = self._ids[0]
        else:
            res_id = self._ids

        dummy, view_res = self.env['ir.model.data'].get_object_reference('poi_bol_cc', 'account_invoice_qr_view')
        return {
            'name': 'Código QR',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'view_id': view_res,
            'res_id': res_id,
            'context': self.env.context,
            'target': 'new',
        }

    def to_word(self, amount):
        number = int(amount)
        mi_moneda = 'BO'
        if mi_moneda != None:
            try:
                moneda = filter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
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
            return 'No es posible convertir el numero a letras'

        number_str = str(number).zfill(9)
        millones = number_str[:3]
        miles = number_str[3:6]
        cientos = number_str[6:]

        if (millones):
            if (millones == '001'):
                converted += 'UN MILLON '
            elif (int(millones) > 0):
                converted += '%sMILLONES ' % self.__convert_group(millones)

            if (miles):
                if (miles == '001'):
                    converted += 'MIL '
                elif (int(miles) > 0):
                    converted += '%sMIL ' % self.__convert_group(miles)

            if (cientos):
                if (cientos == '001'):
                    converted += 'UN '
                elif (int(cientos) > 0):
                    converted += '%s ' % self.__convert_group(cientos)

            converted += moneda
            decimal = self._total_decimal2(amount)

            return converted.title() + ' ' + decimal

        def __convert_group(self, n):
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

        def _total_decimal2(self, amount_total):

            val = str(amount_total).split(".")
            if val[1] and val[1] != '0':
                if int(val[1]) < 10:
                    val = val[1] + '0/100 Bolivianos'
                else:
                    val = val[1] + '/100 Bolivianos'
            else:
                val = '00/100 Bolivianos'

            return val


class CcCertif(models.Model):
    _name = 'poi_bol_cc.cc_certif'

    cc_nit = fields.Char('NIT', help="NIT o CI del cliente.", size=16, digits=(16, 0))
    cc_nro = fields.Integer('Nro. Factura', help=u"Número de factura.")
    cc_aut = fields.Char(u'Nro. Autorización', help=u"Número de autorización.", size=15, digits=(15, 0))
    cc_dos = fields.Char(u'Llave de dosificación', size=254, help=u"Llave de dosificación asignada por el SIN.")
    cc_fec = fields.Date('Fecha factura')
    cc_tot = fields.Float('Monto factura')
    cc_cod = fields.Char(string=u'Código de control', size=14, help=u"Código de representación única para el SIN.")

    @api.one
    def action_cc(self):
        obj_inv = self
        nit_val = obj_inv.cc_nit or 0
        nro_val = obj_inv.cc_nro
        aut_val = obj_inv.cc_aut
        dos_val = obj_inv.cc_dos
        tot_val = obj_inv.cc_tot
        fec_val = int(obj_inv.cc_fec.replace('-', ''))

        cc_val = cc_gen(nro_val, nit_val, tot_val, fec_val, aut_val, dos_val)
        ret = self.write({'cc_cod': cc_val})

        return ret
