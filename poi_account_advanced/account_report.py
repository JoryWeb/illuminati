# -*- coding: utf-8 -*-
##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2011 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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


from openerp.osv import fields, osv
from openerp import api
import openerp.addons.decimal_precision as dp
import time
import datetime
from lxml import etree

from openerp.osv.orm import setup_modifiers
from openerp.tools.translate import _

from openerp.report import report_sxw
from openerp import api, models


class partner(osv.osv):
    _inherit = 'res.partner'

    def print_partner_ledger(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'poi_account_advanced', 'account_partner_ledger_report_view')

        inv = self.browse(cr, uid, ids[0], context=context)
        return {
            'name':_("Extracto de Cuentas"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.partner.report.poi',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {

            }
        }


class account_partner_report_poi(osv.osv_memory):
    _name = "account.partner.report.poi"
    _description = "Poi Account Partner Report"


    def onchange_chart_id(self, cr, uid, ids, chart_account_id=False, context=None):
        res = {}
        if chart_account_id:
            company_id = self.pool.get('account.account').browse(cr, uid, chart_account_id, context=context).company_id.id
            now = time.strftime('%Y-%m-%d')
            domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
            fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
            res['value'] = {'company_id': company_id, 'fiscalyear_id': fiscalyears and fiscalyears[0] or False}
        return res

    _columns = {
        'chart_account_id': fields.many2one('account.account', 'Plan contable', help='Seleccionar plan contable', required=True, domain = [('parent_id','=',False)]),
        'company_id': fields.related('chart_account_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Ejercicio fiscal', help='Dejarlo vacio para todos los ejercicios fiscales abiertos.'),

        'period_from': fields.many2one('account.period', 'Periodo inicial'),
        'period_to': fields.many2one('account.period', 'Periodo final'),
        #'journal_ids': fields.many2many('account.journal', string='Diarios', required=True),
        'date_from': fields.date("Fecha inicial"),
        'date_to': fields.date("Fecha final "),
        'target_move': fields.selection([('posted', 'Todos los asientos asentados'),
                                         ('all', 'Todos los asientos'),
                                        ], 'Movimientos destino', required=True),
        'initial_balance': fields.boolean('Include Initial Balances',
                                    help='If you selected to filter by date or period, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.'),

        'filter': fields.selection([('filter_no', 'No filtros'), ('filter_date', 'Fecha'), ('filter_period', 'Periodos'), ('unreconciled', 'Asientos no Conciliados')], "Filtrar por", required=True),
        'page_split': fields.boolean('Una empresa por pagina', help='Mostrar informe con una empresa por pagina'),
        'amount_currency': fields.boolean("Con divisa", help="Añade la columna de moneda en el informe si la moneda difiere de la moneda de la compañia."),
        #'journal_ids': fields.many2many('account.journal', 'account_partner_ledger_journal_rel', 'account_id', 'journal_id', 'Journals', required=True),
        'result_selection': fields.selection([('customer','Cuentas a cobrar'),
                                              ('supplier','Cuentas a pagar'),
                                              ('customer_supplier','Cuentas a cobrar ya pagar')],
                                              "De empresas", required=True),

        }

    def _check_company_id(self, cr, uid, ids, context=None):
        for wiz in self.browse(cr, uid, ids, context=context):
            company_id = wiz.company_id.id
            if wiz.fiscalyear_id and company_id != wiz.fiscalyear_id.company_id.id:
                return False
            if wiz.period_from and company_id != wiz.period_from.company_id.id:
                return False
            if wiz.period_to and company_id != wiz.period_to.company_id.id:
                return False
        return True

    _constraints = [
        (_check_company_id, 'The fiscalyear, periods or chart of account chosen have to belong to the same company.', ['chart_account_id','fiscalyear_id','period_from','period_to']),
    ]

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None:context = {}
        res = super(account_partner_report_poi, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        if context.get('active_model', False) == 'account.account':
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//field[@name='chart_account_id']")
            for node in nodes:
                node.set('readonly', '1')
                node.set('help', 'If you print the report from Account list/form view it will not consider Charts of account')
                setup_modifiers(node, res['fields']['chart_account_id'])
            res['arch'] = etree.tostring(doc)
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        if context is None:context = {}
        res={}
        #res = super(account_partner_report_poi, self).onchange_filter(cr, uid, ids, filter=filter, fiscalyear_id=fiscalyear_id, context=context)
        #if filter in ['filter_no', 'unreconciled']:
            #if filter == 'unreconciled':
                #res['value'].update({'fiscalyear_id': False})
            #res['value'].update({'initial_balance': False, 'period_from': False, 'period_to': False, 'date_from': False ,'date_to': False})
        return res

    def _get_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False), ('company_id', '=', user.company_id.id)], limit=1)
        return accounts and accounts[0] or False

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
        return self.pool.get('account.journal').search(cr, uid ,[])

    _defaults = {
            'fiscalyear_id': _get_fiscalyear,
            'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.common.report.poi',context=c),
            'journal_ids': _get_all_journal,
            'filter': 'filter_no',
            'chart_account_id': _get_account,
            'target_move': 'posted',
            'initial_balance': False,
            'page_split': False,
            'result_selection': 'customer',
    }




    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        result['fiscalyear'] = 'fiscalyear_id' in data['form'] and data['form']['fiscalyear_id'] or False
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['chart_account_id'] = 'chart_account_id' in data['form'] and data['form']['chart_account_id'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        if data['form']['filter'] == 'filter_date':
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to']
        elif data['form']['filter'] == 'filter_period':
            if not data['form']['period_from'] or not data['form']['period_to']:
                raise osv.except_osv(_('Error!'),_('Select a starting and an ending period.'))
            result['period_from'] = data['form']['period_from']
            result['period_to'] = data['form']['period_to']
        return result

    @api.multi
    def check_report(self, data):

        data['id_wiz']= self._ids
        return self.env['report'].get_action(self, 'poi_account_advanced.report_partnerledger_poi', data=data)

class report_account_partnerledger_poi(models.AbstractModel):
    _name = 'report.poi_account_advanced.report_partnerledger_poi'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('poi_account_advanced.report_partnerledger_poi')

        id_wiz=data['id_wiz'][0]

        start_date=''
        end_date=''

        if (self.env['account.partner.report.poi'].browse(id_wiz).date_from) != False:
            start_date=datetime.date.strftime(datetime.datetime.strptime(self.env['account.partner.report.poi'].browse(id_wiz).date_from,'%Y-%m-%d').date() or '', "%d/%m/%Y")
        else:
            start_date=self.env['account.partner.report.poi'].browse(id_wiz).date_from

        if (self.env['account.partner.report.poi'].browse(id_wiz).date_to) != False:
            end_date=datetime.date.strftime(datetime.datetime.strptime(self.env['account.partner.report.poi'].browse(id_wiz).date_to,'%Y-%m-%d').date() or '', "%d/%m/%Y")
        else:
            end_date=self.env['account.partner.report.poi'].browse(id_wiz).date_to

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(data['active_id']),
            'time': time,
            'lines': self.lines,
            'sum_debit_partner': self._sum_debit_partner,
            'sum_credit_partner': self._sum_credit_partner,
            'get_currency': self._get_currency,
            'get_currency_id': self.env['res.users'].browse(self._uid).company_id.currency_id.id,
            'get_logo':self.env['res.users'].browse(self._uid).company_id.logo,
            'get_start_period': self.env['account.partner.report.poi'].browse(id_wiz).period_from.name,
            'get_end_period': self.env['account.partner.report.poi'].browse(id_wiz).period_to.name,
            'get_account': self.env['account.partner.report.poi'].browse(id_wiz).chart_account_id.name,
            'get_filter': self.env['account.partner.report.poi'].browse(id_wiz).filter,
            'get_start_date': start_date,
            'get_end_date': end_date,
            'get_fiscalyear': self.env['account.partner.report.poi'].browse(id_wiz).fiscalyear_id.name,
            'get_journal': self._get_journal,
            'get_partners':self._get_partners,
            'get_intial_balance':self._get_intial_balance,
            'display_initial_balance':self._display_initial_balance,
            'display_currency':self._display_currency,
            'get_target_move': self.env['account.partner.report.poi'].browse(id_wiz).target_move,
        }

        #return self.pool['report'].render('poi_account_advanced.report_partnerledger_poi', docargs)
        return report_obj.render('poi_account_advanced.report_partnerledger_poi', docargs)

    def _get_filter(self, data):
        id_wizard=data._context['active_id']
        model_wizard=self.env['account.partner.report.poi'].browse(id_wizard)
        if model_wizard.filter == 'unreconciled':
            return _('Unreconciled Entries')
        return model_wizard.filter


    def lines(self, data):
        move_state = ['draft','posted']
        id_wizard=data._context['active_id']
        partner_id=data.ids[0]
        model_wizard=self.env['account.partner.report.poi'].browse(id_wizard)

        result_selection=model_wizard.result_selection

        if result_selection == 'supplier':
            ACCOUNT_TYPE = ['payable']
        elif result_selection == 'customer':
            ACCOUNT_TYPE = ['receivable']
        else:
            ACCOUNT_TYPE = ['payable','receivable']

        self._cr.execute(
            "SELECT a.id " \
            "FROM account_account a " \
            "LEFT JOIN account_account_type t " \
                "ON (a.type=t.code) " \
                'WHERE a.type IN %s' \
                "AND a.active", (tuple(ACCOUNT_TYPE), ))

        account_ids = [a for (a,) in self._cr.fetchall()]

        target_move=model_wizard.target_move
        if target_move == 'posted':
            move_state = ['posted']

        full_account = []
        reconcil = True
        initial_balance = model_wizard.initial_balance
        fiscalyear=self.env['account.partner.report.poi'].browse(id_wizard).fiscalyear_id.id
        init_query="l.state <> 'draft' AND l.period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN ("+str(fiscalyear)+"))  AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')"
        if model_wizard.filter == 'unreconciled':
            reconcil = False
        if reconcil:
            RECONCILE_TAG = " "
        else:
            RECONCILE_TAG = "AND l.reconcile_id IS NULL"

        filtro=self.env['account.partner.report.poi'].browse(id_wizard).filter
        condicion_fecha=" "
        condicion_periodo=" "
        date_from= self.env['account.partner.report.poi'].browse(id_wizard).date_from
        date_to = self.env['account.partner.report.poi'].browse(id_wizard).date_to


        if date_from != False and date_to != False and filtro=='filter_date':
            condicion_fecha="AND l.date>='"+date_from+"' AND l.date<= '"+date_to+"'"
        else:
            condicion_fecha=" "

        periodo_from=self.env['account.partner.report.poi'].browse(id_wizard).period_from.date_start

        periodo_to=self.env['account.partner.report.poi'].browse(id_wizard).period_to.date_stop


        if periodo_from != False and periodo_to != False and filtro=='filter_period':
            condicion_periodo="AND (l.date BETWEEN '"+str(periodo_from)+"' AND '"+str(periodo_to)+"')"
        else:
            condicion_periodo=" "


        self._cr.execute(
            "SELECT l.date, to_char(l.date, 'dd/mm/yyyy') as date_format, j.code, acc.code as a_code, acc.name as a_name, l.ref, m.name as move_name, l.name, sum(l.debit) as debit, sum(l.credit) as credit, l.amount_currency,l.currency_id, c.symbol AS currency_code, " \
            "ai.number, ai.cc_nro as num_factura, (j.name||'('||case when l.currency_id is null then rcu.name else c.name end||')') as forma_pago " \
            "FROM account_move_line l " \
            "LEFT JOIN account_journal j " \
                "ON (l.journal_id = j.id) " \
            "LEFT JOIN account_account acc " \
                "ON (l.account_id = acc.id) " \
            "LEFT JOIN res_currency c ON (l.currency_id=c.id)" \
            "LEFT JOIN account_move m ON (m.id=l.move_id)" \
            "LEFT JOIN account_invoice ai ON (m.id=ai.move_id)" \
            "LEFT JOIN res_partner rp ON (rp.id=l.partner_id) " \
            "LEFT JOIN res_company rc ON (rc.id=rp.company_id)" \
            "LEFT JOIN res_currency rcu ON (rcu.id=rc.currency_id)" \
            "WHERE l.partner_id = %s " \
                "AND l.account_id IN %s AND " + init_query +" " \
                "AND m.state IN %s " \
                " " + condicion_fecha + " "\
                " " + condicion_periodo + " "\
                " " + RECONCILE_TAG + " "\
            "group by l.date, j.code, acc.code, acc.name, l.ref, m.name, l.name, l.amount_currency, l.currency_id, c.symbol, ai.number, ai.cc_nro, j.name, l.currency_id, rcu.name, c.name " \
             "ORDER BY l.date",
                (partner_id, tuple(account_ids), tuple(move_state)))
        res = self._cr.dictfetchall()
        sum = 0.0
        if initial_balance and res:
            sum = res[0][2]
        for r in res:
            sum += r['debit'] - r['credit']
            r['progress'] = sum
            full_account.append(r)
        return full_account

    def _get_intial_balance(self, data):
        move_state = ['draft','posted']
        id_wizard=data._context['active_id']
        model_wizard=self.env['account.partner.report.poi'].browse(id_wizard)
        target_move=model_wizard.target_move
        partner_id=data.ids[0]

        result_selection=model_wizard.result_selection

        if result_selection == 'supplier':
            ACCOUNT_TYPE = ['payable']
        elif result_selection == 'customer':
            ACCOUNT_TYPE = ['receivable']
        else:
            ACCOUNT_TYPE = ['payable','receivable']

        self._cr.execute(
            "SELECT a.id " \
            "FROM account_account a " \
            "LEFT JOIN account_account_type t " \
                "ON (a.type=t.code) " \
                'WHERE a.type IN %s' \
                "AND a.active", (tuple(ACCOUNT_TYPE), ))

        account_ids = [a for (a,) in self._cr.fetchall()]
        if target_move == 'posted':
            move_state = ['posted']
        reconcil = True
        if model_wizard.filter == 'unreconciled':
            reconcil = False
        if reconcil:
            RECONCILE_TAG = " "
        else:
            RECONCILE_TAG = "AND l.reconcile_id IS NULL"

        fiscalyear=self.env['account.partner.report.poi'].browse(id_wizard).fiscalyear_id.id
        init_query="l.state <> 'draft' AND l.period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN ("+str(fiscalyear)+"))  AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')"
        self._cr.execute(
            "SELECT COALESCE(SUM(l.debit),0.0), COALESCE(SUM(l.credit),0.0), COALESCE(sum(debit-credit), 0.0) " \
            "FROM account_move_line AS l,  " \
            "account_move AS m "
            "WHERE l.partner_id = %s " \
            "AND m.id = l.move_id " \
            "AND m.state IN %s "
            "AND account_id IN %s" \
            " " + RECONCILE_TAG + " "\
            "AND " + init_query + "  ",
            (partner_id, tuple(move_state), tuple(account_ids)))
        res = self._cr.fetchall()
        init_bal_sum = res[0][2]
        return res

    def _sum_debit_partner(self, data):
        move_state = ['draft','posted']
        partner_id=data.ids[0]
        obj_partner = self.pool.get('res.partner')
        id_wizard=data._context['active_id']
        model_wizard=self.env['account.partner.report.poi'].browse(id_wizard)

        target_move=model_wizard.target_move
        if target_move == 'posted':
            move_state = ['posted']

        result_selection=model_wizard.result_selection

        if result_selection == 'supplier':
            ACCOUNT_TYPE = ['payable']
        elif result_selection == 'customer':
            ACCOUNT_TYPE = ['receivable']
        else:
            ACCOUNT_TYPE = ['payable','receivable']

        self._cr.execute(
            "SELECT a.id " \
            "FROM account_account a " \
            "LEFT JOIN account_account_type t " \
                "ON (a.type=t.code) " \
                'WHERE a.type IN %s' \
                "AND a.active", (tuple(ACCOUNT_TYPE), ))

        account_ids = [a for (a,) in self._cr.fetchall()]
        params = [tuple(move_state), tuple(account_ids)]

        PARTNER_REQUEST = ''
        if (data._model == 'res.partner') and data.ids[0]:
            PARTNER_REQUEST =  "AND l.partner_id IN %s"
            params += [tuple(data.ids[0])]

        self._cr.execute(
                "SELECT DISTINCT l.partner_id " \
                "FROM account_move_line AS l, account_account AS account, " \
                " account_move AS am " \
                "WHERE l.partner_id IS NOT NULL " \
                    "AND l.account_id = account.id " \
                    "AND am.id = l.move_id " \
                    "AND am.state IN %s"
#                    "AND " + self.query +" " \
                    "AND l.account_id IN %s " \
                    " " + PARTNER_REQUEST + " " \
                    "AND account.active ", params)

        partner_ids = [res['partner_id'] for res in self._cr.dictfetchall()]
        objects = obj_partner.browse(self._cr, self._uid, partner_ids)
        #objects = sorted(objects, key=lambda x: (x.ref, x.name))

        result_tmp = 0.0
        result_init = 0.0
        reconcil = True
        initial_balance = model_wizard.initial_balance
        if model_wizard.filter == 'unreconciled':
            reconcil = False
        if reconcil:
            RECONCILE_TAG = " "
        else:
            RECONCILE_TAG = "AND reconcile_id IS NULL"

        filtro=self.env['account.partner.report.poi'].browse(id_wizard).filter
        condicion_fecha=" "
        condicion_periodo=" "
        date_from= self.env['account.partner.report.poi'].browse(id_wizard).date_from
        date_to = self.env['account.partner.report.poi'].browse(id_wizard).date_to


        if date_from != False and date_to != False and filtro=='filter_date':
            condicion_fecha="AND l.date>='"+date_from+"' AND l.date<= '"+date_to+"'"
        else:
            condicion_fecha=" "

        periodo_from=self.env['account.partner.report.poi'].browse(id_wizard).period_from.date_start

        periodo_to=self.env['account.partner.report.poi'].browse(id_wizard).period_to.date_stop


        if periodo_from != False and periodo_to != False and filtro=='filter_period':
            condicion_periodo="AND (l.date BETWEEN '"+str(periodo_from)+"' AND '"+str(periodo_to)+"')"
        else:
            condicion_periodo=" "


        fiscalyear=self.env['account.partner.report.poi'].browse(id_wizard).fiscalyear_id.id
        init_query="l.state <> 'draft' AND l.period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN ("+str(fiscalyear)+"))  AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')"
        if initial_balance:
            self._cr.execute(
                    "SELECT sum(debit) " \
                    "FROM account_move_line AS l, " \
                    "account_move AS m "
                    "WHERE l.partner_id = %s" \
                        "AND m.id = l.move_id " \
                        "AND m.state IN %s "
                        "AND account_id IN %s" \
                        " " + condicion_fecha + " "\
                        " " + condicion_periodo + " "\
                        " " + RECONCILE_TAG + " " \
                        "AND " + init_query + " ",
                    (partner_id, tuple(move_state), tuple(account_ids)))
            contemp = self._cr.fetchone()
            if contemp != None:
                result_init = contemp[0] or 0.0
            else:
                result_init = result_tmp + 0.0


        self._cr.execute(
                "SELECT sum(debit) " \
                "FROM account_move_line AS l, " \
                "account_move AS m "
                "WHERE l.partner_id = %s " \
                    "AND m.id = l.move_id " \
                    "AND m.state IN %s "
                    "AND account_id IN %s" \
                    " " + condicion_fecha + " "\
                    " " + condicion_periodo + " "\
                    " " + RECONCILE_TAG + " " \
                    "AND " + init_query + " ",
                (partner_id, tuple(move_state), tuple(account_ids),))

        contemp = self._cr.fetchone()
        if contemp != None:
            result_tmp = contemp[0] or 0.0
        else:
            result_tmp = result_tmp + 0.0

        return result_tmp  + result_init

    def _sum_credit_partner(self, data):
        move_state = ['draft','posted']
        partner_id=data.ids[0]
        obj_partner = self.pool.get('res.partner')
        id_wizard=data._context['active_id']
        model_wizard=self.env['account.partner.report.poi'].browse(id_wizard)

        target_move=model_wizard.target_move
        move_state = ['draft','posted']
        if target_move == 'posted':
            move_state = ['posted']


        result_selection=model_wizard.result_selection

        if result_selection == 'supplier':
            ACCOUNT_TYPE = ['payable']
        elif result_selection == 'customer':
            ACCOUNT_TYPE = ['receivable']
        else:
            ACCOUNT_TYPE = ['payable','receivable']

        self._cr.execute(
            "SELECT a.id " \
            "FROM account_account a " \
            "LEFT JOIN account_account_type t " \
                "ON (a.type=t.code) " \
                'WHERE a.type IN %s' \
                "AND a.active", (tuple(ACCOUNT_TYPE), ))

        account_ids = [a for (a,) in self._cr.fetchall()]
        params = [tuple(move_state), tuple(account_ids)]

        PARTNER_REQUEST = ''
        if (data._model == 'res.partner') and data.ids[0]:
            PARTNER_REQUEST =  "AND l.partner_id IN %s"
            params += [tuple(data.ids[0])]

        self._cr.execute(
                "SELECT DISTINCT l.partner_id " \
                "FROM account_move_line AS l, account_account AS account, " \
                " account_move AS am " \
                "WHERE l.partner_id IS NOT NULL " \
                    "AND l.account_id = account.id " \
                    "AND am.id = l.move_id " \
                    "AND am.state IN %s"
#                    "AND " + self.query +" " \
                    "AND l.account_id IN %s " \
                    " " + PARTNER_REQUEST + " " \
                    "AND account.active ", params)

        partner_ids = [res['partner_id'] for res in self._cr.dictfetchall()]
        objects = obj_partner.browse(self._cr, self._uid, partner_ids)
        #objects = sorted(objects, key=lambda x: (x.ref, x.name))

        result_tmp = 0.0
        result_init = 0.0
        reconcil = True
        initial_balance = model_wizard.initial_balance
        if model_wizard.filter == 'unreconciled':
            reconcil = False
        if reconcil:
            RECONCILE_TAG = " "
        else:
            RECONCILE_TAG = "AND reconcile_id IS NULL"

        filtro=self.env['account.partner.report.poi'].browse(id_wizard).filter
        condicion_fecha=" "
        condicion_periodo=" "
        date_from= self.env['account.partner.report.poi'].browse(id_wizard).date_from
        date_to = self.env['account.partner.report.poi'].browse(id_wizard).date_to


        if date_from != False and date_to != False and filtro=='filter_date':
            condicion_fecha="AND l.date>='"+date_from+"' AND l.date<= '"+date_to+"'"
        else:
            condicion_fecha=" "

        periodo_from=self.env['account.partner.report.poi'].browse(id_wizard).period_from.date_start

        periodo_to=self.env['account.partner.report.poi'].browse(id_wizard).period_to.date_stop


        if periodo_from != False and periodo_to != False and filtro=='filter_period':
            condicion_periodo="AND (l.date BETWEEN '"+str(periodo_from)+"' AND '"+str(periodo_to)+"')"
        else:
            condicion_periodo=" "

        fiscalyear=self.env['account.partner.report.poi'].browse(id_wizard).fiscalyear_id.id
        init_query="l.state <> 'draft' AND l.period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN ("+str(fiscalyear)+"))  AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')"
        if initial_balance:
            self._cr.execute(
                    "SELECT sum(credit) " \
                    "FROM account_move_line AS l, " \
                    "account_move AS m  "
                    "WHERE l.partner_id = %s" \
                        "AND m.id = l.move_id " \
                        "AND m.state IN %s "
                        "AND account_id IN %s" \
                        " " + condicion_fecha + " "\
                        " " + condicion_periodo + " "\
                        " " + RECONCILE_TAG + " " \
                        "AND " + init_query + " ",
                    (partner_id, tuple(move_state), tuple(account_ids)))
            contemp = self._cr.fetchone()
            if contemp != None:
                result_init = contemp[0] or 0.0
            else:
                result_init = result_tmp + 0.0

        self._cr.execute(
                "SELECT sum(credit) " \
                "FROM account_move_line AS l, " \
                "account_move AS m "
                "WHERE l.partner_id=%s " \
                    "AND m.id = l.move_id " \
                    "AND m.state IN %s "
                    "AND account_id IN %s" \
                    " " + condicion_fecha + " "\
                    " " + condicion_periodo + " "\
                    " " + RECONCILE_TAG + " " \
                    "AND " + init_query + " ",
                (partner_id, tuple(move_state), tuple(account_ids),))

        contemp = self._cr.fetchone()
        if contemp != None:
            result_tmp = contemp[0] or 0.0
        else:
            result_tmp = result_tmp + 0.0
        return result_tmp  + result_init

    def _get_partners(self, data):
        # TODO: deprecated, to remove in trunk
        model_wizard=self.env['account.partner.report.poi'].browse(id_wizard)
        result_selection=model_wizard.result_selection
        if result_selection == 'customer':
            return _('Receivable Accounts')
        elif result_selection == 'supplier':
            return _('Payable Accounts')
        elif result_selection == 'customer_supplier':
            return _('Receivable and Payable Accounts')
        return ''

    def _sum_currency_amount_account(self, account, form):
        #self._set_get_account_currency_code(account.id)
        self._cr.execute("SELECT sum(aml.amount_currency) FROM account_move_line as aml,res_currency as rc WHERE aml.currency_id = rc.id AND aml.account_id= %s ", (account.id,))
        total = self._cr.fetchone()
        if self.account_currency:
            return_field = str(total[0]) + self.account_currency
            return return_field
        else:
            currency_total = self.tot_currency = 0.0
            return currency_total

    def _display_initial_balance(self, data):
        id_wizard=data._context['active_id']
        model_wizard=self.env['account.partner.report.poi'].browse(id_wizard)
        initial_balance=model_wizard.initial_balance
        if initial_balance:
            return True
        return False

    def _display_currency(self, data):
        id_wizard=data._context['active_id']
        model_wizard=self.env['account.partner.report.poi'].browse(id_wizard)
        amount_currency=model_wizard.amount_currency
        if amount_currency:
            return True
        return False

    ####

    def _sum_debit(self, period_id=False, journal_id=False):
        if journal_id and isinstance(journal_id, int):
            journal_id = [journal_id]
        if period_id and isinstance(period_id, int):
            period_id = [period_id]
        if not journal_id:
            journal_id = self.journal_ids
        if not period_id:
            period_id = self.period_ids
        if not (period_id and journal_id):
            return 0.0
        self.cr.execute('SELECT SUM(debit) FROM account_move_line l '
                        'WHERE period_id IN %s AND journal_id IN %s ' + self.query_get_clause + ' ',
                        (tuple(period_id), tuple(journal_id)))
        return self.cr.fetchone()[0] or 0.0

    def _sum_credit(self, period_id=False, journal_id=False):
        if journal_id and isinstance(journal_id, int):
            journal_id = [journal_id]
        if period_id and isinstance(period_id, int):
            period_id = [period_id]
        if not journal_id:
            journal_id = self.journal_ids
        if not period_id:
            period_id = self.period_ids
        if not (period_id and journal_id):
            return 0.0
        self.cr.execute('SELECT SUM(credit) FROM account_move_line l '
                        'WHERE period_id IN %s AND journal_id IN %s '+ self.query_get_clause+'',
                        (tuple(period_id), tuple(journal_id)))
        return self.cr.fetchone()[0] or 0.0

    def _get_start_date(self, data):
        if data.get('form', False) and data['form'].get('date_from', False):
            return data['form']['date_from']
        return ''

    def _get_target_move(self, data):
        if data.get('form', False) and data['form'].get('target_move', False):
            if data['form']['target_move'] == 'all':
                return _('All Entries')
            return _('All Posted Entries')
        return ''

    def _get_end_date(self, data):
        if data.get('form', False) and data['form'].get('date_to', False):
            return data['form']['date_to']
        return ''

    def get_start_period(self, data):
        if data.get('form', False) and data['form'].get('period_from', False):
            return self.pool.get('account.period').browse(self.cr,self.uid,data['form']['period_from']).name
        return ''

    def get_end_period(self, data):
        if data.get('form', False) and data['form'].get('period_to', False):
            return self.pool.get('account.period').browse(self.cr, self.uid, data['form']['period_to']).name
        return ''

    def _get_account(self, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['chart_account_id']).name
        return ''

    def _get_sortby(self, data):
        raise (_('Error!'), _('Not implemented.'))

    def _get_filter(self, data):
        if data.get('form', False) and data['form'].get('filter', False):
            if data['form']['filter'] == 'filter_date':
                return self._translate('Date')
            elif data['form']['filter'] == 'filter_period':
                return self._translate('Periods')
        return self._translate('No Filters')

    def _sum_debit_period(self, period_id, journal_id=None):
        journals = journal_id or self.journal_ids
        if not journals:
            return 0.0
        self.cr.execute('SELECT SUM(debit) FROM account_move_line l '
                        'WHERE period_id=%s AND journal_id IN %s '+ self.query_get_clause +'',
                        (period_id, tuple(journals)))

        return self.cr.fetchone()[0] or 0.0

    def _sum_credit_period(self, period_id, journal_id=None):
        journals = journal_id or self.journal_ids
        if not journals:
            return 0.0
        self.cr.execute('SELECT SUM(credit) FROM account_move_line l '
                        'WHERE period_id=%s AND journal_id IN %s ' + self.query_get_clause +' ',
                        (period_id, tuple(journals)))
        return self.cr.fetchone()[0] or 0.0

    def _get_fiscalyear(self, data):
        if data.get('form', False) and data['form'].get('fiscalyear_id', False):
            return self.pool.get('account.fiscalyear').browse(self.cr, self.uid, data['form']['fiscalyear_id']).name
        return ''

    def _get_company(self, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['chart_account_id']).company_id.name
        return ''

    def _get_journal(self, data):
        codes = []
        if data.get('form', False) and data['form'].get('journal_ids', False):
            self.cr.execute('select code from account_journal where id IN %s',(tuple(data['form']['journal_ids']),))
            codes = [x for x, in self.cr.fetchall()]
        return codes

    def _get_currency(self, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['chart_account_id']).company_id.currency_id.symbol
        return ''




