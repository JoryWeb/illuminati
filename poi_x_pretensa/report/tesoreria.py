##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Poiesis Consulting
#    autor: Nicolas Bustillos
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


from openerp.osv import fields, osv
import openerp.tools
import openerp.addons.decimal_precision as dp

import time


class poi_pret_tesoreria(osv.Model):
    _name = 'pret.tesoreria'
    _description = u"Reporte Tesorería"
    _order = 'date,id'
    _auto = False

    _columns = {
        'name': fields.char('Glosa', size=64, readonly=True),
        'move_id': fields.many2one('account.move', string='Asiento', readonly=True),
        'analytic_id': fields.many2one('account.analytic.account', string=u'Analítica', readonly=True),
        'account_id': fields.many2one('account.account', string='Cuenta', readonly=True),
        'journal_id': fields.many2one('account.journal', string='Diario', readonly=True),
        # 'period_id': fields.many2one('account.period', string=u'Período', readonly=True),
        'period_id': fields.char(string=u'Período', readonly=True),
        'date': fields.date('Fecha', readonly=True),
        'ref': fields.char('Ref.', size=64, readonly=True),
        'partner_id': fields.many2one('res.partner', string='Socio', readonly=True),
        'company_id': fields.many2one('res.company', string='Socio', readonly=True),
        'state': fields.selection([('draft', 'Abierto'), ('posted', 'Confirmado')], 'Estado', readonly=True),
        'debit': fields.float('Debe', digits_compute=dp.get_precision('Account'), readonly=True),
        'credit': fields.float('Haber', digits_compute=dp.get_precision('Account'), readonly=True),
        'debit_usd': fields.float('Debe USD', digits_compute=dp.get_precision('Account'), size=64, readonly=True),
        'credit_usd': fields.float('Haber USD', digits_compute=dp.get_precision('Account'), size=64, readonly=True),
        'saldo': fields.char('Saldo', readonly=True),
        'saldo_usd': fields.char('Saldo USD', readonly=True),
        'shop_id': fields.many2one('stock.warehouse', string='Tienda', readonly=True),
        'contra_accounts': fields.text('Contra Cuentas', readonly=True),
        'nro_check': fields.char('Nr Cheque', readonly=True),
    }

    def init(self, cr):
        self.build_view(cr, context={})
        # View can be rebuilt from Wizard

    def build_view(self, cr, context=None):

        context = context or {}
        # Para mantener la columna de Saldo coherente, tanto la filtración como la agrupación deben manejarse a nivel de query según se especifique en el wizard
        where_part = ''
        if context.get('date_from', False):
            where_part = "%s and aml.date>='%s'" % (where_part, context.get('date_from', '0'))
        if context.get('date_to', False):
            where_part = "%s and aml.date<='%s'" % (where_part, context.get('date_to', '0'))
        if context.get('account_ids', False):
            where_part = "%s and aml.account_id IN %s" % (
            where_part, str(context.get('account_ids', [0])).replace("[", "(").replace("]", ")"))
        if context.get('analytic_ids', False):
            where_part = "%s and aml.analytic_account_id IN %s" % (
            where_part, str(context.get('analytic_ids', [0])).replace("[", "(").replace("]", ")"))
        if context.get('state', False):
            where_part = "%s and am.state='%s'" % (where_part, context.get('state', ''))
        if context.get('partner_id', False):
            where_part = "%s and aml.partner_id = %s" % (where_part, context.get('partner_id', 0))

        partition_clause = "partition by aml.account_id"
        order_clause = "order by aml.account_id,aml.date,aml.id"
        if context.get('grouping', False):
            grouping = context.get('grouping')
            if grouping == 'analytic':
                partition_clause = "partition by aml.account_id,aml.analytic_account_id"
                order_clause = "order by aml.account_id,aml.analytic_account_id,aml.date,aml.id"
            if grouping == 'partner':
                partition_clause = "partition by aml.account_id,aml.partner_id"
                order_clause = "order by aml.account_id,aml.partner_id,aml.date,aml.id"

        openerp.tools.sql.drop_view_if_exists(cr, 'pret_tesoreria')

        view_query = """
            CREATE OR REPLACE VIEW pret_tesoreria AS (
                select mayor.*,av.id as voucher_id,av.check_number as nro_check,ss.id as shop_id
                from (
                    select aml.id,aml.move_id,aml.account_id,aml.date,aml.analytic_account_id as analytic_id, to_char(aml.date,'MM/YYYY') as period_id, aml.journal_id,aml.partner_id,aml.company_id,am.state,aml.name,aml.ref
                        ,avg(aml.debit) as debit, avg(aml.credit) as credit, to_char(sum(coalesce(aml.debit, 0.0) - coalesce(aml.credit, 0.0)) over (%s order by aml.date,aml.id), 'FM999,999,999.00') as saldo
                        ,avg(aml.debit/tc.rate) as debit_usd, avg(aml.credit/tc.rate) as credit_usd, to_char(sum(coalesce(aml.debit/avg(tc.rate), 0.0) - coalesce(aml.credit/avg(tc.rate), 0.0)) over (%s order by aml.date,aml.id), 'FM999,999,999.00') as saldo_usd
                        ,concat('-> ',string_agg(contra.name,E'\n-> ')) as contra_accounts
                    from account_move_line aml
                        inner join account_move am on am.id = aml.move_id
                        inner join account_account aa on aa.id=aml.account_id
                        inner join (select cr.name::date as from_date,cr.rate
                                    ,coalesce(((LAG(cr.name::date) over (order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
                                from res_currency_rate cr
                                where cr.currency_id=62
                                order by cr.name::date desc
                                ) tc on aml.date between tc.from_date and tc.to_date
                        left outer join (select caml.move_id as m_id,caml.account_id,caa.name,sign(sum(caml.debit-caml.credit)) as signo
                                        from account_move_line caml inner join account_account caa on caa.id=caml.account_id
                                        group by caml.move_id,caml.account_id,caa.name
                                        order by caml.move_id
                                    ) contra on (contra.m_id=aml.move_id and contra.account_id!=aml.account_id and sign(aml.debit-aml.credit)!=contra.signo)
                    where aml.account_id in (select distinct aj.default_debit_account_id from account_journal aj where aj.type in ('cash','bank')
                                                UNION
                                            select distinct aj.default_credit_account_id from account_journal aj where aj.type in ('cash','bank'))
                    %s
                    group by aml.id,aml.account_id,am.state
                    %s
                ) as mayor
                left outer join account_voucher av on av.move_id = mayor.move_id
                left outer join stock_warehouse ss on ss.analytic_account_id = mayor.analytic_id
                order by mayor.date,mayor.id
            )
        """ % (partition_clause, partition_clause, where_part, order_clause)

        cr.execute(view_query)

    def launch_form(self, cr, uid, ids, context=None):

        line = self.browse(cr, uid, ids[0], context=context)

        action_form = {
            'name': "Asiento contable",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.move',
            'res_id': line.move_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': context,
        }
        return action_form


poi_pret_tesoreria()


class poi_pret_tesoreria_wiz(osv.TransientModel):
    _name = 'pret.tesoreria.wizard'
    _description = u"Asistente Reporte Tesorería"

    _columns = {
        'grouping': fields.selection(
            [('none', u'Sin agrupación'), ('account', 'Cuenta'), ('analytic', u'Cuenta-Analítica'),
             ('partner', 'Cuenta-Socio')], string=u"Agrupación", required=True),
        'analytic_ids': fields.many2many('account.analytic.account', 'pret_tesoreria_wizard_analytic_rel', 'wizard_id',
                                         'analytic_id', string=u'Cuentas Analíticas', readonly=False),
        'account_ids': fields.many2many('account.account', 'pret_tesoreria_wizard_account_rel', 'wizard_id',
                                        'account_id', string=u'Cuentas específicas', readonly=False),
        'journal_ids': fields.many2many('account.journal', 'pret_tesoreria_wizard_journal_rel', 'wizard_id',
                                        'journal_id', 'Diarios', required=True),
        # 'period_id': fields.many2one('account.period', string=u'Período', readonly=False),
        'date_from': fields.date('Fecha Desde', readonly=False),
        'date_to': fields.date('Fecha Hasta', readonly=False),
        'partner_id': fields.many2one('res.partner', string='Socio', readonly=False),
        # 'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', help='Keep empty for all open fiscal year'),
        'usd': fields.boolean('Ver USD', help=u"Mostrar montos en moneda dólar también"),
        'contra': fields.boolean('Ver Contra Cuentas',
                                 help=u"Ver listado de Cuentas contra las cuales se contabiliza cada movimiento."),
        'posted': fields.boolean('Ver sólo Confirmados', help=u"Mostrar solamente Asientos confirmados"),
    }

    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = time.strftime('%Y-%m-%d')
        company_id = False
        ids = context.get('active_ids', [])
        if ids and context.get('active_model') == 'account.account':
            company_id = self.pool.get('account.account').browse(cr, uid, ids[0], context=context).company_id.id
        else:  # use current company id
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
        return fiscalyears and fiscalyears[0] or False

    def _get_all_journal(self, cr, uid, context=None):
        return self.pool.get('account.journal').search(cr, uid, [])

    _defaults = {
        'grouping': 'none',
        # 'fiscalyear_id': _get_fiscalyear,
        'journal_ids': _get_all_journal,
        'posted': True,
    }

    def launch_report(self, cr, uid, ids, context=None):

        wizard = self.browse(cr, uid, ids[0], context=context)

        context['grouping'] = wizard.grouping
        if wizard.grouping == "account":
            context['search_default_group_account'] = 1
        elif wizard.grouping == "analytic":
            context['search_default_group_analytic'] = 1
        elif wizard.grouping == "partner":
            context['search_default_group_partner'] = 1
        else:
            context['search_default_group_account'] = 0
            context['search_default_group_analytic'] = 0
            context['search_default_group_partner'] = 0

        name_context = ""
        if wizard.date_from:
            context['date_from'] = wizard.date_from
            name_context += "Desde:%s " % (wizard.date_from)
        if wizard.date_to:
            context['date_to'] = wizard.date_to
            name_context += "Hasta:%s " % (wizard.date_to)
        if wizard.partner_id and wizard.partner_id.id > 0:
            context['partner_id'] = wizard.partner_id.id
        if wizard.posted:
            context['state'] = 'posted'
        if wizard.usd:
            context['search_default_ver_usd'] = 1
        if wizard.contra:
            context['search_default_ver_contra'] = 1
        if wizard.account_ids:
            accounts = []
            for row in wizard.account_ids:
                accounts.append(row.id)
            context['account_ids'] = accounts
        if wizard.analytic_ids:
            analytics = []
            for row in wizard.analytic_ids:
                analytics.append(row.id)
            context['analytic_ids'] = analytics

        # Recrear la vista sql en base a parametros del wizard
        self.pool.get('pret.tesoreria').build_view(cr, context=context)

        action_report = {
            'name': "Reporte Tesorería",
            'view_mode': 'tree',
            'view_type': 'form',
            'res_model': 'pret.tesoreria',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'context': context,
        }
        return action_report


poi_pret_tesoreria_wiz()
