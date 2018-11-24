# -*- coding: utf-8 -*-
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


from openerp import api, fields, models
import openerp.tools
import openerp.addons.decimal_precision as dp

import time
import datetime


class poi_libro_mayor_wiz(models.TransientModel):
    _name = 'poi.libro.mayor.wizard'
    _description = "Asistente Libro Mayor"

    def _get_all_journal(self):
        return self.env['account.journal'].search([])

    grouping = fields.Selection([('account','Cuenta'), ('analytic',u'Cuenta-Analítica'), ('acc_partner','Cuenta-Empresa'), ('partner_acc','Empresa-Cuenta')], string=u"Agrupación", default='account', required=True)
    analytic_ids = fields.Many2many('account.analytic.account', 'poi_libro_mayor_wizard_analytic_rel', 'wizard_id', 'analytic_id', string=u'Cuentas Analíticas', readonly=False)
    account_ids = fields.Many2many('account.account', 'poi_libro_mayor_wizard_account_rel', 'wizard_id', 'account_id', string=u'Cuentas específicas', readonly=False)
    journal_ids = fields.Many2many('account.journal', 'poi_libro_mayor_wizard_journal_rel', 'wizard_id', 'journal_id', 'Diarios', default=_get_all_journal, required=True)
    date_from = fields.Date('Fecha Desde', readonly=False)
    date_to = fields.Date('Fecha Hasta', readonly=False)
    partner_id = fields.Many2one('res.partner', string='Socio', readonly=False)
    usd = fields.Boolean('Ver USD', help=u"Mostrar montos en moneda dólar también")
    contra = fields.Boolean('Ver Contra Cuentas', help=u"Ver listado de Cuentas contra las cuales se contabiliza cada movimiento.")
    posted = fields.Boolean('Ver sólo Confirmados', help=u"Mostrar solamente Asientos confirmados", default=True)
    balance = fields.Boolean('Ver Balance Inicial', help=u"Mostrar una primera línea con el balance previo al rango de fechas solicitado.")

    @api.multi
    def launch_report(self):

        wizard = self
        context = self._context.copy() or {}

        report_view = 'poi.libro.mayor'
        report_tree = 'poi_report_mayor'
        context['grouping'] = wizard.grouping

        if wizard.grouping == "account":
            context['search_default_group_account'] = 1
            report_view = 'poi.libro.mayor'
        if wizard.grouping == "analytic":
            context['search_default_group_account'] = 1
            context['search_default_group_analytic'] = 1
            report_view = 'poi.libro.mayor'
        if wizard.grouping == "acc_partner":
            context['search_default_group_account'] = 1
            context['search_default_group_partner'] = 1
            report_view = 'poi.libro.mayor'
        if wizard.grouping == "partner_acc":
            context['search_default_group_partner'] = 1
            context['search_default_group_account'] = 1
            report_view = 'poi.libro.mayor.partner_acc'
            report_tree = 'poi_report_mayor_partner_acc'

        name_context = ""
        if wizard.date_from:
            context['date_from'] = wizard.date_from
            name_context += " Desde: %s | " % (datetime.date.strftime(datetime.datetime.strptime(wizard.date_from,'%Y-%m-%d').date() or '', "%d/%m/%Y"))
        if wizard.date_to:
            context['date_to'] = wizard.date_to
            name_context += " Hasta: %s | " % (datetime.date.strftime(datetime.datetime.strptime(wizard.date_to,'%Y-%m-%d').date() or '', "%d/%m/%Y"))
        if wizard.partner_id and wizard.partner_id.id > 0:
            context['partner_id'] = wizard.partner_id.id
            name_context += " Socio: %s | " % (wizard.partner_id.name)

        context['balance'] = wizard.balance
        context['search_default_ver_usd'] = wizard.usd and 1 or 0
        context['search_default_ver_contra'] = wizard.contra and 1 or 0
        if wizard.posted:
            context['state'] = 'posted'
            name_context += " Estado: Asentados | "
        else:
            context['state'] = ''
            name_context += " Estado: Todos | "

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
        if wizard.journal_ids:
            journals = []
            for row in wizard.journal_ids:
                journals.append(row.id)
            if journals != self._get_all_journal():
                context['journal_ids'] = journals

        #Recrear la vista sql en base a parametros del wizard
        self.env[report_view].with_context(dict(context)).build_view(self._cr, context)

        custom_model_view = self.env['ir.model.data'].sudo().get_object('poi_account_advanced',report_tree)


        action_report = {
            'name': "LIBRO MAYOR:" + name_context,
            'view_mode': 'tree',
            'view_type': 'form',
            'res_model': report_view,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'context': context,
            'view_id': custom_model_view.id,
        }
        return action_report


class poi_libro_mayor(models.Model):
    _name = 'poi.libro.mayor'
    _description = "Libro Mayor"
    _order = 'case_order,date,id'
    _auto = False

    #NBA. Columna saldo definida como Char porque las vistas tree agrupadas estaban inevitablemente jalando sumatoria que causa confusión
    name = fields.Char('Glosa', size=220, readonly=True)
    move_id = fields.Many2one('account.move', string='Asiento', readonly=True)
    analytic_id_a = fields.Many2one('account.analytic.account', string=u'Analítica', readonly=True)
    account_id_a = fields.Many2one('account.account', string='Cuenta', readonly=True)
    journal_id_a = fields.Many2one('account.journal', string='Diario', readonly=True)
    period_id_a = fields.Char(string=u'Período1')
    analytic_id_b = fields.Char(string=u'Analítica',)
    account_id_b = fields.Char(string='Cuenta',)
    journal_id_b = fields.Char(string='Diario',)
    period_id_b = fields.Char(string=u'Período2')
    case_order = fields.Integer('Orden caso')
    date = fields.Date('Fecha', readonly=True)
    ref = fields.Char('Ref.', size=64, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Socio', readonly=True)
    partner_id_b = fields.Char(string='Socio', readonly=True)
    company_id = fields.Many2one('res.company', string='Socio', readonly=True)
    state = fields.Selection([('draft', 'Abierto'), ('posted', 'Asentado')], 'Estado', readonly=True)
    debit = fields.Float('Debe', digits_compute=dp.get_precision('Account'), readonly=True)
    credit = fields.Float('Haber', digits_compute=dp.get_precision('Account'), readonly=True)
    debit_usd = fields.Float('Debe USD', digits_compute=dp.get_precision('Account'), size=64, readonly=True)
    credit_usd = fields.Float('Haber USD', digits_compute=dp.get_precision('Account'), size=64, readonly=True)
    saldo = fields.Char('Saldo', digits_compute=dp.get_precision('Account'), readonly=True)
    saldo_usd = fields.Char('Saldo USD', digits_compute=dp.get_precision('Account'), readonly=True)
    balance = fields.Float('Balance Total', digits_compute=dp.get_precision('Account'), readonly=True)
    balance_usd = fields.Float('Balance Total USD', digits_compute=dp.get_precision('Account'), readonly=True)
    contra_accounts = fields.Text('Contra Cuentas', readonly=True)

    def init(self, cr):
        #self.__dict__['_ids'] = 0
        b=False
        self.pool['poi.libro.mayor'].build_view(b=b, cr=cr, context={})
        #View can be rebuilt from Wizard

    @api.model
    def build_view(self, b, cr=False, context=None):


        #Para mantener la columna de Saldo coherente, tanto la filtración como la agrupación deben manejarse a nivel de query según se especifique en el wizard
        where_part = 'where True'
        where_bal = ''
        if context.get('date_from', False):
            where_part = "%s and am.date>='%s'" % (where_part,context.get('date_from','0'))
        if context.get('date_to', False):
            where_part = "%s and am.date<='%s'" % (where_part,context.get('date_to','0'))
        if context.get('account_ids', False):
            where_part = "%s and aml.account_id IN %s" % (where_part,str(context.get('account_ids',[0])).replace("[","(").replace("]",")"))
            where_bal = "%s and aml.account_id IN %s" % (where_bal,str(context.get('account_ids',[0])).replace("[","(").replace("]",")"))
        if context.get('analytic_ids', False):
            where_part = "%s and aml.analytic_account_id IN %s" % (where_part,str(context.get('analytic_ids',[0])).replace("[","(").replace("]",")"))
            where_bal = "%s and aml.analytic_account_id IN %s" % (where_bal,str(context.get('analytic_ids',[0])).replace("[","(").replace("]",")"))
        if context.get('state', '') != '':
            where_part = "%s and am.state='%s'" % (where_part,context.get('state',''))
            where_bal = "%s and am.state='%s'" % (where_bal,context.get('state',''))
        if context.get('partner_id', False):
            where_part = "%s and aml.partner_id = %s" % (where_part,context.get('partner_id',0))
            where_bal = "%s and aml.partner_id = %s" % (where_bal,context.get('partner_id',0))
        if context.get('journal_ids', False):
            where_part = "%s and aml.journal_id IN %s" % (where_part,str(context.get('journal_ids',[0])).replace("[","(").replace("]",")"))
            where_bal = "%s and aml.journal_id IN %s" % (where_bal,str(context.get('journal_ids',[0])).replace("[","(").replace("]",")"))

        partition_clause = "partition by urep.account_id"
        order_clause = "order by account_id,date,id"
        if context.get('grouping', False):
            grouping = context.get('grouping')

            if grouping == 'analytic':
                partition_clause = "partition by urep.account_id,urep.analytic_id"
                order_clause = "order by account_id,analytic_id,date,id"
            elif grouping == 'partner':
                partition_clause = "partition by urep.account_id,urep.partner_id"
                order_clause = "order by account_id,partner_id,date,id"

        balance_union = ""
        if context.get('balance', False):
            order_clause = order_clause.replace(',date',',case_order,date')
            balance_union = """UNION
                           select (aml.account_id * -1) as id, NULL as move_id, aml.account_id as account_id,0 as case_order, NULL as date, NULL AS analytic_id, NULL as period_id, NULL as journal_id, NULL as partner_id, NULL as company_id, '' as state, 'INICIAL' as name, 'INICIAL' as ref,  case when sum(COALESCE(aml.debit, 0.0) - COALESCE(aml.credit, 0.0)) > 0 then sum(COALESCE(aml.debit, 0.0) - COALESCE(aml.credit, 0.0)) else 0 end AS debit, case when sum(COALESCE(aml.debit, 0.0) - COALESCE(aml.credit, 0.0)) < 0 then sum(COALESCE(aml.credit, 0.0) - COALESCE(aml.debit, 0.0)) else 0 end AS credit,'' AS contra_accounts
                           from account_move_line aml inner join account_move am on am.id=aml.move_id
                           where am.date < '%s' %s
                           group by aml.account_id
                            """ % (context.get('date_from','1900-01-01'), where_bal)


        #openerp.tools.sql.drop_view_if_exists(cr, 'poi_libro_mayor')

        view_query = """
            DROP MATERIALIZED VIEW IF EXISTS poi_libro_mayor;
            CREATE MATERIALIZED VIEW poi_libro_mayor AS (
                select urep.id, urep.move_id, urep.account_id as account_id_a,
                                    urep.analytic_id as analytic_id_a,
                                    period_id as period_id_a,
                                    journal_id as journal_id_a,
                                    (t1.code || ' ' || t1.name) as account_id_b,
                                    COALESCE(t2.name,'') as analytic_id_b,
                                    period_id as period_id_b,
                                    t4.name as journal_id_b,
                                    case_order, urep.date, urep.partner_id, urep.company_id,
                                    urep.state,
                                    urep.name, urep.ref, urep.debit, urep.credit, urep.contra_accounts
                    ,to_char(sum(COALESCE(urep.debit, 0.0) - COALESCE(urep.credit, 0.0)) OVER (%s ORDER BY urep.case_order,urep.date,urep.id), 'FM999,999,999.00') AS saldo
                    ,case when lead(account_id) over (%s ORDER BY urep.case_order, urep.date, urep.id) = account_id then null else sum(COALESCE(urep.debit, 0.0) - COALESCE(urep.credit, 0.0)) OVER (%s ORDER BY urep.case_order, urep.date, urep.id) end as balance
                    ,(urep.debit*tc.rate) as debit_usd, (urep.credit*tc.rate) as credit_usd
                    ,to_char(sum(coalesce(urep.debit*(tc.rate), 0.0) - coalesce(urep.credit*(tc.rate), 0.0)) over (%s order by urep.case_order,urep.date,urep.id), 'FM999,999,999.00') as saldo_usd
                    ,case when lead(account_id) over (%s ORDER BY urep.case_order, urep.date, urep.id) = account_id then null else sum(coalesce(urep.debit*(tc.rate), 0.0) - coalesce(urep.credit*(tc.rate), 0.0)) over (%s order by urep.case_order,urep.date,urep.id) end as balance_usd
                from
                (   select aml.id,aml.move_id,aml.account_id,1 as case_order,am.date,aml.analytic_account_id as analytic_id,
                    to_char(aml.date, 'MM/YYYY') as period_id,
                    aml.journal_id,
                    aml.partner_id,
                    aml.company_id,
                    am.state,
                    aml.name,
                    aml.ref
                        ,avg(aml.debit) as debit, avg(aml.credit) as credit
                        ,concat('-> ',string_agg(contra.name,E'\n-> ')) as contra_accounts
                    from account_move_line aml
                        inner join account_account aa on aa.id=aml.account_id
                        inner join account_move am on am.id=aml.move_id
                        left outer join (select caml.move_id as m_id,caml.account_id,caa.name,sign(sum(caml.debit-caml.credit)) as signo
                                        from account_move_line caml inner join account_account caa on caa.id=caml.account_id
                                        group by caml.move_id,caml.account_id,caa.name
                                        order by caml.move_id
                                    ) contra on (contra.m_id=aml.move_id and contra.account_id!=aml.account_id and sign(aml.debit-aml.credit)!=contra.signo)
                    %s
                    group by aml.id,aml.account_id,am.state,am.date
                %s
                ) as urep
                inner join account_account t1 on t1.id = urep.account_id
                left outer join account_analytic_account t2 on t2.id = urep.analytic_id
                inner join account_journal t4 on t4.id = urep.journal_id

                left join (select cr.name::date as from_date,cr.rate
                                ,coalesce(((LAG(cr.name::date) over (order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
                            from res_currency_rate cr where cr.currency_id=3 order by cr.name::date desc
                            ) tc on urep.date between tc.from_date and tc.to_date
                %s
            )
        """ % (partition_clause,partition_clause,partition_clause,partition_clause,partition_clause,partition_clause,where_part,balance_union,order_clause)

        #print view_query
        cr.execute(view_query)

    @api.multi
    def launch_form(self):

        line = self

        action_form = {
            'name': "Asiento contable",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.move',
            'res_id': int(line.move_id.id),
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': str([]),
            'target': 'new',
            'context': self._context,
        }
        return action_form


class poi_libro_mayor_partner_acc(models.Model):
    _inherit = 'poi.libro.mayor'
    _name = 'poi.libro.mayor.partner_acc'
    _description = "Libro Mayor (Empresa-Cuenta)"
    _order = 'case_order,date,id'
    _auto = False

    def init(self, cr):
        self.__dict__['_ids'] = 0
        self.build_view(cr=cr, context={})
        #View can be rebuilt from Wizard

    @api.model
    def build_view(self, cr=False, context=None):

        #Para mantener la columna de Saldo coherente, tanto la filtración como la agrupación deben manejarse a nivel de query según se especifique en el wizard
        where_part = 'where True'
        where_bal = ''
        if context.get('date_from', False):
            where_part = "%s and am.date>='%s'" % (where_part,context.get('date_from','0'))
        if context.get('date_to', False):
            where_part = "%s and am.date<='%s'" % (where_part,context.get('date_to','0'))
        if context.get('account_ids', False):
            where_part = "%s and aml.account_id IN %s" % (where_part,str(context.get('account_ids',[0])).replace("[","(").replace("]",")"))
            where_bal = "%s and aml.account_id IN %s" % (where_bal,str(context.get('account_ids',[0])).replace("[","(").replace("]",")"))
        if context.get('analytic_ids', False):
            where_part = "%s and aml.analytic_account_id IN %s" % (where_part,str(context.get('analytic_ids',[0])).replace("[","(").replace("]",")"))
            where_bal = "%s and aml.analytic_account_id IN %s" % (where_bal,str(context.get('analytic_ids',[0])).replace("[","(").replace("]",")"))
        if context.get('state', '') != '':
            where_part = "%s and am.state='%s'" % (where_part,context.get('state',''))
            where_bal = "%s and am.state='%s'" % (where_bal,context.get('state',''))
        if context.get('partner_id', False):
            where_part = "%s and aml.partner_id = %s" % (where_part,context.get('partner_id',0))
            where_bal = "%s and aml.partner_id = %s" % (where_bal,context.get('partner_id',0))
        if context.get('journal_ids', False):
            where_part = "%s and aml.journal_id IN %s" % (where_part,str(context.get('journal_ids',[0])).replace("[","(").replace("]",")"))
            where_bal = "%s and aml.journal_id IN %s" % (where_bal,str(context.get('journal_ids',[0])).replace("[","(").replace("]",")"))

        partition_clause = "partition by urep.partner_id,urep.account_id"
        order_clause = "order by urep.partner_id,account_id,date,id"

        balance_union = ""
        if context.get('balance', False):
            order_clause = order_clause.replace(',date',',case_order,date')
            balance_union = """UNION
                           select (aml.account_id * -1) as id, NULL as move_id, aml.account_id as account_id,0 as case_order, NULL as date, NULL AS analytic_id, NULL as period_id, NULL as journal_id, NULL as partner_id, NULL as company_id, '' as state, 'INICIAL' as name, 'INICIAL' as ref
                                ,  case when sum(COALESCE(aml.debit, 0.0) - COALESCE(aml.credit, 0.0)) > 0 then sum(COALESCE(aml.debit, 0.0) - COALESCE(aml.credit, 0.0)) else 0 end AS debit
                                , case when sum(COALESCE(aml.debit, 0.0) - COALESCE(aml.credit, 0.0)) < 0 then sum(COALESCE(aml.credit, 0.0) - COALESCE(aml.debit, 0.0)) else 0 end AS credit,'' AS contra_accounts
                           from account_move_line aml inner join account_move am on am.id=aml.move_id
                           where am.date < '%s' %s
                           group by aml.partner_id
                            """ % (context.get('date_from','1900-01-01'), where_bal)


        #openerp.tools.sql.drop_view_if_exists(cr, 'poi_libro_mayor')

        view_query = """
            DROP MATERIALIZED VIEW IF EXISTS poi_libro_mayor_partner_acc;
            CREATE MATERIALIZED VIEW poi_libro_mayor_partner_acc AS (
                select urep.id, urep.move_id, urep.account_id as account_id_a,
                                    urep.analytic_id as analytic_id_a,
                                    period_id as period_id_a,
                                    journal_id as journal_id_a,
                                    (t1.code || ' ' || t1.name) as account_id_b,
                                    COALESCE(t2.name,'') as analytic_id_b,
                                    period_id as period_id_b,
                                    t4.name as journal_id_b,
                                    case_order, urep.date, urep.partner_id, urep.company_id,
                                    urep.state,
                                    urep.name, urep.ref, urep.debit, urep.credit, urep.contra_accounts
                    ,to_char(sum(COALESCE(urep.debit, 0.0) - COALESCE(urep.credit, 0.0)) OVER (%s ORDER BY urep.case_order,urep.date,urep.id), 'FM999,999,999.00') AS saldo
                    ,case when lead(account_id) over (%s ORDER BY urep.case_order, urep.date, urep.id) = account_id then null else sum(COALESCE(urep.debit, 0.0) - COALESCE(urep.credit, 0.0)) OVER (%s ORDER BY urep.case_order, urep.date, urep.id) end as balance
                    ,(urep.debit*tc.rate) as debit_usd, (urep.credit*tc.rate) as credit_usd
                    ,to_char(sum(coalesce(urep.debit*(tc.rate), 0.0) - coalesce(urep.credit*(tc.rate), 0.0)) over (%s order by urep.case_order,urep.date,urep.id), 'FM999,999,999.00') as saldo_usd
                    ,case when lead(account_id) over (%s ORDER BY urep.case_order, urep.date, urep.id) = account_id then null else sum(coalesce(urep.debit*(tc.rate), 0.0) - coalesce(urep.credit*(tc.rate), 0.0)) over (%s order by urep.case_order,urep.date,urep.id) end as balance_usd
                from
                (   select aml.id,aml.move_id,aml.account_id,1 as case_order,am.date,aml.analytic_account_id as analytic_id,
                    to_char(aml.date, 'MM/YYYY') as period_id,
                    aml.journal_id,
                    aml.partner_id,
                    aml.company_id,
                    am.state,
                    aml.name,
                    aml.ref
                        ,avg(aml.debit) as debit, avg(aml.credit) as credit
                        ,concat('-> ',string_agg(contra.name,E'\n-> ')) as contra_accounts
                    from account_move_line aml
                        inner join account_account aa on aa.id=aml.account_id
                        inner join account_move am on am.id=aml.move_id
                        left outer join (select caml.move_id as m_id,caml.account_id,caa.name,sign(sum(caml.debit-caml.credit)) as signo
                                        from account_move_line caml inner join account_account caa on caa.id=caml.account_id
                                        group by caml.move_id,caml.account_id,caa.name
                                        order by caml.move_id
                                    ) contra on (contra.m_id=aml.move_id and contra.account_id!=aml.account_id and sign(aml.debit-aml.credit)!=contra.signo)
                    %s
                    group by aml.id,aml.account_id,am.state,am.date
                %s
                ) as urep
                inner join account_account t1 on t1.id = urep.account_id
                left outer join account_analytic_account t2 on t2.id = urep.analytic_id
                inner join account_journal t4 on t4.id = urep.journal_id

                left join (select cr.name::date as from_date,cr.rate
                                ,coalesce(((LAG(cr.name::date) over (order by cr.name::date desc))::date - interval '1' day)::date,'9999-12-31'::date) as to_date
                            from res_currency_rate cr where cr.currency_id=3 order by cr.name::date desc
                            ) tc on urep.date between tc.from_date and tc.to_date
                %s
            )
        """ % (partition_clause,partition_clause,partition_clause,partition_clause,partition_clause,partition_clause,where_part,balance_union,order_clause)

        #print view_query
        cr.execute(view_query)
