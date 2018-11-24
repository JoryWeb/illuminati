# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import api
from openerp.exceptions import UserError


class product_template(osv.osv):
    _inherit = 'product.template'

    # To remove in master because this function is now used on "product.product" model.
    def do_change_standard_price(self, cr, uid, ids, new_price, context=None):
        """ Changes the Standard Price of Product and creates an account move accordingly."""
        location_obj = self.pool.get('stock.location')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        user_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        loc_ids = location_obj.search(cr, uid, [('usage', '=', 'internal'), ('company_id', '=', user_company_id)])
        for rec_id in ids:
            datas = self.get_product_accounts(cr, uid, rec_id, context=context)
            for location in location_obj.browse(cr, uid, loc_ids, context=context):
                c = context.copy()
                c.update({'location': location.id, 'compute_child': False})
                product = self.browse(cr, uid, rec_id, context=c)

                diff = product.standard_price - new_price
                if not diff:
                    raise UserError(_("No difference between standard price and new price!"))
                for prod_variant in product.product_variant_ids:
                    qty = prod_variant.qty_available
                    if qty:
                        # Accounting Entries
                        amount_diff = abs(diff * qty)
                        if diff * qty > 0:
                            debit_account_id = datas['expense'].id
                            credit_account_id = datas['stock_valuation'].id
                        else:
                            debit_account_id = datas['stock_valuation'].id
                            credit_account_id = datas['expense'].id

                        lines = [(0, 0, {'name': _('Standard Price changed'),
                                        'account_id': debit_account_id,
                                        'debit': amount_diff,
                                        'credit': 0,
                                        }),
                                 (0, 0, {
                                        'name': _('Standard Price changed'),
                                        'account_id': credit_account_id,
                                        'debit': 0,
                                        'credit': amount_diff,
                                        })]
                        move_vals = {
                            'journal_id': datas['stock_journal'].id,
                            'company_id': location.company_id.id,
                            'line_ids': lines,
                            'src': 'product.template,' + str(rec_id) #Override because this
                        }
                        move_id = move_obj.create(cr, uid, move_vals, context=context)
                        move_obj.post(cr, uid, [move_id], context=context)
            self.write(cr, uid, rec_id, {'standard_price': new_price})
        return True


class product_product(osv.osv):
    _inherit = 'product.product'

    def do_change_standard_price(self, cr, uid, ids, new_price, context=None):
        """ Changes the Standard Price of Product and creates an account move accordingly."""
        location_obj = self.pool.get('stock.location')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        user_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        loc_ids = location_obj.search(cr, uid, [('usage', '=', 'internal'), ('company_id', '=', user_company_id)])
        for rec_id in ids:
            for location in location_obj.browse(cr, uid, loc_ids, context=context):
                c = context.copy()
                c.update({'location': location.id, 'compute_child': False})
                product = self.browse(cr, uid, rec_id, context=c)
                datas = self.pool['product.template'].get_product_accounts(cr, uid, product.product_tmpl_id.id, context=context)
                diff = product.standard_price - new_price
                if not diff:
                    raise UserError(_("No difference between standard price and new price!"))
                qty = product.qty_available
                if qty:
                    # Accounting Entries
                    amount_diff = abs(diff * qty)
                    if diff * qty > 0:
                        debit_account_id = datas['expense'].id
                        credit_account_id = datas['stock_valuation'].id
                    else:
                        debit_account_id = datas['stock_valuation'].id
                        credit_account_id = datas['expense'].id

                    lines = [(0, 0, {'name': _('Standard Price changed'),
                                    'account_id': debit_account_id,
                                    'debit': amount_diff,
                                    'credit': 0,
                                    }),
                             (0, 0, {
                                    'name': _('Standard Price changed'),
                                    'account_id': credit_account_id,
                                    'debit': 0,
                                    'credit': amount_diff,
                                    })]
                    move_vals = {
                        'journal_id': datas['stock_journal'].id,
                        'company_id': location.company_id.id,
                        'line_ids': lines,
                        'src': 'product.product,'+str(rec_id) #Override because this
                    }
                    move_id = move_obj.create(cr, uid, move_vals, context=context)
                    move_obj.post(cr, uid, [move_id], context=context)
            self.write(cr, uid, rec_id, {'standard_price': new_price})
        return True
