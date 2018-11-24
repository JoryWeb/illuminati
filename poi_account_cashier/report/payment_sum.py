
import time
from odoo import api, models, _, exceptions
import logging

_logger = logging.getLogger(__name__)


class ReportPayment(models.AbstractModel):
    _name = 'report.poi_account_cashier.report_payment_template'

    def lines(self, journal_ids, data, ptype):
        domain = ['|', ('journal_id.type', '=', 'cash'), ('payment_type', '=', 'transfer')]

        domain.append(('state', '!=', 'draft'))
        domain.append(('state', '!=', 'cancel'))
        domain.append(('payment_type', '=', ptype))
        if isinstance(journal_ids, int):
            journal_ids = [journal_ids]
            domain.append(('journal_id', 'in', journal_ids))
        if data['form']['date_from']:
            domain.append(('payment_date', '>=', data['form']['date_from']))
        if data['form']['date_to']:
            domain.append(('payment_date', '<=', data['form']['date_to']))
        if data['form']['company_id']:
            domain.append(('company_id', '=', data['form']['company_id'][0]))
        if data['form']['cashier_id']:
            domain.append(('cashier_id', '=', data['form']['cashier_id'][0]))
        if data['form']['analytic_account_id']:
            domain.append(('analytic_account_id', '=', data['form']['analytic_account_id'][0]))

        payments = self.env['account.payment'].search(domain)
        return payments

    def sums(self, journal_ids, data):
        sums = []
        #Obtener datos para la tabla resumen final. Primero el saldo inicial antes de la fecha. Luego la sumatoria de movimientos por cada Diario
        self.env.cr.execute("""SELECT 'SALDO INICIAL' as journal,SUM(caml.amountbs) as amountbs,SUM(caml.amountsec) as amountsec
                                FROM
                                    (SELECT aml.account_id,aml.currency_id,aml.company_currency_id
                                            ,CASE WHEN (aml.currency_id IS NULL OR aml.currency_id=aml.company_currency_id) THEN (aml.debit-aml.credit) ELSE 0 END as amountbs
                                            ,CASE WHEN aml.currency_id!=aml.company_currency_id THEN (aml.amount_currency) ELSE 0 END as amountsec
                                        FROM account_move_line aml INNER JOIN account_account aa ON aml.account_id=aa.id 
                                            INNER JOIN account_journal aj ON aml.journal_id=aj.id LEFT OUTER JOIN account_journal paj ON aml.payment_journal_id=paj.id 
                                            INNER JOIN account_move am on aml.move_id=am.id
                                        WHERE am.state = 'posted' and aml.date < '%s'
                                            AND COALESCE(aml.payment_journal_id,aml.journal_id) IN %s AND aa.internal_type='liquidity' AND COALESCE(paj.type, aj.type)='cash' AND aml.cashier_id = %s
                                    ) AS caml
                            """ % (data['form']['date_from'], tuple(journal_ids), data['form']['cashier_id'][0],));
        sums_inic = self.env.cr.dictfetchall()

        self.env.cr.execute("""SELECT aj.name as journal,SUM(caml.amountbs) as amountbs,SUM(caml.amountsec) as amountsec
                                        FROM
                                            (SELECT aml.account_id,aml.currency_id,aml.company_currency_id,COALESCE(aml.payment_journal_id,aml.journal_id) as journal_id
                                                    ,CASE WHEN (aml.currency_id IS NULL OR aml.currency_id=aml.company_currency_id) THEN (aml.debit-aml.credit) ELSE 0 END as amountbs
                                                    ,CASE WHEN aml.currency_id!=aml.company_currency_id THEN (aml.amount_currency) ELSE 0 END as amountsec
                                                FROM account_move_line aml INNER JOIN account_account aa ON aml.account_id=aa.id 
                                                    INNER JOIN account_journal aj ON aml.journal_id=aj.id LEFT OUTER JOIN account_journal paj ON aml.payment_journal_id=paj.id 
                                                    INNER JOIN account_move am on aml.move_id=am.id
                                                WHERE am.state = 'posted' and aml.date >= '%s' and aml.date <= '%s'
                                                    AND COALESCE(aml.payment_journal_id,aml.journal_id) IN %s AND aa.internal_type='liquidity' AND COALESCE(paj.type, aj.type)='cash' AND aml.cashier_id = %s
                                            ) AS caml
                                        INNER JOIN account_journal aj on caml.journal_id=aj.id
                                        GROUP BY aj.name
                                """ % (data['form']['date_from'],data['form']['date_to'], tuple(journal_ids), data['form']['cashier_id'][0],));
        sums_date = self.env.cr.dictfetchall()

        sums = sums_inic + sums_date
        end_bs = 0.0
        end_sec = 0.0
        for s in sums:
            end_bs += s['amountbs'] or 0.0
            end_sec += s['amountsec'] or 0.0
        sums.append({'journal': 'SALDO FINAL', 'amountbs': end_bs, 'amountsec': end_sec})
        return sums

    def banks(self, journal_ids, data):
        banks = []

        self.env.cr.execute("""SELECT aj.name as journal,SUM(caml.amountbs) as amountbs,SUM(caml.amountsec) as amountsec
                                        FROM
                                            (SELECT aml.account_id,aml.currency_id,aml.company_currency_id,aml.journal_id
                                                    ,CASE WHEN (aml.currency_id IS NULL OR aml.currency_id=aml.company_currency_id) THEN (aml.debit-aml.credit) ELSE 0 END as amountbs
                                                    ,CASE WHEN aml.currency_id!=aml.company_currency_id THEN (aml.amount_currency) ELSE 0 END as amountsec
                                                FROM account_move_line aml INNER JOIN account_account aa ON aml.account_id=aa.id INNER JOIN account_journal aj ON aml.journal_id=aj.id 
                                                    INNER JOIN account_move am on aml.move_id=am.id
                                                WHERE am.state = 'posted' and aml.date >= '%s' and aml.date <= '%s'
                                                    AND COALESCE(aml.payment_journal_id,aml.journal_id) IN %s AND aa.internal_type='liquidity' AND aj.type='bank' AND aml.cashier_id = %s
                                            ) AS caml
                                        INNER JOIN account_journal aj on caml.journal_id=aj.id
                                        GROUP BY aj.name
                                """ % (data['form']['date_from'],data['form']['date_to'], tuple(journal_ids), data['form']['cashier_id'][0],));
        sums_date = self.env.cr.dictfetchall()

        banks = sums_date

        return banks

    def currencies(self, journal_ids, data):
        #Devuelve las monedas dadas por los diarios para
        currs = []
        for journal in self.env['account.journal'].search([]):
            pass

    @api.model
    def get_report_values(self, docids, data=None):
        cases = [{'type': 'outbound', 'desc': 'Egresos'}, {'type': 'inbound', 'desc': 'Ingresos'},
                 {'type': 'transfer', 'desc': 'Traspasos'}]
        res = {}
        for case in cases:
            ptype = case['type']
            try:
                res[ptype] = self.with_context(data['form'].get('used_context', {})).lines(data['form']['journal_ids'],
                                                                                           data, ptype)
            except KeyError:
                raise exceptions.Warning(
                    _('Realice la impresión en la siguiente dirección: Contabilidad > Informe > Informes PDF'))
        sum = []
        sums = self.with_context(data['form'].get('used_context', {})).sums(data['form']['journal_ids'], data)
        banks = self.with_context(data['form'].get('used_context', {})).banks(data['form']['journal_ids'], data)
        currencies = self.with_context(data['form'].get('used_context', {})).currencies(data['form']['journal_ids'],
                                                                                        data)
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('poi_account_cashier.report_payment_template')

        docargs = {
            'report': report,
            'doc_ids': data['form']['journal_ids'],
            'doc_model': self.env['account.journal'],
            'data': data,
            'docs': self.env['account.journal'].browse(data['form']['journal_ids']),
            'time': time,
            'cases': cases,
            'lines': res,
            'sums': sums,
            'banks': banks,
            'currencies': currencies,
        }
        return docargs

    @api.model
    def render_html_DEPREC(self, docids, data=None):

        cases = [{'type':'outbound','desc': 'Egresos'} ,{'type':'inbound','desc': 'Ingresos'},{'type':'transfer','desc': 'Traspasos'}]
        res = {}
        for case in cases:
            ptype = case['type']
            try:
                res[ptype] = self.with_context(data['form'].get('used_context', {})).lines(data['form']['journal_ids'], data, ptype)
            except KeyError:
                raise exceptions.Warning(
                _('Realice la impresión en la siguiente dirección: Contabilidad > Informe > Informes PDF'))
        sum = []
        sums = self.with_context(data['form'].get('used_context', {})).sums(data['form']['journal_ids'], data)
        banks = self.with_context(data['form'].get('used_context', {})).banks(data['form']['journal_ids'], data)
        currencies = self.with_context(data['form'].get('used_context', {})).currencies(data['form']['journal_ids'], data)

        docargs = {
            'doc_ids': data['form']['journal_ids'],
            'doc_model': self.env['account.journal'],
            'data': data,
            'docs': self.env['account.journal'].browse(data['form']['journal_ids']),
            'time': time,
            'cases': cases,
            'lines': res,
            'sums': sums,
            'banks': banks,
            'currencies': currencies,
        }
        return self.env['report'].render('poi_account_cashier.report_payment_template', docargs)
