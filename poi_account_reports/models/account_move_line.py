# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from itertools import groupby


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"

    expected_pay_date = fields.Date('Expected Payment Date', help="Expected payment date as manually set through the customer statement (e.g: if you had the customer on the phone and want to remember the date he promised he would pay)")
    internal_note = fields.Text('Internal Note', help="Note you can set through the customer statement about a receivable journal item")
    next_action_date = fields.Date('Next Action Date', help="Date where the next action should be taken for a receivable item. Usually, automatically set when sending reminders through the customer statement.")

    def _compute_fields(self, field_names, group_by=None):
        """ Computes the required fields with the options given in the context using _query_get()
            @param field_names: a list of the fields to compute
            @returns : a dictionnary that has for each aml in the domain a dictionnary of the values of the fields
        """
        if len(self) == 0:
            return []
        select = ','.join(['\"account_move_line\".' + k + ((self.env.context.get('cash_basis') and k in ['balance', 'credit', 'debit']) and '_cash_basis' or '') for k in field_names])
        tables, where_clause, where_params = self._query_get()

        if (self.env.context.get('sum_if_pos') or self.env.context.get('sum_if_neg')) and group_by:
            sql = "SELECT account_move_line.id,account_move_line." + group_by + " as " + group_by + "," + select + " FROM " + tables + " WHERE " + where_clause + " AND account_move_line.id IN %s GROUP BY account_move_line.id"
            where_params += [tuple(self.ids)]
            self.env.cr.execute(sql, where_params)
            ret = {}
            results = self.env.cr.fetchall()
            results = [(dict([(field_names[i], l) for i, l in enumerate(k[2:])] + [('groupby', k[1]), ('id', k[0])])) for k in results]
            results = sorted(results, key=lambda r: r['groupby'])
            for groupby_value, values in groupby(results, key=lambda r: r['groupby']):
                values = list(values)
                total = sum([k['balance'] for k in values])
                if (total > 0 and self.env.context.get('sum_if_pos')) or (total < 0 and self.env.context.get('sum_if_neg')):
                    values = dict([k['id'], k] for k in values)
                    ret.update(values)
            return ret

        sql = "SELECT account_move_line.id," + select + " FROM " + tables + " WHERE " + where_clause + " AND account_move_line.id IN %s GROUP BY account_move_line.id"

        where_params += [tuple(self.ids)]
        self.env.cr.execute(sql, where_params)
        results = self.env.cr.fetchall()
        results = dict([(k[0], dict([(field_names[i], j) for i, j in enumerate(k[1:])])) for k in results])
        return results

    @api.multi
    def get_model_id_and_name(self):
        """Function used to display the right action on journal items on dropdown lists, in reports like general ledger"""
        if self.statement_id:
            return ['account.bank.statement', self.statement_id.id, _('View Bank Statement'), False]
        if self.payment_id:
            return ['account.payment', self.payment_id.id, _('View Payment'), False]
        if self.invoice_id:
            view_id = self.invoice_id.get_formview_id()
            return ['account.invoice', self.invoice_id.id, _('View Invoice'), view_id]
        return ['account.move', self.move_id.id, _('View Move'), False]

    @api.multi
    def write_blocked(self, blocked):
        """ This function is used to change the 'blocked' status of an aml.
            You need to be able to change it even if you're an account user and the aml is locked by the lock date
            (this function is used in the customer statements) """
        if self.env.user in self.env.ref('account.group_account_user').users:
            return self.sudo().write({'blocked': blocked})
        return self.write({'blocked': blocked})
