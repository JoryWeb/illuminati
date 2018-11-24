import logging
from odoo import fields, models, api, _
from odoo.exceptions import Warning
from itertools import chain
import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
_logger = logging.getLogger(__name__)

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.multi
    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
        """ Low-level method - Mono pricelist, multi products
        Returns: dict{product_id: (price, suitable_rule) for the given pricelist}

        If date in context: Date of the pricelist (%Y-%m-%d)

            :param products_qty_partner: list of typles products, quantity, partner
            :param datetime date: validity date
            :param ID uom_id: intermediate unit of measure
        """
        self.ensure_one()
        if not date:
            date = self._context.get('date') or fields.Date.context_today(self)
        if not uom_id and self._context.get('uom'):
            uom_id = self._context['uom']
        if uom_id:
            # rebrowse with uom if given
            products = [item[0].with_context(uom=uom_id) for item in products_qty_partner]
            products_qty_partner = [(products[index], data_struct[1], data_struct[2]) for index, data_struct in enumerate(products_qty_partner)]
        else:
            products = [item[0] for item in products_qty_partner]

        if not products:
            return {}

        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = list(categ_ids)

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
        if self._context.get('year_id', False):
            year_id = self._context.get('year_id', False)
            self._cr.execute(
                'SELECT item.id '
                'FROM product_pricelist_item AS item '
                'LEFT JOIN product_category AS categ '
                'ON item.categ_id = categ.id '
                'WHERE (item.product_tmpl_id IS NULL OR item.product_tmpl_id = any(%s))'
                'AND (item.product_id IS NULL OR item.product_id = any(%s))'
                'AND (item.categ_id IS NULL OR item.categ_id = any(%s)) '
                'AND (year_id IS NULL OR year_id = %s)'
                'AND (item.pricelist_id = %s) '
                'AND (item.date_start IS NULL OR item.date_start<=%s) '
                'AND (item.date_end IS NULL OR item.date_end>=%s)'
                'ORDER BY item.applied_on, item.min_quantity desc, categ.parent_left desc',
                (prod_tmpl_ids, prod_ids, categ_ids, year_id, self.id, date, date))
        else:
            self._cr.execute(
                'SELECT item.id '
                'FROM product_pricelist_item AS item '
                'LEFT JOIN product_category AS categ '
                'ON item.categ_id = categ.id '
                'WHERE (item.product_tmpl_id IS NULL OR item.product_tmpl_id = any(%s))'
                'AND (item.product_id IS NULL OR item.product_id = any(%s))'
                'AND (item.categ_id IS NULL OR item.categ_id = any(%s)) '
                'AND (item.pricelist_id = %s) '
                'AND (item.date_start IS NULL OR item.date_start<=%s) '
                'AND (item.date_end IS NULL OR item.date_end>=%s)'
                'ORDER BY item.applied_on, item.min_quantity desc, categ.parent_left desc',
                (prod_tmpl_ids, prod_ids, categ_ids, self.id, date, date))

        item_ids = [x[0] for x in self._cr.fetchall()]
        items = self.env['product.pricelist.item'].browse(item_ids)
        results = {}
        for product, qty, partner in products_qty_partner:
            results[product.id] = 0.0
            suitable_rule = False

            # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
            # An intermediary unit price may be computed according to a different UoM, in
            # which case the price_uom_id contains that UoM.
            # The final price will be converted to match `qty_uom_id`.
            qty_uom_id = self._context.get('uom') or product.uom_id.id
            price_uom_id = product.uom_id.id
            qty_in_product_uom = qty
            if qty_uom_id != product.uom_id.id:
                try:
                    qty_in_product_uom = self.env['product.uom'].browse([self._context['uom']])._compute_quantity(qty, product.uom_id)
                except UserError:
                    # Ignored - incompatible UoM in context, use default product UoM
                    pass

            # if Public user try to access standard price from website sale, need to call price_compute.
            # TDE SURPRISE: product can actually be a template
            price = product.price_compute('list_price')[product.id]

            price_uom = self.env['product.uom'].browse([qty_uom_id])
            for rule in items:
                if rule.min_quantity and qty_in_product_uom < rule.min_quantity:
                    continue
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and not (product.product_variant_count == 1 and product.product_variant_id.id == rule.product_id.id):
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
                    price_tmp = rule.base_pricelist_id._compute_price_rule([(product, qty, partner)])[product.id][0]  # TDE: 0 = price, 1 = rule
                    price = rule.base_pricelist_id.currency_id.compute(price_tmp, self.currency_id, round=False)
                else:
                    # if base option is public price take sale price else cost price of product
                    # price_compute returns the price in the context UoM, i.e. qty_uom_id
                    price = product.price_compute(rule.base)[product.id]

                convert_to_price_uom = (lambda price: product.uom_id._compute_price(price, price_uom))

                if price is not False:
                    if rule.compute_price == 'fixed':
                        price = convert_to_price_uom(rule.fixed_price)
                    elif rule.compute_price == 'percentage':
                        price = (price - (price * (rule.percent_price / 100))) or 0.0
                    else:
                        # complete formula
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
                price = product.currency_id.compute(price, self.currency_id, round=False)

            results[product.id] = (price, suitable_rule and suitable_rule.id or False)

        return results


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    year_id = fields.Many2one('anio.toyosa', u'Año Modelo')


class ProductPricelistAssistant(models.Model):
    _name = 'product.pricelist.assistant'
    _description = 'Asistente de actualizacion de Lista de Precio'
    _authmode = True

    name = fields.Char('Descripcion', readonly=True, states={'draft':[('readonly',False)]})
    pricelist_id = fields.Many2one('product.pricelist', 'Lista de Precio', readonly=True, states={'draft':[('readonly',False)]})
    pricelist_id2 = fields.Many2one('product.pricelist', 'Lista de Precios Cif', readonly=True, states={'draft':[('readonly',False)]})
    year_id = fields.Many2one('anio.toyosa', u'Año Modelo', readonly=True, states={'draft':[('readonly',False)]})
    product_id = fields.Many2one('product.template', 'Producto', readonly=True, states={'draft':[('readonly',False)]})
    item_ids = fields.One2many('product.pricelist.assistant.item', 'assistant_id', 'Items', readonly=True, states={'draft':[('readonly',False)]})
    date = fields.Date('Fecha', default=fields.Date.today(), readonly=True, states={'draft':[('readonly',False)]})
    compute_price  = fields.Selection(
        string="Caculo de Precio",
        selection=[
            ('fixed', 'Precio Fijo'),
            ('current_i', 'Precio Actual + Incremento'),
            ('percentage', 'Porcetanje Sobre el Precio Actual'),
        ], default="fixed", readonly=True, states={'draft':[('readonly',False)]}
    )
    amount = fields.Float('Monto/Porcentaje', readonly=True, states={'draft':[('readonly',False)]})
    state = fields.Selection(
        string="Estado",
        selection=[
            ('draft', 'Borrrador'),
            ('done', 'Realizado'),
        ], default="draft", readonly=True, states={'draft':[('readonly',False)]}
    )
    circuit_check = fields.Boolean('Aprobado', default=False, readonly=True, states={'draft':[('readonly',False)]})

    @api.onchange("pricelist_id", "year_id", "product_id")
    def _onchange_pricelist_id(self):
        if self.pricelist_id:
            domain = []
            data = []
            domain.append(['compute_price', '=', 'fixed'])
            domain.append(['applied_on', '=', '1_product'])
            self.item_ids = False
            items_obj = self.env['product.pricelist.item']
            if self.pricelist_id:
                domain.append(['pricelist_id', '=', self.pricelist_id.id])
            if self.year_id:
                domain.append(['year_id', '=', self.year_id.id])
            if self.product_id:
                domain.append(['product_tmpl_id', '=', self.product_id.id])

            items_ids = items_obj.search(domain)
            for i in items_ids:
                data.append([0,0,{'product_id': i.product_tmpl_id.id, 'current_price': i.fixed_price, 'year_id': (i.year_id and i.year_id.id) or False, 'item_id': i.id}])
            self.item_ids = data


    @api.onchange("amount", "compute_price")
    def _onchange_amount(self):
        if self.amount:
            if self.compute_price == 'fixed':
                for i in self.item_ids:
                    i.new_price = self.amount
            if self.compute_price == 'current_i':
                for i in self.item_ids:
                    i.new_price = i.current_price + self.amount
            if self.compute_price == 'percentage':
                for i in self.item_ids:
                    i.new_price = ((i.current_price * self.amount) / 100) + i.current_price

        else:
            for i in self.item_ids:
                i.new_price = None
    @api.multi
    def action_send_circuit(self):
        for i in self.item_ids:
            if not i.item_id:
                raise Warning('No se puede Enviar a Circuito de Aprobacion por tener una linea que no corresponde a ninguna lista de precios.')
        auth = self.check_authorization(code='product.pricelist.update')
        if auth:
            self.action_confirm()
            self._refresh_price()
            self.circuit_check = True

    @api.multi
    def action_confirm(self):
        self.state = 'done'

    @api.multi
    def on_authorized(self):
        code = self.auth_log_id.auth_id.code
        res = super(ProductPricelistAssistant, self).on_authorized()
        if code == 'product.pricelist.update':
            self.action_send_circuit()

    def _refresh_price(self):
        pricelist_obj = self.env['product.pricelist.item']
        for i in self.item_ids:
            i.item_id.fixed_price = i.new_price
            if self.pricelist_id2  and self.pricelist_id2.id:
                item_id = pricelist_obj.search([('pricelist_id', '=', self.pricelist_id2.id), ('product_tmpl_id', '=', i.product_id.id), ('year_id', '=', i.year_id.id)])
                if item_id:
                    item_id[0].fixed_price = i.new_price_cif


class ProductPricelistAssistantItem(models.Model):
    _name = 'product.pricelist.assistant.item'
    _description = 'Items a actualizar listas de Precio'

    assistant_id = fields.Many2one('product.pricelist.assistant', 'Asistente')
    product_id = fields.Many2one('product.template', 'Producto', readonly=True)
    year_id = fields.Many2one('anio.toyosa', u'Año Modelo', readonly=True)
    current_price = fields.Float('Precio Actual', readonly=True)
    new_price = fields.Float('Precio Nuevo')
    new_price_cif = fields.Float('Precio Cif')
    item_id = fields.Many2one('product.pricelist.item', 'Item_id')
