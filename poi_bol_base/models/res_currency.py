##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


class ResCurrency(models.Model):
    _inherit = "res.currency"

    # Subir decimales a 15
    rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=(12, 15),
                        help='The rate of the currency to the currency of rate 1.')
    name_on_report = fields.Char(string='Nombre en Reporte')

    @api.v8
    def name_get(self):
        currencies = []
        for currency in self:
            currencies.append((currency.id, currency.symbol))
        return currencies

    # @api.v8
    # @api.multi
    # def read(self, fields=None, load='_classic_read'):
    #
    #     res = super(ResCurrency, self).read(fields=fields, load=load)
    #
    #     if self.env.context.get('force_name'):
    #         return res
    #     if load:
    #         if load == '_classic_write':
    #             for currency in res:
    #                 if 'name' in fields:
    #                     if currency['name'] == 'BOB':
    #                         currency['name'] = currency['symbol']
    #     return res


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    rate = fields.Float('Rate', digits=(12, 15), help='The rate of the currency to the currency of rate 1')
