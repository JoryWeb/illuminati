##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
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

import re
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo import SUPERUSER_ID

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging


class CCDosif(models.Model):
    _inherit = 'poi_bol_base.cc_dosif'

    @api.one
    def _get_last_pos_cc_nro(self):
        order_obj = self.env['pos.order']
        orders = order_obj.sudo().search([('cc_dos', '=', self.id)])

        if orders:
            cc_nros = [x.cc_nro_int for x in orders]
            self.last_pos_cc_nro = max(cc_nros)
        else:
            self.last_pos_cc_nro = self.rango_ini - 1

    last_pos_cc_nro = fields.Integer("Last CC Nro", compute=_get_last_pos_cc_nro, store=False)

    @api.one
    @api.depends('warehouse_id.partner_id')
    def _get_dosif_invoice_data(self):
        self.street = self.warehouse_id.partner_id.street
        self.street2 = self.warehouse_id.partner_id.street2
        self.city = self.warehouse_id.partner_id.city
        self.country_id = self.warehouse_id.partner_id.country_id and self.warehouse_id.partner_id.country_id.id or False
        self.phone = self.warehouse_id.partner_id.phone
        self.branch = self.warehouse_id.branch

    street = fields.Char('Street', compute=_get_dosif_invoice_data)
    street2 = fields.Char('Street2', compute=_get_dosif_invoice_data)
    city = fields.Char('City', compute=_get_dosif_invoice_data)
    country_id = fields.Many2one('res.country', 'Country', compute=_get_dosif_invoice_data)
    phone = fields.Char("Phone", compute=_get_dosif_invoice_data)
    branch = fields.Char('Sucursal', compute=_get_dosif_invoice_data)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    dosif_id = fields.Many2one('poi_bol_base.cc_dosif', 'Dosificacion')


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _payment_fields(self, ui_paymentline):
        fields = super(PosOrder, self)._payment_fields(ui_paymentline)

        fields.update({
            'card_code': ui_paymentline.get('card_code'),
            'card_bank_owner': ui_paymentline.get('card_bank_owner'),
        })

        return fields

    @api.model
    def add_payment(self, data):
        statement_id = super(PosOrder, self).add_payment(data)
        statement_lines = self.env['account.bank.statement.line'].search([('statement_id', '=', statement_id),
                                                                          ('pos_statement_id', '=', self.id),
                                                                          ('journal_id', '=', data['journal']),
                                                                          ('amount', '=', data['amount'])])

        for line in statement_lines:
            if not line.card_code:
                line.card_code = data.get('card_code')
                line.card_bank_owner = data.get('card_bank_owner')
                break

        return statement_id


    def _on_refund_clone(self):
        res = super(PosOrder, self)._on_refund_clone()
        res['estado_fac'] = ''
        return res

    @api.cr_uid
    def _on_refund_order(self, cr, uid, order_id, clone_id):
        order_obj = self.browse(cr, uid, order_id)
        clone_obj = self.browse(cr, uid, clone_id)

        res = super(PosOrder, self)._on_refund_order(cr, uid, order_id, clone_id)

        if order_obj.amount_total > 0 and clone_obj.amount_total < 0:
            order_obj.write({'estado_fac': 'A'})
            clone_obj.write({'estado_fac': 'na'})

        elif order_obj.amount_total < 0 and clone_obj.amount_total > 0:
            order_obj.write({'estado_fac': 'na'})
            clone_obj.write({'estado_fac': 'V'})

        return res

    @api.cr_uid
    def _on_duplicate_order(self, cr, uid, order_id, clone_id):
        order_obj = self.browse(cr, uid, order_id)
        clone_obj = self.browse(cr, uid, clone_id)

        res = super(PosOrder, self)._on_duplicate_order(cr, uid, order_id, clone_id)

        if order_obj.estado_fac != 'A':
            order_obj.write({'estado_fac': 'A'})
        clone_obj.write({'estado_fac': 'V',
                         'cc_nro': None,
                         'cc_aut': None,
                         'cc_cod': None,
                         'qr_img': None
                         })

        return res

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)

        res['nit'] = ui_order.get('nit', '0')
        res['razon'] = ui_order.get('razon', _('No name'))

        self.env['bol.customer'].set_razon(res['nit'], res['razon'])

        res['cc_aut'] = ui_order.get('cc_aut')
        res['cc_nro'] = ui_order.get('cc_nro')
        res['cc_dos'] = ui_order.get('cc_dos')
        res['leyenda'] = ui_order.get('leyenda')
        # res['order_data'] = str(ui_order)
        res['cc_cod'] = ui_order.get('cc_cod')
        res['qr_img'] = ui_order.get('qr_img')

        res['date_fac'] = ui_order.get('date_fac')
        res['time_fac'] = ui_order.get('time_fac')

        # Change to currency
        # tot_val = ui_order.get('tot_val')

        # if tot_val:
        #    res['tot_val'] = tot_val
        # else:
        #    session_pool = self.pool.get('pos.session')
        #    currency_pool=self.pool.get('res.currency')
        #    session_id = ui_order.get('pos_session_id')
        #    if session_id:
        #        session_obj = session_pool.browse(cr, uid, session_id)
        #        currency_obj = session_obj.config_id.shop_id.pricelist_id.currency_id

        # if currency_obj.name != 'BOB':
        #    bob = currency_pool.search(cr, uid, [('name','=','BOB')])[0]
        #    tot_val = currency_pool.compute(cr, uid, currency_obj.id, bob, ui_order.get('amount_total'), context={})
        # else:
        #    tot_val = ui_order.get('amount_total')
        # res['tot_val'] = tot_val
        # else:
        #    raise osv.except_osv(u'Sesión Inválida', u'Revise la codificación')

        return res

    @api.one
    @api.depends('cc_nro')
    def _compute_cc_nro(self):
        self.cc_nro_int = int(self.cc_nro)

    @api.depends('session_id')
    def compute_default_dosif(self):
        dosif_users_pool = self.env['poi_bol_base.cc_dosif.users']
        dosif_users_ids = dosif_users_pool.search([('user_id', '=', self.env.uid), ('user_default', '=', True)])
        for dosif_users in dosif_users_ids:
            if dosif_users.dosif_id.activa:
                return dosif_users.dosif_id.id
        else:
            return False

    date_fac = fields.Char(
        "Date Invoice")  # These fields will store the REAL time of the invoice. Date order will not be affected
    time_fac = fields.Char("Time Invoice")

    nit = fields.Char(string='NIT/CI', size=10, help='NIT o CI del cliente')
    razon = fields.Char(string='Razon Social', size=64, help='Razon Social o Nombre para la factura')
    email = fields.Char(string='Email')
    cc_nro = fields.Char(string='Nro. Factura', help='Numero de Factura')
    cc_aut = fields.Char(string='Nro. Autorizacion', help='Numero de Autorizacion')
    cc_dos = fields.Many2one('poi_bol_base.cc_dosif', 'Serie Dosificacion', readonly=True,
                             help='Serie de dosificacion segun parametrizacion. Asocia Numero de autorizacion y Llave de dosificacion.',
                             default=compute_default_dosif)
    estado_fac = fields.Selection(
        [('V', u'Válida'), ('A', 'Anulada'), ('E', 'Extraviada'), ('N', 'No Utilizada'), ('na', 'No Aplica')],
        string='Estado SIN', default='V')
    cc_nro_int = fields.Integer(string='Nro. Factura (Num)', compute=_compute_cc_nro, store=True)

    ice = fields.Float(string='Importe ICE', digits=dp.get_precision('Account'))
    exento = fields.Float(string='Importe Exentos', digits=dp.get_precision('Account'))

    cc_cod = fields.Char(u'Código de control', size=14,
                         help=u"Código de representación única para el SIN. Generación automática para Ventas (versión 7). Introducción manual para Compras.")
    qr_img = fields.Binary(u'Código QR',
                           help=u"Código QR generado automáticamente en base a los datos específicos de la Factura.")
    leyenda = fields.Text('Leyenda', help='La leyenda impresa en el PdV')


    @api.multi
    @api.depends('lines.price_subtotal_incl', 'lines.discount')
    def _amount_all_bs(self):
        for order in self:
            currency = order.pricelist_id.currency_id
            order.tax_bs = currency.round(
                sum(self._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
            amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
            order.total_bs = order.tax_bs + amount_untaxed

    total_bs = fields.Float(string='Total (Bs.)', compute=_amount_all_bs, store=True)
    tax_bs = fields.Float(string='Tax (Bs.)', compute=_amount_all_bs, store=True)



    @api.one
    @api.constrains('cc_aut', 'cc_nro', 'estado_fac')
    def _check_duplicity_cc_nro(self):
        if self.estado_fac == 'V' and self.cc_aut and self.cc_nro:
            orders_found = self.search(
                [('cc_aut', '=', self.cc_aut), ('cc_nro', '=', self.cc_nro), ('estado_fac', 'in', ['V', 'A']),
                 ('id', '!=', self.id)])
            if orders_found:
                raise ValueError(_("Invoice Number must be UNIQUE for a valid order."))

    @api.multi
    def pop_qr(self):
        if not isinstance(self.ids, (int)):
            res_id = self.ids[0]
        else:
            res_id = self.ids

        dummy, view_res = self.env['ir.model.data'].get_object_reference('poi_pos_bol', 'pos_order_qr_view')
        return {
            'name': 'Código QR',
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'pos.order',
            'type': 'ir.actions.act_window',
            'view_id': view_res,
            'res_id': res_id,
            'context': self.env.context,
            'target': 'new',
        }
