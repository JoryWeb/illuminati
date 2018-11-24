from odoo import models, fields, api
from odoo.tools.translate import _

class AccountMoveAssetReversal(models.TransientModel):
    """
    Account move reversal wizard, it cancel an account move by reversing it.
    """
    _name = 'account.move.asset.reversal'
    _description = 'Account move reversal'

    @api.model
    def _default_account_moves(self):
        move_ids = []
        self._cr.execute("""select move_id from account_asset_value where move_id is not null group by move_id""")
        res = self._cr.dictfetchall()
        for r in res:
            move_ids.append(r['move_id'])
        return move_ids

    date = fields.Date(string='Fecha Reversión', default=fields.Date.context_today, required=True)
    move_id = fields.Many2one('account.move', string='Asiento contable', required=True)
    journal_id = fields.Many2one('account.journal', string='Diario Especifico', help='If empty, uses the journal of the journal entry to be reversed.')
    move_ids = fields.Many2many('account.move', default=_default_account_moves, string='Asiento Contables', copy=False)
    @api.multi
    def reverse_moves(self):
        res = self.env['account.move'].browse(self.move_id.id).reverse_moves(self.date, self.journal_id or False)
        asset_val = self.env['account.asset.value'].search([('move_id', '=', self.move_id.id)])
        asset_val.unlink()
        if res:
            return {
                'name': _('Asiento Revertido'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'domain': [('id', 'in', res)],
            }
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('move_id')
    def onchange_move_id(self):
        if self.move_id:
            self.date = self.move_id.date
            self.journal_id = self.move_id.journal_id.id
