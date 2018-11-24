##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-2014 CodUP (<http://codup.com>).
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

from odoo import models, fields, api, modules, _
from odoo import tools

import time

class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'
    account_aitb_asset_id = fields.Many2one('account.account', string='Cuenta AITB Perdida', required=True,
                                       domain=[('internal_type', '=', 'other'), ('deprecated', '=', False)])
    account_aitb_asset_util_id = fields.Many2one('account.account', string='Cuenta AITB Utilidad', required=True,
                                            domain=[('internal_type', '=', 'other'), ('deprecated', '=', False)])

class account_asset_location(models.Model):
    _name = 'account.asset.location'

    name = fields.Char(string='Nombre')
    parent_id = fields.Many2one('account.asset.location', 'Ubicacion padre')
    usage = fields.Selection([('view', 'Vista'), ('normal', 'Ubicacion')])


class account_asset_asset(models.Model):
    _inherit = 'account.asset.asset'

    def _get_default_image(self):
        image_path = modules.get_module_resource('poi_bol_asset', 'static/src/img', 'asset_placeholder.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

    # @api.multi
    # @api.depends('account_move_ids')
    # def _hist_count(self):
    #     for asset in self:
    #         asset.entry_count = self.env['account.asset.history'].search_count([('asset_id', '=', asset.id)])

    #@api.multi
    #def _amount_residual(self):
    #    for asset in self:
    #        asset.value_residual = 10.0

    # Intervenir el valor residual ya no se usara el nativo
    # se aplicara el que maneja UFV
    @api.one
    @api.depends('value', 'salvage_value', 'depreciation_ufv_ids.amount_dep_per')
    def _amount_residual(self):
        total_amount = 0.0
        inc_act = 0.0
        dep_per = 0.0
        dep_act = 0.0
        for line in self.depreciation_ufv_ids:
            inc_act += line.amount_inc_act
            dep_per += line.amount_dep_per
            dep_act += line.amount_dep_act
        self.value_residual = self.value + inc_act - dep_per - dep_act

    @api.one
    @api.depends('value')
    def _total_restante(self):
        self.n_depre_restante = self.method_number - self.n_depre_actual - len(self.depreciation_ufv_ids.ids) + 1

    #hist_count = fields.Integer(compute='_hist_count', string='# Asset History')
    serial = fields.Char('Nr. Serie', size=64, copy=False,
                         help="Número de serie provisto por el manufacturador como identificación Única del producto.")
    account_analytic_id = fields.Many2one('account.analytic.account', 'Cuenta analítica',
                                          help="Cuenta analítica utilizada para la contabilización de los gastos asociados.")
    assign_id = fields.Many2one('res.partner', 'Asigando a', track_visibility='onchange',
                                help="Persona contacto asignada")
    location_id = fields.Many2one('account.asset.location', 'Ubicado en', track_visibility='onchange',
                                  help="Lugar físico de Ubicación", domain=[('usage', '!=', 'view')])
    image = fields.Binary("Foto", attachment=True,
                          help="This field holds the image used as photo for the event or presents, limited to 1024x1024px.")  # , default=_get_default_image  #carga demasiado la DB

    n_depre_actual = fields.Integer(string='# Depreciaciones realizadas', default = 0)
    n_depre_restante = fields.Integer(string='# Restantes', compute='_total_restante', method=True)
    depreciation_ufv_ids = fields.One2many('account.asset.value', 'asset_id', string='Lineas depreciadas',
                                            readonly=True,
                                            states={'draft': [('readonly', False)], 'open': [('readonly', False)]})

    def _log_history(self, args):
        if 'assign_id' in args or 'location_id' in args:
            assign_id = 'assign_id' in args and args['assign_id'] or False
            location_id = 'location_id' in args and args['location_id'] or False

            self.env['account.asset.history'].create({
                'asset_id': self.id,
                'assign_id': assign_id,
                'location_id': location_id,
                'user_id': self._uid,
            })

    @api.model
    def create(self, args):

        asset_id = super(account_asset_asset, self).create(args)

        self._log_history(args)

        return asset_id

    @api.multi
    def write(self, args):
        super(account_asset_asset, self).write(args)
        self._log_history(args)
        return True

    @api.multi
    def see_log(self):
        form_view = False
        tree_view = self.env.ref('poi_bol_asset.view_asset_history_tree')
        sear_view = self.env.ref('poi_bol_asset.view_asset_history_search')
        return {
            'name': "Historial: %s" % (self.name),
            'domain': [('asset_id', '=', self.id)],
            'res_model': 'account.asset.history',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(tree_view and tree_view.id or False, 'tree'),
                      (sear_view and sear_view.id or False, 'search')],
            'view_mode': 'tree',
            'view_type': 'form',
            'limit': 60,
            'context': "{'search_default_asset_id': %s, 'asset_id': %s}" % (self.id, self.id),
            'target': 'new',
        }

    @api.multi
    def view_depreciation(self):
        compose_form = self.env.ref('poi_bol_asset.view_asset_value_tree', False)
        domain = "[('asset_id', '=', %s)]" % (self.id)
        return {
            'name': _('Depreciacion de Activos'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.value',
            'views': [(compose_form.id, 'tree')],
            'view_id': compose_form.id,
            'domain': domain,
        }


class account_asset_history(models.Model):
    _name = 'account.asset.history'
    _description = 'Kardex Activo fijo'

    asset_id = fields.Many2one('account.asset.asset', 'Activo')
    assign_id = fields.Many2one('res.partner', 'Assigned to')
    location_id = fields.Many2one('account.asset.location', 'Ubicado en', help="Lugar físico de Ubicación")
    date = fields.Date('Fecha', default=fields.Date.today)
    note = fields.Text('Notas')

    _order = 'date desc'


class account_asset_value_header(models.Model):
    _name = 'account.asset.value.header'
    _description = 'Grupo kardex valorado Activo fijo'

    date_trans = fields.Date('Fecha', default=fields.Date.today)
    note = fields.Text('Notas')
    value_ids = fields.One2many('account.asset.value', 'head_id', string=u'Líneas de valor')

    _order = 'date_trans desc'


class account_asset_value(models.Model):
    _name = 'account.asset.value'
    _description = 'Kardex valorado Activo fijo'

    head_id = fields.Many2one('account.asset.value.header', 'Transacción')
    asset_id = fields.Many2one('account.asset.asset', 'Activo')
    value_type = fields.Selection(
        [('ACTI', u'Activación'), ('DEPR', 'Depreciacion periodo'), ('INCR', 'Incremento'), ('REVA', u'Revalorización'),
         ('BAJA', u'Baja')], string='Tipo')
    date_trans = fields.Date('Fecha', default=fields.Date.today)
    date_accounting = fields.Date('Fecha Asiento')
    note = fields.Text('Notas')
    move_id = fields.Many2one('account.move', string=u'Asiento de depreciación')
    time_delta = fields.Integer('Ajuste tiempo de vida',
                                help=u'Valor de actualizacion del Activo. Suma/resta a su tiempo de vida.')
    amount_inc_act = fields.Float(string=u'Actualización valor',
                                  help=u'Valor de actualización del Activo. Suma a su valor neto.')
    amount_dep_per = fields.Float(string=u'Depreciación valor',
                                  help=u'Valor de depreciación del Activo. Resta a su valor neto.')
    amount_dep_act = fields.Float(string=u'Actualización Depreciación acumulada',
                                  help=u'Valor de depreciación acumulada actualizada. Resta a su valor neto.')
    _order = 'date_trans desc'


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    def asset_create(self):
        # SuperCopyCheck. Override de la creación del Activo para la respectiva asignación de cuenta analítica
        if self.asset_category_id:
            vals = {
                'name': self.name,
                'code': self.invoice_id.number or False,
                'category_id': self.asset_category_id.id,
                'value': self.price_subtotal_signed,
                'partner_id': self.invoice_id.partner_id.id,
                'company_id': self.invoice_id.company_id.id,
                'currency_id': self.invoice_id.company_currency_id.id,
                'date': self.asset_start_date or self.invoice_id.date_invoice,
                'invoice_id': self.invoice_id.id,
                'account_analytic_id': self.account_analytic_id.id or self.asset_category_id.account_analytic_id.id,  # Asigna la cuenta analítica del gasto
            }
            changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
            vals.update(changed_vals['value'])
            asset = self.env['account.asset.asset'].create(vals)
            if self.asset_category_id.open_asset:
                asset.validate()
        return True
