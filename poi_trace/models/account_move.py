
from odoo import models, fields, api, _
from odoo.osv import osv
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.one
    @api.depends('src')
    def _is_automove(self):
        if self.src:
            self.automove = True
        else:
            self.automove = False

    src = fields.Char(string='Source')
    automove = fields.Boolean(string='Automove', readonly=True, compute='_is_automove')
    fixable_automatic_asset = fields.Boolean(string='Fixable Automatic Asset', default=False, copy=False,
                                             help='This is going to be enabled if the asset needs to be modified.')
    copy_id = fields.Many2one('account.move', string='Copied from', help="Account entry from which it was copied")

    @api.multi
    def add_source(self, model, res_id):
        self.write({'src': str(model) + ',' + str(res_id)})
        return True

    # THIS IS JUST A TEMPORARY FIX ON PAYMENTS
    @api.multi
    def make_fixable(self):
        self.write({'fixable_automatic_asset': True})
        return True

    # THIS IS JUST A TEMPORARY FIX ON PAYMENTS
    @api.multi
    def make_unfixable(self):
        self.write({'fixable_automatic_asset': False})
        return True

    @api.multi
    def button_cancel(self):
        for move in self:
            if move.automove and not move.fixable_automatic_asset:
                raise osv.except_osv(_('Error!'),
                                     _('You cannot modify an automatic entry.\nOtherwise you can revert it.'))
        return super(AccountMove, self).button_cancel()

    @api.multi
    def unlink(self):
        for move in self:
            if move.automove and not move.fixable_automatic_asset:
                raise osv.except_osv(_('User Error!'),
                                     _('You cannot delete an automatic entry "%s".') % \
                                     move['name'])
        return super(AccountMove, self).unlink()

    def create_reverse_asset(self, move, type='revert'):
        reversed_move_id = None
        reversed_move_id = self.copy(move.id, default={'src': ''})

        if reversed_move_id:
            reversed_obj = self.browse(reversed_move_id)
            # We are going to keep the relation with object and allow the user to fix their assets
            reversed_obj.write({'src': move.src, 'fixable_automatic_asset': True,
                                'ref': move.ref and move.ref + _(' (reverted)') or move.name + _(' (reverted)')})
            for line in reversed_obj.line_id:
                if type == 'revert':
                    line.write({'credit': line.debit, 'debit': line.credit})
                else:
                    line.write({'credit': 0.0, 'debit': 0.0})
        return reversed_move_id

    @api.multi
    def revert_asset(self, type='revert'):
        """
        :param type: Type can be "revert" or "fix".
        revert: Create a new move with all the lines (debit -> credit AND credit -> debit)
        fix: Create a new move with all the lines in zero
        """
        reversed_ids = []
        for move in self.browse():
            reversed_id = self.create_reverse_asset(move, type=type)
            reversed_ids.append(reversed_id)

        return reversed_ids

    @api.multi
    def copy(self, default=None):
        # Registrar el id original del cual se copio
        default['copy_id'] = self.id
        return super(AccountMove, self.with_context(dont_create_taxes=True)).copy(default)

    @api.multi
    def reverse_moves(self, date=None, journal_id=None):
        # Copiar origen src cuando se vuelca un Asiento

        reversed_moves = super(AccountMove, self).reverse_moves(date=date, journal_id=journal_id)

        to_reconcile_lines = self.env['account.move.line']
        for rev in self.browse(reversed_moves):
            # Escribir origen
            rev.write({'src': rev.copy_id.src})
            # Conciliar las cuentas que sean conciliables y que no hayan sido conciliadas nativamente
            rev_lines = rev.line_ids.filtered(lambda r: not r.reconciled and r.account_id.reconcile)
            to_reconcile_lines += rev_lines
            copy_lines = rev.copy_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.reconcile)
            to_reconcile_lines += copy_lines

            if to_reconcile_lines:
                to_reconcile_lines.reconcile()

        return reversed_moves

    @api.multi
    def action_open_origin(self):
        '''
        Buscar y verificar los origenes de un asiento contable
        '''
        src = self.src
        obj, id = src.split(',')
        inv_ids = []
        if obj == 'account.invoice':
            inv_ids.append(int(id))
            action = self.env.ref('account.action_invoice_tree2')
            result = action.read()[0]
            if len(inv_ids) != 1:
                result['domain'] = "[('id', 'in', [" + ','.join(map(str, inv_ids)) + "])]"
            elif len(inv_ids) == 1:
                res = self.env.ref('account.invoice_supplier_form', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = inv_ids[0]
            return result

        elif obj == 'account.payment':
            inv_ids.append(int(id))
            action = self.env.ref('account.action_account_payments')
            result = action.read()[0]
            if len(inv_ids) != 1:
                result['domain'] = "[('id', 'in', [" + ','.join(map(str, inv_ids)) + "])]"
            elif len(inv_ids) == 1:
                res = self.env.ref('account.view_account_payment_form', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = inv_ids[0]
            return result

        elif obj == 'account.bank.statement.line':
            inv_ids.append(int(id))
            action = self.env.ref('account.action_bank_statement_line')
            result = action.read()[0]
            if len(inv_ids) != 1:
                result['domain'] = "[('id', 'in', [" + ','.join(map(str, inv_ids)) + "])]"
            elif len(inv_ids) == 1:
                res = self.env.ref('account.view_bank_statement_line_form', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = inv_ids[0]
            return result


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def unlink(self):
        for line in self:
            if line.move_id.automove and not line.move_id.fixable_automatic_asset:
                raise osv.except_osv(_('User Error!'),
                                     _('You cannot delete any line of an automatic entry "%s".') % \
                                     line.move_id['name'])
        return super(AccountMoveLine, self).unlink()

    def _restricted_keys(self):
        # Inherit and add more fields in case that you don't want them to be edited.
        restricted_keys = ['name', 'credit', 'debit', 'ref', 'account_id', 'partner_id', 'analytic_account_id']
        return restricted_keys

    @api.multi
    def write(self, vals):
        for line in self:
            if line.move_id.automove and line.move_id.state != 'draft' and not (
                    line.move_id.fixable_automatic_asset or line.move_id.copy_id.fixable_automatic_asset):
                for field, fill in vals.iteritems():
                    if field in self._restricted_keys():
                        raise UserError(_('You cannot edit any line of an automatic entry "%s".') % \
                                        line.move_id['name'])

        return super(AccountMoveLine, self).write(vals)

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        move_objs = [x.move_id for x in self]
        # TODO: SIMPLIFY
        # move_objs.make_fixable()
        for move in move_objs:
            move.make_fixable()
        res = super(AccountMoveLine, self).reconcile(writeoff_acc_id=writeoff_acc_id,
                                                     writeoff_journal_id=writeoff_journal_id)

        # move_objs.make_unfixable()
        for move in move_objs:
            move.make_unfixable()
        return res

    src = fields.Char(string='Source', copy=False)
