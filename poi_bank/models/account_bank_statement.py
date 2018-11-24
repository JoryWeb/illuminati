##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2014 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Developed by: Grover Menacho
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
from openerp.exceptions import ValidationError
from openerp.tools import float_compare, float_round
#-from odoo.report import report_sxw
from openerp.tools import float_is_zero
import openerp.addons.decimal_precision as dp
from openerp import osv


class AccountBankStatementReconcile(models.Model):
    _name = 'account.bank.statement.reconcile'

    name = fields.Char('Name')
    move_line_ids = fields.One2many('account.move.line', 'bank_reconcile_id', 'Entry Lines')
    statement_line_ids = fields.One2many('account.bank.statement.line', 'bank_reconcile_id', 'Statement Lines')

    def button_break_reconcile(self, cr, uid, ids, context=None):
        return self.unlink(cr, uid, ids, context=context)


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account')



class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    @api.depends('amount')
    def _compute_amount(self):
        for rec in self:
            if rec.amount < 0.0:
                rec.debit = -rec.amount
                rec.credit = 0.0
            else:
                rec.debit = 0.0
                rec.credit = rec.amount


    def _inverse_amount(self):
        for rec in self:
            if rec.debit > 0.0 and rec.credit == 0.0:
                rec.amount = -rec.debit
            elif rec.debit == 0.0 and rec.credit > 0.0:
                rec.amount = rec.credit
            else:
                rec.amount = 0.0

    name = fields.Char('Transaction Number', required=True)
    transaction_date = fields.Datetime('Transaction Datetime') #Debe reemplazar a date
    transaction_agency = fields.Char('Agency')
    transaction_place = fields.Char('Transaction Place') #Sucursal
    #ref = Descripcion
    #notes = Notas
    debit = fields.Float('Debit', compute=_compute_amount, inverse=_inverse_amount, store=True)
    credit = fields.Float('Credit', compute=_compute_amount, inverse=_inverse_amount, store=True)
    bank_reconcile_id = fields.Many2one('account.bank.statement.reconcile', string='Bank Reconcile')
    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account', related='statement_id.bank_account_id', store=True, readonly=True)
    bank_reconcile_comment = fields.Char('Bank Reconcile Comment')


    def process_bank_reconciliations(self, cr, uid, data, context=None):
        for datum in data:
            self.process_bank_reconciliation(cr, uid, datum[0], datum[1], context=context)

    def process_bank_reconciliation(self, cr, uid, id, mv_line_dicts, context=None):
        """ Creates a move line for each item of mv_line_dicts and for the statement line. Reconcile a new move line with its counterpart_move_line_id if specified. Finally, mark the statement line as reconciled by putting the newly created move id in the column journal_entry_id.

            :param int id: id of the bank statement line
            :param list of dicts mv_line_dicts: move lines to create. If counterpart_move_line_id is specified, reconcile with it
        """
        if context is None:
            context = {}
        st_line = self.browse(cr, uid, id, context=context)
        company_currency = st_line.journal_id.company_id.currency_id
        statement_currency = st_line.journal_id.currency or company_currency
        bs_obj = self.pool.get('account.bank.statement')
        am_obj = self.pool.get('account.move')
        aml_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')

        # Checks
        if st_line.bank_reconcile_id.id:
            raise osv.except_osv(_('Error!'), _('The bank statement line was already reconciled.'))
        for mv_line_dict in mv_line_dicts:
            for field in ['debit', 'credit', 'amount_currency']:
                if field not in mv_line_dict:
                    mv_line_dict[field] = 0.0
            if mv_line_dict.get('counterpart_move_line_id'):
                mv_line = aml_obj.browse(cr, uid, mv_line_dict.get('counterpart_move_line_id'), context=context)
                if mv_line.bank_reconcile_id:
                    raise osv.except_osv(_('Error!'), _('A selected move line was already reconciled.'))

        bank_reconcile_obj = self.pool.get('account.bank.statement.reconcile')
        bank_reconcile_name = (st_line.statement_id.name or st_line.name) + "/" + str(st_line.sequence)
        bank_reconcile_id = bank_reconcile_obj.create(cr, uid, {'name': bank_reconcile_name})
        st_line.write({'bank_reconcile_id': bank_reconcile_id})

        move_created = False

        for mv_line_dict in mv_line_dicts:
            for field in ['debit', 'credit', 'amount_currency']:
                if field not in mv_line_dict:
                    mv_line_dict[field] = 0.0
            if mv_line_dict.get('counterpart_move_line_id'):
                mv_line = aml_obj.browse(cr, uid, mv_line_dict.get('counterpart_move_line_id'), context=context)
                mv_line.write({'bank_reconcile_id': bank_reconcile_id})
                move_created = True

        if not move_created:
            # Create the move
            move_name = (st_line.statement_id.name or st_line.name) + "/" + str(st_line.sequence)
            move_vals = bs_obj._prepare_move(cr, uid, st_line, move_name, context=context)
            move_id = am_obj.create(cr, uid, move_vals, context=context)

            # Create the move line for the statement line
            if st_line.statement_id.currency.id != company_currency.id:
                if st_line.currency_id == company_currency:
                    amount = st_line.amount_currency
                else:
                    ctx = context.copy()
                    ctx['date'] = st_line.date
                    amount = currency_obj.compute(cr, uid, st_line.statement_id.currency.id, company_currency.id,
                                                  st_line.amount, context=ctx)
            else:
                amount = st_line.amount
            bank_st_move_vals = bs_obj._prepare_bank_move_line(cr, uid, st_line, move_id, amount, company_currency.id,
                                                               context=context)
            aml_obj.create(cr, uid, bank_st_move_vals, context=context)
            # Complete the dicts
            st_line_currency = st_line.currency_id or statement_currency
            st_line_currency_rate = st_line.currency_id and (st_line.amount_currency / st_line.amount) or False
            to_create = []
            for mv_line_dict in mv_line_dicts:
                if mv_line_dict.get('is_tax_line'):
                    continue
                mv_line_dict['bank_reconcile_id'] = bank_reconcile_id
                mv_line_dict['ref'] = move_name
                mv_line_dict['move_id'] = move_id
                mv_line_dict['period_id'] = st_line.statement_id.period_id.id
                mv_line_dict['journal_id'] = st_line.journal_id.id
                mv_line_dict['company_id'] = st_line.company_id.id
                mv_line_dict['statement_id'] = st_line.statement_id.id
                if mv_line_dict.get('counterpart_move_line_id'):
                    mv_line = aml_obj.browse(cr, uid, mv_line_dict['counterpart_move_line_id'], context=context)
                    mv_line_dict['partner_id'] = mv_line.partner_id.id or st_line.partner_id.id
                    mv_line_dict['account_id'] = mv_line.account_id.id
                if st_line_currency.id != company_currency.id:
                    ctx = context.copy()
                    ctx['date'] = st_line.date
                    mv_line_dict['amount_currency'] = mv_line_dict['debit'] - mv_line_dict['credit']
                    mv_line_dict['currency_id'] = st_line_currency.id
                    if st_line.currency_id and statement_currency.id == company_currency.id and st_line_currency_rate:
                        debit_at_current_rate = self.pool.get('res.currency').round(cr, uid, company_currency,
                                                                                    mv_line_dict[
                                                                                        'debit'] / st_line_currency_rate)
                        credit_at_current_rate = self.pool.get('res.currency').round(cr, uid, company_currency,
                                                                                     mv_line_dict[
                                                                                         'credit'] / st_line_currency_rate)
                    elif st_line.currency_id and st_line_currency_rate:
                        debit_at_current_rate = currency_obj.compute(cr, uid, statement_currency.id,
                                                                     company_currency.id,
                                                                     mv_line_dict['debit'] / st_line_currency_rate,
                                                                     context=ctx)
                        credit_at_current_rate = currency_obj.compute(cr, uid, statement_currency.id,
                                                                      company_currency.id,
                                                                      mv_line_dict['credit'] / st_line_currency_rate,
                                                                      context=ctx)
                    else:
                        debit_at_current_rate = currency_obj.compute(cr, uid, st_line_currency.id, company_currency.id,
                                                                     mv_line_dict['debit'], context=ctx)
                        credit_at_current_rate = currency_obj.compute(cr, uid, st_line_currency.id, company_currency.id,
                                                                      mv_line_dict['credit'], context=ctx)
                    if mv_line_dict.get('counterpart_move_line_id'):
                        # post an account line that use the same currency rate than the counterpart (to balance the account) and post the difference in another line
                        ctx['date'] = mv_line.date
                        if mv_line.currency_id.id == mv_line_dict['currency_id'] \
                                and float_is_zero(abs(mv_line.amount_currency) - abs(mv_line_dict['amount_currency']),
                                                  precision_rounding=mv_line.currency_id.rounding):
                            debit_at_old_rate = mv_line.credit
                            credit_at_old_rate = mv_line.debit
                        else:
                            debit_at_old_rate = currency_obj.compute(cr, uid, st_line_currency.id, company_currency.id,
                                                                     mv_line_dict['debit'], context=ctx)
                            credit_at_old_rate = currency_obj.compute(cr, uid, st_line_currency.id, company_currency.id,
                                                                      mv_line_dict['credit'], context=ctx)
                        mv_line_dict['credit'] = credit_at_old_rate
                        mv_line_dict['debit'] = debit_at_old_rate
                        if debit_at_old_rate - debit_at_current_rate:
                            currency_diff = debit_at_current_rate - debit_at_old_rate
                            to_create.append(
                                self.get_currency_rate_line(cr, uid, st_line, -currency_diff, move_id, context=context))
                        if credit_at_old_rate - credit_at_current_rate:
                            currency_diff = credit_at_current_rate - credit_at_old_rate
                            to_create.append(
                                self.get_currency_rate_line(cr, uid, st_line, currency_diff, move_id, context=context))
                        if mv_line.currency_id and mv_line_dict['currency_id'] == mv_line.currency_id.id:
                            amount_unreconciled = mv_line.amount_residual_currency
                        else:
                            amount_unreconciled = currency_obj.compute(cr, uid, company_currency.id,
                                                                       mv_line_dict['currency_id'],
                                                                       mv_line.amount_residual, context=ctx)
                        if float_is_zero(mv_line_dict['amount_currency'] + amount_unreconciled,
                                         precision_rounding=mv_line.currency_id.rounding):
                            amount = mv_line_dict['debit'] or mv_line_dict['credit']
                            sign = -1 if mv_line_dict['debit'] else 1
                            currency_rate_difference = sign * (mv_line.amount_residual - amount)
                            if not company_currency.is_zero(currency_rate_difference):
                                exchange_lines = self._get_exchange_lines(cr, uid, st_line, mv_line,
                                                                          currency_rate_difference,
                                                                          mv_line_dict['currency_id'], move_id,
                                                                          context=context)
                                for exchange_line in exchange_lines:
                                    to_create.append(exchange_line)

                    else:
                        mv_line_dict['debit'] = debit_at_current_rate
                        mv_line_dict['credit'] = credit_at_current_rate
                elif statement_currency.id != company_currency.id:
                    # statement is in foreign currency but the transaction is in company currency
                    prorata_factor = (mv_line_dict['debit'] - mv_line_dict['credit']) / st_line.amount_currency
                    mv_line_dict['amount_currency'] = prorata_factor * st_line.amount
                to_create.append(mv_line_dict)
            # If the reconciliation is performed in another currency than the company currency, the amounts are converted to get the right debit/credit.
            # If there is more than 1 debit and 1 credit, this can induce a rounding error, which we put in the foreign exchane gain/loss account.
            if st_line_currency.id != company_currency.id:
                diff_amount = bank_st_move_vals['debit'] - bank_st_move_vals['credit'] \
                              + sum(aml['debit'] for aml in to_create) - sum(aml['credit'] for aml in to_create)
                if not company_currency.is_zero(diff_amount):
                    diff_aml = self.get_currency_rate_line(cr, uid, st_line, diff_amount, move_id, context=context)
                    diff_aml['name'] = _('Rounding error from currency conversion')
                    to_create.append(diff_aml)
            # Create move lines
            move_line_pairs_to_reconcile = []
            for mv_line_dict in to_create:
                counterpart_move_line_id = None  # NB : this attribute is irrelevant for aml_obj.create() and needs to be removed from the dict
                if mv_line_dict.get('counterpart_move_line_id'):
                    counterpart_move_line_id = mv_line_dict['counterpart_move_line_id']
                    del mv_line_dict['counterpart_move_line_id']
                new_aml_id = aml_obj.create(cr, uid, mv_line_dict, context=context)
                if counterpart_move_line_id != None:
                    move_line_pairs_to_reconcile.append([new_aml_id, counterpart_move_line_id])
            # Reconcile
            #for pair in move_line_pairs_to_reconcile:
            #    aml_obj.reconcile_partial(cr, uid, pair, context=context)
            # Mark the statement line as reconciled
            self.write(cr, uid, id, {'journal_entry_id': move_id}, context=context)


    #TODO WORKING FROM HERE

    def get_data_for_bank_reconciliations(self, cr, uid, ids, excluded_ids=None, search_reconciliation_proposition=True,
                                     context=None):
        """ Returns the data required to display a reconciliation, for each statement line id in ids """
        ret = []
        if excluded_ids is None:
            excluded_ids = []

        for st_line in self.browse(cr, uid, ids, context=context):
            reconciliation_data = {}
            if search_reconciliation_proposition:
                #We are replacing this part. We don't want to break the native functionality
                reconciliation_proposition = self.get_bank_reconciliation_proposition(cr, uid, st_line,
                                                                                 excluded_ids=excluded_ids,
                                                                                 context=context)
                for mv_line in reconciliation_proposition:
                    excluded_ids.append(mv_line['id'])
                reconciliation_data['reconciliation_proposition'] = reconciliation_proposition
            else:
                reconciliation_data['reconciliation_proposition'] = []
            st_line = self.get_bank_statement_line_for_reconciliation(cr, uid, st_line, context=context)
            reconciliation_data['st_line'] = st_line
            ret.append(reconciliation_data)

        return ret

    def get_bank_statement_line_for_reconciliation(self, cr, uid, st_line, context=None):
        """ Returns the data required by the bank statement reconciliation widget to display a statement line """
        if context is None:
            context = {}
        statement_currency = st_line.journal_id.currency or st_line.journal_id.company_id.currency_id
        #-rml_parser = report_sxw.rml_parse(cr, uid, 'reconciliation_widget_asl', context=context)

        if st_line.amount_currency and st_line.currency_id:
            amount = st_line.amount_currency
            amount_currency = st_line.amount
            amount_currency_str = amount_currency > 0 and amount_currency or -amount_currency
            amount_currency_str = rml_parser.formatLang(amount_currency_str, currency_obj=statement_currency)
        else:
            amount = st_line.amount
            amount_currency_str = ""
        amount_str = amount
        amount_str = rml_parser.formatLang(amount_str, currency_obj=st_line.currency_id or statement_currency)

        data = {
            'id': st_line.id,
            'ref': st_line.ref,
            'note': st_line.note or "",
            'name': st_line.name,
            'date': st_line.date,
            'amount': amount,
            'amount_str': amount_str,  # Amount in the statement line currency
            'currency_id': st_line.currency_id.id or statement_currency.id,
            'partner_id': st_line.partner_id.id,
            'statement_id': st_line.statement_id.id,
            'account_code': st_line.journal_id.default_debit_account_id.code,
            'account_name': st_line.journal_id.default_debit_account_id.name,
            'partner_name': st_line.partner_id.name,
            'communication_partner_name': st_line.partner_name,
            'amount_currency_str': amount_currency_str,  # Amount in the statement currency
            'has_no_partner': not st_line.partner_id.id,
        }
        if st_line.partner_id.id:
            if amount > 0:
                data['open_balance_account_id'] = st_line.partner_id.property_account_receivable.id
            else:
                data['open_balance_account_id'] = st_line.partner_id.property_account_payable.id

        return data


    #POIESIS: New function to get all the lines on the format that I want!
    def get_bank_reconciliation_lines(self, cr, uid, ids, excluded_ids=None,
                                          search_reconciliation_proposition=True,
                                          context=None):
        """ Returns the data required to display a reconciliation, for each statement line id in ids """
        ret = []
        reconciliation_lines = {
            'unreconciled': [],
            'prereconciled': []
        }
        if excluded_ids is None:
            excluded_ids = []

        for st_line in self.browse(cr, uid, ids, context=context):
            reconciliation_data = {}
            st_line = self.get_bank_statement_line_for_reconciliation(cr, uid, st_line, context=context)
            reconciliation_data['st_line'] = st_line
            ret.append(reconciliation_data)

        #THIS PART IS JUST FOR NOW. WE NEED TO DIVIDE IT
        if ret:
            reconciliation_lines['unreconciled'] = ret

        return reconciliation_lines

    def get_move_line_for_reconciliation(self, cr, uid, move_line, context=None):
        """ Returns the data required by the bank statement reconciliation widget to display a statement line """
        if context is None:
            context = {}
        statement_currency = move_line.move_id.journal_id.currency or move_line.move_id.journal_id.company_id.currency_id
        #-rml_parser = report_sxw.rml_parse(cr, uid, 'reconciliation_widget_asl', context=context)

        move_amount = move_line.debit - move_line.credit

        amount_str = str(move_amount)

        data = {
            'id': move_line.id,
            'ref': move_line.move_id.ref,
            'note': move_line.move_id.narration or "",
            'name': move_line.name,
            'date': move_line.move_id.date,
            'amount': move_amount,
            'amount_str': amount_str,  # Amount in the statement line currency
            'partner_id': move_line.partner_id.id,
            'account_code': move_line.account_id.code,
            'account_name': move_line.account_id.name,
            'partner_name': move_line.partner_id.name,
        }
        return data

    def get_account_move_lines(self, cr, uid, ids, excluded_ids=None, context=None):


        """ Find the move lines that could be used to reconcile a statement line. If count is true, only returns the count.

            :param st_line: the browse record of the statement line
            :param integers list excluded_ids: ids of move lines that should not be fetched
            :param boolean count: just return the number of records
            :param tuples list additional_domain: additional domain restrictions
        """
        mv_line_pool = self.pool.get('account.move.line')

        # Get move lines ; in case of a partial reconciliation, only keep one line (the first whose amount is greater than
        # the residual amount because it is presumably the invoice, which is the relevant item in this situation)
        filtered_lines = []
        reconcile_partial_ids = []

        ret = []
        reconciliation_move_lines = {
            'unreconciled': [],
            'prereconciled': []
        }


        domain = [('id','in',ids)]

        line_ids = mv_line_pool.search(cr, uid, domain,
                                       order="date_maturity asc, id asc", context=context)
        lines = mv_line_pool.browse(cr, uid, line_ids, context=context)
        for line in lines:
            reconciliation_data = {}
            move_line = self.get_move_line_for_reconciliation(cr, uid, line, context=context)
            reconciliation_data['move_line'] = move_line
            ret.append(reconciliation_data)

        # THIS PART IS JUST FOR NOW. WE NEED TO DIVIDE IT
        if ret:
            reconciliation_move_lines['unreconciled'] = ret

        return reconciliation_move_lines


    #TODO WORKING UNTIL HERE


    def _domain_bank_reconciliation_proposition(self, cr, uid, st_line, excluded_ids=None, context=None):
        if excluded_ids is None:
            excluded_ids = []
        domain = [('bank_reconcile_id', '=', False),
                  ('bank_account_id', '!=', False),
                  ('bank_account_id', '=', st_line.bank_account_id.id),
                  ('id', 'not in', excluded_ids), ]
        if st_line.partner_id:
            domain.append(('partner_id', '=', st_line.partner_id.id))
        return domain

    def get_bank_reconciliation_proposition(self, cr, uid, st_line, excluded_ids=None, context=None):
        """ Returns move lines that constitute the best guess to reconcile a statement line. """
        mv_line_pool = self.pool.get('account.move.line')

        # Look for structured communication
        if st_line.name:
            domain = self._domain_bank_reconciliation_proposition(cr, uid, st_line, excluded_ids=excluded_ids,
                                                             context=context)
            match_id = mv_line_pool.search(cr, uid, domain, offset=0, limit=2, context=context)
            if match_id and len(match_id) == 1:
                mv_line_br = mv_line_pool.browse(cr, uid, match_id, context=context)
                target_currency = st_line.currency_id or st_line.journal_id.currency or st_line.journal_id.company_id.currency_id
                mv_line = mv_line_pool.prepare_move_lines_for_bank_reconciliation_widget(cr, uid, mv_line_br,
                                                                                    target_currency=target_currency,
                                                                                    target_date=st_line.date,
                                                                                    context=context)[0]
                mv_line['has_no_partner'] = not bool(st_line.partner_id.id)
                #LINEAS DE MOVIMIENTO, NO TIENE XQ ESCRIBIR PARTNER!!!
                # If the structured communication matches a move line that is associated with a partner, we can safely associate the statement line with the partner
                #if (mv_line['partner_id']):
                #    self.write(cr, uid, st_line.id, {'partner_id': mv_line['partner_id']}, context=context)
                #    mv_line['has_no_partner'] = False
                return [mv_line]

        # How to compare statement line amount and move lines amount
        precision_digits = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        currency_id = st_line.currency_id.id or st_line.journal_id.currency.id
        # NB : amount can't be == 0 ; so float precision is not an issue for amount > 0 or amount < 0
        amount = st_line.amount_currency or st_line.amount
        domain = []
        if currency_id:
            domain += [('currency_id', '=', currency_id)]
        sign = 1  # correct the fact that st_line.amount is signed and debit/credit is not
        amount_field = 'debit'
        if currency_id == False:
            if amount < 0:
                amount_field = 'credit'
                sign = -1
        else:
            amount_field = 'amount_currency'

        # Look for a matching amount
        domain_exact_amount = domain + [
            (amount_field, '=', float_round(sign * amount, precision_digits=precision_digits))]
        domain_exact_amount_ref = domain_exact_amount + [('ref', '=', st_line.ref)]
        match_id = self.get_move_lines_for_bank_reconciliation(cr, uid, st_line, excluded_ids=excluded_ids, offset=0,
                                                          limit=2, additional_domain=domain_exact_amount_ref)
        if not match_id:
            match_id = self.get_move_lines_for_bank_reconciliation(cr, uid, st_line, excluded_ids=excluded_ids, offset=0,
                                                              limit=2, additional_domain=domain_exact_amount)

        if match_id and len(match_id) == 1:
            return match_id

        if not st_line.partner_id.id:
            return []

        # Look for a set of move line whose amount is <= to the line's amount
        if amount > 0:  # Make sure we can't mix receivable and payable
            domain += [('account_id.type', '=', 'receivable')]
        else:
            domain += [('account_id.type', '=', 'payable')]
        if amount_field == 'amount_currency' and amount < 0:
            domain += [(amount_field, '<', 0), (amount_field, '>=', (sign * amount))]
        else:
            domain += [(amount_field, '>', 0), (amount_field, '<=', (sign * amount))]
        mv_lines = self.get_move_lines_for_bank_reconciliation(cr, uid, st_line, excluded_ids=excluded_ids, limit=5,
                                                          additional_domain=domain, context=context)
        ret = []
        total = 0
        for line in mv_lines:
            total += abs(line['debit'] - line['credit'])
            if float_compare(total, abs(amount), precision_digits=precision_digits) != 1:
                ret.append(line)
            else:
                break
        return ret

    def get_move_lines_for_bank_reconciliation_by_statement_line_id(self, cr, uid, st_line_id, excluded_ids=None, str=False,
                                                               offset=0, limit=None, count=False,
                                                               additional_domain=None, context=None):
        """ Bridge between the web client reconciliation widget and get_move_lines_for_bank_reconciliation (which expects a browse record) """
        if excluded_ids is None:
            excluded_ids = []
        if additional_domain is None:
            additional_domain = []
        st_line = self.browse(cr, uid, st_line_id, context=context)
        return self.get_move_lines_for_bank_reconciliation(cr, uid, st_line, excluded_ids, str, offset, limit, count,
                                                      additional_domain, context=context)

    def _domain_move_lines_for_bank_reconciliation(self, cr, uid, st_line, excluded_ids=None, str=False,
                                              additional_domain=None, context=None):
        if excluded_ids is None:
            excluded_ids = []
        if additional_domain is None:
            additional_domain = []
        # Make domain
        domain = additional_domain + [
            ('bank_reconcile_id', '=', False),
            ('bank_account_id', '!=', False),
            ('bank_account_id', '=', st_line.bank_account_id.id)]
        if st_line.partner_id.id:
            domain += [('partner_id', '=', st_line.partner_id.id)]
        if excluded_ids:
            domain.append(('id', 'not in', excluded_ids))
        if str:
            domain += [
                '|', ('move_id.name', 'ilike', str),
                '|', ('move_id.ref', 'ilike', str),
                ('date_maturity', 'like', str),
            ]
            if not st_line.partner_id.id:
                domain.insert(-1, '|', )
                domain.append(('partner_id.name', 'ilike', str))
            if str != '/':
                domain.insert(-1, '|', )
                domain.append(('name', 'ilike', str))
        return domain

    def get_move_lines_for_bank_reconciliation(self, cr, uid, st_line, excluded_ids=None, str=False, offset=0, limit=None,
                                          count=False, additional_domain=None, context=None):
        """ Find the move lines that could be used to reconcile a statement line. If count is true, only returns the count.

            :param st_line: the browse record of the statement line
            :param integers list excluded_ids: ids of move lines that should not be fetched
            :param boolean count: just return the number of records
            :param tuples list additional_domain: additional domain restrictions
        """
        mv_line_pool = self.pool.get('account.move.line')
        domain = self._domain_move_lines_for_bank_reconciliation(cr, uid, st_line, excluded_ids=excluded_ids, str=str,
                                                            additional_domain=additional_domain, context=context)

        # Get move lines ; in case of a partial reconciliation, only keep one line (the first whose amount is greater than
        # the residual amount because it is presumably the invoice, which is the relevant item in this situation)
        filtered_lines = []
        reconcile_partial_ids = []
        actual_offset = offset
        while True:
            line_ids = mv_line_pool.search(cr, uid, domain, offset=actual_offset, limit=limit,
                                           order="date_maturity asc, id asc", context=context)
            lines = mv_line_pool.browse(cr, uid, line_ids, context=context)
            make_one_more_loop = False
            for line in lines:
                if line.reconcile_partial_id and \
                        (line.reconcile_partial_id.id in reconcile_partial_ids or \
                                     abs(line.debit - line.credit) < abs(line.amount_residual)):
                    # if we filtered a line because it is partially reconciled with an already selected line, we must do one more loop
                    # in order to get the right number of items in the pager
                    make_one_more_loop = True
                    continue
                filtered_lines.append(line)
                if line.reconcile_partial_id:
                    reconcile_partial_ids.append(line.reconcile_partial_id.id)

            if not limit or not make_one_more_loop or len(filtered_lines) >= limit:
                break
            actual_offset = actual_offset + limit
        lines = limit and filtered_lines[:limit] or filtered_lines

        # Either return number of lines
        if count:
            return len(lines)

        # Or return list of dicts representing the formatted move lines
        else:
            target_currency = st_line.currency_id or st_line.journal_id.currency or st_line.journal_id.company_id.currency_id
            mv_lines = mv_line_pool.prepare_move_lines_for_bank_reconciliation_widget(cr, uid, lines,
                                                                                 target_currency=target_currency,
                                                                                 target_date=st_line.date,
                                                                                 context=context)
            has_no_partner = not bool(st_line.partner_id.id)
            for line in mv_lines:
                line['has_no_partner'] = has_no_partner
            return mv_lines
