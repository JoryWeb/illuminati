
from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'


    @api.multi
    def action_open_origin(self):
        '''
        Buscar y verificar los origenes de un asiento contable
        '''
        src = self.src
        obj, id = src.split(',')
        inv_ids = []
        if obj == 'account.voucher':
            voucher_obj = self.env['account.voucher'].browse(int(id))
            if voucher_obj.voucher_type == 'purchase':
                inv_ids.append(int(id))
                action = self.env.ref('account_voucher.action_purchase_receipt')
                result = action.read()[0]
                if len(inv_ids) != 1:
                    result['domain'] = "[('id', 'in', [" + ','.join(map(str, inv_ids)) + "])]"
                elif len(inv_ids) == 1:
                    res = self.env.ref('account_voucher.view_purchase_receipt_form', False)
                    result['views'] = [(res and res.id or False, 'form')]
                    result['res_id'] = inv_ids[0]
                return result
            else:
                inv_ids.append(int(id))
                action = self.env.ref('account_voucher.action_sale_receipt')
                result = action.read()[0]
                if len(inv_ids) != 1:
                    result['domain'] = "[('id', 'in', [" + ','.join(map(str, inv_ids)) + "])]"
                elif len(inv_ids) == 1:
                    res = self.env.ref('account_voucher.view_sale_receipt_form', False)
                    result['views'] = [(res and res.id or False, 'form')]
                    result['res_id'] = inv_ids[0]
                return result
        else:
            return super(AccountMove, self).action_open_origin()


