#!/usr/bin/env python
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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
from openerp.exceptions import except_orm, Warning, RedirectWarning

import time


# ToDo. Ignorar asientos de Ajuste previos!!

class actualiza_aitb(models.TransientModel):
    _name = "poi_bol_base.actualiza_aitb"
    _description = "Actualización de valor"

    date_from = fields.Date('Desde Fecha', required=True)
    date_to = fields.Date('Hasta Fecha', required=True)
    case = fields.Selection([('ufv', 'UFV'), ('usd', 'USD')], 'Caso', default='ufv')
    journal_id = fields.Many2one('account.journal', 'Diario', required=True,
                                 help=u"Especifica el Diario bajo el cual se generará el nuevo Asiento.")
    currency_id = fields.Many2one('res.currency', 'Según Moneda',
                                  help=u"Especifica la moneda contra la cual se hara la actualización de valor según diferencias de tipo de cambio entre las fechas provistas.")
    state = fields.Selection([('init', 'init'), ('warning', 'warning'), ('done', 'done')], 'state', default='init')

    @api.multi
    def action_generate(self):

        for data in self:
            journal_id = data['journal_id'].id
            state = data['state']
            case = data['case']
            from_date = data['date_from']
            to_date = data['date_to']

            # Asignar particularidades de los dos casos manejados por el Wizard
            case_dsc = case.upper()
            if case == 'ufv':
                currency_id = self.env['ir.model.data'].xmlid_to_res_id('poi_bol_base.res_currency_ufv',
                                                                        raise_if_not_found=True)

                ufv_ini = 0.0
                ufv_fin = 0.0
                date_str_init_ufv = from_date
                date_str_end_ufv = to_date
                counter_account = 'account_aju_ufv_id'
                self._cr.execute("""
                                            SELECT rate FROM res_currency_rate WHERE currency_id = %s and to_char(name,'YYYY-MM-dd') = %s
                                           """, (currency_id, date_str_init_ufv,))
                res = self._cr.fetchall()
                for line in res:
                    ufv_ini = line[0]

                self._cr.execute("""
                                            SELECT rate FROM res_currency_rate WHERE currency_id = %s and to_char(name,'YYYY-MM-dd') = %s
                                           """, (currency_id, date_str_end_ufv,))
                res = self._cr.fetchall()
                for line in res:
                    ufv_fin = line[0]
            elif case == 'usd':
                currency_id = self.env['ir.model.data'].xmlid_to_res_id('base.USD', raise_if_not_found=True)
                counter_account = 'account_aju_usd_id'
            else:
                raise except_orm(_(u'Error de Usuario'), _('Caso de uso de ajusto desconocido!'))

            # Obtener tipo de cambio a la fecha de hoy
            company_currency = data['journal_id'].company_id.currency_id
            currency = self.env['res.currency'].browse(currency_id)
            currency = currency.with_context(date=to_date or fields.Date.context_today(self))
            # si la moneda no es Dolar
            if ufv_fin != 0.0:
                rate_now = ufv_fin
            else:
                rate_now = company_currency.compute(1, currency, round=False)
                if not rate_now or rate_now == 0:
                    raise except_orm(_(u'Error de Configuración'),
                                     _('No se ha configurado el tipo de cambio para la Moneda provista!'))

            if int(from_date.replace('-', '')) > int(to_date.replace('-', '')):
                raise except_orm(_('Error !'), _('La fecha Desde es mayor que la fecha Hasta!!'))

            cr_query = """select grp_aml.account_id, aa.account_aju_ufv_id, grp_aml.saldo as saldo, tc.rate as rate_init, (grp_aml.saldo * tc.rate) as saldo_ufv
                            from (SELECT
                                    aml.account_id,
                                    aml.date,
                                    SUM(aml.debit - aml.credit)           AS saldo
                                  FROM account_move_line aml
                                    inner join account_move am on am.id=aml.move_id
                                  WHERE am.state = 'posted' and am.caso_aju = 'n'
                                    and aml.date >= %s and aml.date <= %s
                                  group by aml.account_id, aml.date
                                ) as grp_aml
                                inner join account_account aa on aa.id=grp_aml.account_id
                                inner join account_account_type aat on aat.id=aa.user_type_id
                                left join (select cr.name::date as from_date,cr.rate
                                                            ,coalesce(((LAG(cr.name::date) over (order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
                                                        from res_currency_rate cr where cr.currency_id=%s order by cr.name::date desc
                                                        ) tc on grp_aml.date between tc.from_date and tc.to_date
                            where aa.ajusta_ufv = TRUE
                            order by grp_aml.date
                        """
            self._cr.execute(cr_query, (from_date, to_date, currency_id,))

            if self._cr.rowcount > 0:
                cr_fetch = self._cr.dictfetchall()
                je_id = False
                account_move_env = self.env['account.move']
                account_move_line_env = self.env['account.move.line']
                # ToDo: #FIX9: period_id ya no existe!
                # period_env = self.env['account.period']
                # period_id = period_env.find(dt=to_date).id

                move_ins = {
                    "name": u'Actualización valor ' + case_dsc,
                    "journal_id": journal_id,
                    "date": to_date,
                    # "period_id": period_id,
                }
                je_id = account_move_env.create(move_ins)
            else:
                raise except_orm(_(u'Advertencia'), _(
                    'No encontraron líneas contables actualizables para el rango de fechas especificado.'))

            saldo_diff = 0.0
            ajuste_lines = {}
            counter_lines = {}
            for row in cr_fetch:
                saldo = row['saldo']
                saldo_ufv = row['saldo_ufv']
                rate_init = row['rate_init']
                account_id = row['account_id']
                counter_account_id = row[counter_account]

                saldo_diff = (saldo * (rate_now/rate_init)) - saldo
                if saldo_diff != 0:
                     #sum aggregate the counter lines to be created later
                    if account_id in ajuste_lines:
                        ajuste_lines[account_id] += saldo_diff
                    else:
                        ajuste_lines[account_id] = saldo_diff



                    #sum aggregate the counter lines to be created later
                    if counter_account_id in counter_lines:
                        counter_lines[counter_account_id] += saldo_diff
                    else:
                        counter_lines[counter_account_id] = saldo_diff
            # Crear líneas de Asiento con los totales calculados
            for counter_acc_id in counter_lines.keys():
                counter_amount = counter_lines[counter_acc_id]
                move_line_ins = {
                    "move_id": je_id.id,
                    "account_id": counter_acc_id,
                    "debit": counter_amount < 0 and counter_amount * -1 or 0,
                    "credit": counter_amount > 0 and counter_amount or 0,
                    "date": to_date,
                    "name": u'Ajuste Actualización valor ' + case_dsc,
                    "journal_id": journal_id,
                }
                account_move_line_env.with_context(check_move_validity=False).create(move_line_ins)

            for ajuste_acc_id in ajuste_lines.keys():
                ajuste_amount = ajuste_lines[ajuste_acc_id]
                move_line_ins = {
                    "move_id": je_id.id,
                    "account_id": ajuste_acc_id,
                    "debit": ajuste_amount > 0 and ajuste_amount or 0,
                    "credit": ajuste_amount < 0 and ajuste_amount * -1 or 0,
                    "date": to_date,
                    "name": u'Actualización valor ' + case_dsc,
                    "journal_id": journal_id,
                }
                account_move_line_env.with_context(check_move_validity=False).create(move_line_ins)

            # Mostrar Asiento
            if je_id:
                return {
                    'name': _('Journal Entries'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': False,
                    'res_model': 'account.move',
                    'domain': [],
                    'context': self._context,
                    'res_id': je_id.id,
                    'type': 'ir.actions.act_window',
                }
            else:
                return {'view_mode': 'tree,form', 'type': 'ir.actions.act_window_close'}
