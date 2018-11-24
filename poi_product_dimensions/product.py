##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
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
from openerp.tools.translate import _
from common import rounding
from itertools import chain
from openerp.exceptions import UserError
from openerp import tools
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import time

class product_template(osv.osv):
    _inherit = 'product.template'
    _columns = {
        'metric_type': fields.selection([('lineal', 'Lineal'), ('area', 'Area'), ('volume','Volume')], 'Metric Type'),
        'dimension_ids': fields.many2many('product.dimension', 'product_template_dimension_rel', 'product_id', 'dimension_id', 'Dimensions Allowed'),
    }

class product_pricelist_item(osv.osv):
    _inherit = "product.pricelist.item"
    _columns = {
        'base': fields.selection(
            [('list_price', 'Public Price'), ('standard_price', 'Cost'), ('pricelist', 'Other Pricelist'), ('fixed', 'Fixed amount')],
            string="Based on", required=True,
            help='Base price for computation. \n Public Price: The base price will be the Sale/public Price. \n Cost Price : The base price will be the cost price. \n Other Pricelist : Computation of the base price based on another Pricelist.'),
        'min_metric': fields.float('Min Metric'),
        'max_metric': fields.float('Max Metric'),
        'fixed_amount': fields.float('Fixed Amount'),
        'fixed_per': fields.selection([('quantity','Per UoM'),('metric','Per Metric')], string='Fixed Per', help="Specifies whether the fixed priced is based on the quantified UoM or on the dimension metric."),
    }

    _defaults = {
        'fixed_per': 'metric',
    }

product_pricelist_item()

class product_pricelist(osv.osv):
    _inherit = 'product.pricelist'

    def _price_rule_get_multi(self, cr, uid, pricelist, products_by_qty_by_partner, context=None):
        context = context or {}
        date = context.get('date') and context['date'][0:10] or time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        products = map(lambda x: x[0], products_by_qty_by_partner)
        product_uom_obj = self.pool.get('product.uom')

        if not products:
            return {}

        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = categ_ids.keys()

        is_product_template = products[0]._name == "product.template"
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            # all variants of all products
            prod_ids = [p.id for p in
                        list(chain.from_iterable([t.product_variant_ids for t in products]))]
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

        # Load all rules
            # metric
        if context.get('metric'):
            metric = context.get('metric')
        else:
            metric = False
        # Load all rules
        if metric:
            cr.execute(
                'SELECT i.id '
                'FROM product_pricelist_item AS i '
                'LEFT JOIN product_category AS c '
                'ON i.categ_id = c.id '
                'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = any(%s))'
                'AND (product_id IS NULL OR product_id = any(%s))'
                'AND (categ_id IS NULL OR categ_id = any(%s)) '
                'AND (pricelist_id = %s) '
                'AND ((i.date_start IS NULL OR i.date_start<=%s) AND (i.date_end IS NULL OR i.date_end>=%s))'
                'AND ((min_metric <= %s AND max_metric > %s) OR (max_metric IS NULL and min_metric IS NULL) OR (min_metric = 0 AND max_metric = 0))'
                'ORDER BY applied_on, min_quantity desc, c.parent_left desc',
                (prod_tmpl_ids, prod_ids, categ_ids, pricelist.id, date, date, metric, metric))

            item_ids = [x[0] for x in cr.fetchall()]
            items = self.pool.get('product.pricelist.item').browse(cr, uid, item_ids, context=context)
        else:
            cr.execute(
                'SELECT i.id '
                'FROM product_pricelist_item AS i '
                'LEFT JOIN product_category AS c '
                'ON i.categ_id = c.id '
                'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = any(%s))'
                'AND (product_id IS NULL OR product_id = any(%s))'
                'AND (categ_id IS NULL OR categ_id = any(%s)) '
                'AND (pricelist_id = %s) '
                'AND ((i.date_start IS NULL OR i.date_start<=%s) AND (i.date_end IS NULL OR i.date_end>=%s))'
                'ORDER BY applied_on, min_quantity desc, c.parent_left desc',
                (prod_tmpl_ids, prod_ids, categ_ids, pricelist.id, date, date))

            item_ids = [x[0] for x in cr.fetchall()]
            items = self.pool.get('product.pricelist.item').browse(cr, uid, item_ids, context=context)

        results = {}
        for product, qty, partner in products_by_qty_by_partner:
            results[product.id] = 0.0
            suitable_rule = False

            # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
            # An intermediary unit price may be computed according to a different UoM, in
            # which case the price_uom_id contains that UoM.
            # The final price will be converted to match `qty_uom_id`.
            qty_uom_id = context.get('uom') or product.uom_id.id
            price_uom_id = product.uom_id.id
            qty_in_product_uom = qty
            if qty_uom_id != product.uom_id.id:
                try:
                    qty_in_product_uom = product_uom_obj._compute_qty(
                        cr, uid, context['uom'], qty, product.uom_id.id)
                except UserError:
                    # Ignored - incompatible UoM in context, use default product UoM
                    pass

            # if Public user try to access standard price from website sale, need to call _price_get.
            price = self.pool['product.template']._price_get(cr, uid, [product], 'list_price', context=context)[product.id]

            price_uom_id = qty_uom_id
            for rule in items:
                if rule.min_quantity and qty_in_product_uom < rule.min_quantity:
                    continue
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and not (product.product_variant_count == 1 and product.product_variant_ids[0].id == rule.product_id.id):
                        # product rule acceptable on template if has only one variant
                        continue
                else:
                    if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and product.id != rule.product_id.id:
                        continue

                if rule.categ_id:
                    cat = product.categ_id
                    while cat:
                        if cat.id == rule.categ_id.id:
                            break
                        cat = cat.parent_id
                    if not cat:
                        continue

                if rule.base == 'pricelist' and rule.base_pricelist_id:
                    price_tmp = self._price_get_multi(cr, uid, rule.base_pricelist_id, [(product, qty, partner)], context=context)[product.id]
                    ptype_src = rule.base_pricelist_id.currency_id.id
                    price = self.pool['res.currency'].compute(cr, uid, ptype_src, pricelist.currency_id.id, price_tmp, round=False, context=context)

                elif rule.base == 'fixed' and not rule.base_pricelist_id:
                    if 'fixed_per' in rule and rule['fixed_per'] == 'metric':
                        price_tmp = rule['fixed_amount'] * (metric or 1.0)
                    else:
                        price_tmp = rule['fixed_amount']

                    #price_tmp = self._price_get_multi(cr, uid, rule.base_pricelist_id, [(product, qty, partner)], context=context)[product.id]
                    ptype_src = rule.base_pricelist_id.currency_id.id
                    price = self.pool['res.currency'].compute(cr, uid, ptype_src, pricelist.currency_id.id, price_tmp, round=False, context=context)
                else:
                    # if base option is public price take sale price else cost price of product
                    # price_get returns the price in the context UoM, i.e. qty_uom_id
                    price = self.pool['product.template']._price_get(cr, uid, [product], rule.base, context=context)[product.id]

                convert_to_price_uom = (lambda price: product_uom_obj._compute_price(
                                            cr, uid, product.uom_id.id,
                                            price, price_uom_id))

                if price is not False:
                    if rule.compute_price == 'fixed':
                        price = convert_to_price_uom(rule.fixed_price)
                    elif rule.compute_price == 'percentage':
                        price = (price - (price * (rule.percent_price / 100))) or 0.0
                    else:
                        #complete formula
                        price_limit = price
                        price = (price - (price * (rule.price_discount / 100))) or 0.0
                        if rule.price_round:
                            price = tools.float_round(price, precision_rounding=rule.price_round)

                        if rule.price_surcharge:
                            price_surcharge = convert_to_price_uom(rule.price_surcharge)
                            price += price_surcharge

                        if rule.price_min_margin:
                            price_min_margin = convert_to_price_uom(rule.price_min_margin)
                            price = max(price, price_limit + price_min_margin)

                        if rule.price_max_margin:
                            price_max_margin = convert_to_price_uom(rule.price_max_margin)
                            price = min(price, price_limit + price_max_margin)
                    suitable_rule = rule
                break
            # Final price conversion into pricelist currency
            if suitable_rule and suitable_rule.compute_price != 'fixed' and suitable_rule.base != 'pricelist':
                price = self.pool['res.currency'].compute(cr, uid, product.currency_id.id, pricelist.currency_id.id, price, round=False, context=context)

            results[product.id] = (price, suitable_rule and suitable_rule.id or False)
        return results


    def price_get_multi(self, cr, uid, pricelist_ids, products_by_qty_by_partner, context=None):
        """multi products 'price_get'.
           @param pricelist_ids:
           @param products_by_qty:
           @param partner:
           @param context: {
             'date': Date of the pricelist (%Y-%m-%d),}
           @return: a dict of dict with product_id as key and a dict 'price by pricelist' as value
        """

        def _create_parent_category_list(id, lst):
            if not id:
                return []
            parent = product_category_tree.get(id)
            if parent:
                lst.append(parent)
                return _create_parent_category_list(parent, lst)
            else:
                return lst
        # _create_parent_category_list

        if context is None:
            context = {}

        date = context.get('date') or time.strftime('%Y-%m-%d')

        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.product')
        product_category_obj = self.pool.get('product.category')
        product_uom_obj = self.pool.get('product.uom')
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        price_type_obj = self.pool.get('product.price.type')

        # product.pricelist.version:
        if not pricelist_ids:
            pricelist_ids = self.pool.get('product.pricelist').search(cr, uid, [], context=context)

        pricelist_version_ids = self.pool.get('product.pricelist.version').search(cr, uid, [
                                                        ('pricelist_id', 'in', pricelist_ids),
                                                        '|',
                                                        ('date_start', '=', False),
                                                        ('date_start', '<=', date),
                                                        '|',
                                                        ('date_end', '=', False),
                                                        ('date_end', '>=', date),
                                                    ])
        if len(pricelist_ids) != len(pricelist_version_ids):
            raise osv.except_osv(_('Warning!'), _("At least one pricelist has no active version !\nPlease create or activate one."))

        # product.product:
        product_ids = [i[0] for i in products_by_qty_by_partner]
        #products = dict([(item['id'], item) for item in product_obj.read(cr, uid, product_ids, ['categ_id', 'product_tmpl_id', 'uos_id', 'uom_id'])])
        products = product_obj.browse(cr, uid, product_ids, context=context)
        products_dict = dict([(item.id, item) for item in products])

        # product.category:
        product_category_ids = product_category_obj.search(cr, uid, [])
        product_categories = product_category_obj.read(cr, uid, product_category_ids, ['parent_id'])
        product_category_tree = dict([(item['id'], item['parent_id'][0]) for item in product_categories if item['parent_id']])


        #metric
        if context.get('metric'):
            metric = context.get('metric')
        else:
            metric = False

        results = {}
        for product_id, qty, partner in products_by_qty_by_partner:
            for pricelist_id in pricelist_ids:
                price = False

                tmpl_id = products_dict[product_id].product_tmpl_id and products_dict[product_id].product_tmpl_id.id or False

                categ_id = products_dict[product_id].categ_id and products_dict[product_id].categ_id.id or False
                categ_ids = _create_parent_category_list(categ_id, [categ_id])
                if categ_ids:
                    categ_where = '(categ_id IN (' + ','.join(map(str, categ_ids)) + '))'
                else:
                    categ_where = '(categ_id IS NULL)'

                if partner:
                    partner_where = 'base <> -2 OR %s IN (SELECT name FROM product_supplierinfo WHERE product_id = %s) '
                    partner_args = (partner, tmpl_id)
                else:
                    partner_where = 'base <> -2 '
                    partner_args = ()

                if metric:

                    cr.execute(
                        'SELECT i.*, pl.currency_id '
                        'FROM product_pricelist_item AS i, '
                            'product_pricelist_version AS v, product_pricelist AS pl '
                        'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                            'AND (product_id IS NULL OR product_id = %s) '
                            'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                            'AND (' + partner_where + ') '
                            'AND price_version_id = %s '
                            'AND (min_quantity IS NULL OR min_quantity <= %s) '
                            'AND ((min_metric <= %s AND max_metric > %s) OR (max_metric IS NULL and min_metric IS NULL) OR (min_metric = 0 AND max_metric = 0))'
                            'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                        'ORDER BY sequence',
                        (tmpl_id, product_id) + partner_args + (pricelist_version_ids[0], qty, metric, metric))
                    res1 = cr.dictfetchall()

                else:

                    cr.execute(
                        'SELECT i.*, pl.currency_id '
                        'FROM product_pricelist_item AS i, '
                            'product_pricelist_version AS v, product_pricelist AS pl '
                        'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                            'AND (product_id IS NULL OR product_id = %s) '
                            'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                            'AND (' + partner_where + ') '
                            'AND price_version_id = %s '
                            'AND (min_quantity IS NULL OR min_quantity <= %s) '
                            'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                        'ORDER BY sequence',
                        (tmpl_id, product_id) + partner_args + (pricelist_version_ids[0], qty))
                    res1 = cr.dictfetchall()
                uom_price_already_computed = False
                for res in res1:
                    if res:
                        if res['base'] == -1:
                            if not res['base_pricelist_id']:
                                price = 0.0
                            else:
                                price_tmp = self.price_get(cr, uid,
                                        [res['base_pricelist_id']], product_id,
                                        qty, context=context)[res['base_pricelist_id']]
                                ptype_src = self.browse(cr, uid, res['base_pricelist_id']).currency_id.id
                                uom_price_already_computed = True
                                price = currency_obj.compute(cr, uid,
                                        ptype_src, res['currency_id'],
                                        price_tmp, round=False,
                                        context=context)
                        elif res['base'] == -2:
                            # this section could be improved by moving the queries outside the loop:
                            where = []
                            if partner:
                                where = [('name', '=', partner) ]
                            sinfo = supplierinfo_obj.search(cr, uid,
                                    [('product_id', '=', tmpl_id)] + where)
                            price = 0.0
                            if sinfo:
                                qty_in_product_uom = qty
                                product_default_uom = product_obj.read(cr, uid, [product_id], ['uom_id'])[0]['uom_id'][0]
                                supplier = supplierinfo_obj.browse(cr, uid, sinfo, context=context)[0]
                                seller_uom = supplier.product_uom and supplier.product_uom.id or False
                                if seller_uom and product_default_uom and product_default_uom != seller_uom:
                                    uom_price_already_computed = True
                                    qty_in_product_uom = product_uom_obj._compute_qty(cr, uid, product_default_uom, qty, to_uom_id=seller_uom)
                                cr.execute('SELECT * ' \
                                        'FROM pricelist_partnerinfo ' \
                                        'WHERE suppinfo_id IN %s' \
                                            'AND min_quantity <= %s ' \
                                        'ORDER BY min_quantity DESC LIMIT 1', (tuple(sinfo),qty_in_product_uom,))
                                res2 = cr.dictfetchone()
                                if res2:
                                    price = res2['price']

                        elif res['base'] == -3:
                            if 'fixed_per' in res and res['fixed_per'] == 'metric':
                                #NBA. If the Fixed Price is based on metric, multiply by the given metric so that the resulting subtotal will be Listprice*(Metric*Quantity)
                                price = res['fixed_amount']*(metric or 1.0)
                            else:
                                price = res['fixed_amount']

                        else:
                            price_type = price_type_obj.browse(cr, uid, int(res['base']))
                            uom_price_already_computed = True
                            price = currency_obj.compute(cr, uid,
                                    price_type.currency_id.id, res['currency_id'],
                                    product_obj.price_get(cr, uid, [product_id],
                                    price_type.field, context=context)[product_id], round=False, context=context)

                        if price is not False:
                            price_limit = price
                            price = price * (1.0+(res['price_discount'] or 0.0))
                            price = rounding(price, res['price_round']) #TOFIX: rounding with tools.float_rouding
                            price += (res['price_surcharge'] or 0.0)
                            if res['price_min_margin']:
                                price = max(price, price_limit+res['price_min_margin'])
                            if res['price_max_margin']:
                                price = min(price, price_limit+res['price_max_margin'])
                            break

                    else:
                        # False means no valid line found ! But we may not raise an
                        # exception here because it breaks the search
                        price = False

                if price:
                    results['item_id'] = res['id']
                    if 'uom' in context and not uom_price_already_computed:
                        product = products_dict[product_id]
                        uom = product.uos_id or product.uom_id
                        price = product_uom_obj._compute_price(cr, uid, uom.id, price, context['uom'])

                if results.get(product_id):
                    results[product_id][pricelist_id] = price
                else:
                    results[product_id] = {pricelist_id: price}

        return results
