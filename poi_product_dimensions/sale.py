##############################################################################
#
#    Poiesis Consulting, OpenERP Partner
#    Copyright (C) 2013 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Coded by: Grover Menacho
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

from openerp.osv import osv, fields
from openerp import api, models
from openerp.tools.translate import _


class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _prepare_order_picking(self, cr, uid, order, context=None):
        res = super(sale_order, self)._prepare_order_picking(cr, uid, order, context=None)
        total_metric = order.total_metric
        total_metric_m2 = order.total_metric_m2
        total_metric_m3 = order.total_metric_m3
        total_weight = order.total_weight
        res['total_metric'] = total_metric
        res['total_metric_m2'] = total_metric_m2
        res['total_metric_m3'] = total_metric_m3
        res['total_weight'] = total_weight

        return res

    # Ya no aplica en la version 9
    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):

        res = super(sale_order, self)._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned,
                                                               context=context)

        if line.product_dimension:
            lot_id = self._get_dimension_lot_id(cr, uid, line.product_id.id, line.product_dimension.id, context=context)
            total_dim = line.get_total_dimension()[line.id] or 0.0
            top_uom = line.product_dimension and line.product_dimension.uom_id.name or ''
            metric_type = line.get_metric_type()[line.id]

            if (metric_type) == 'lineal':
                total_dim = str(total_dim) + ' ' + top_uom
            else:
                if (metric_type) == 'area':
                    total_dim = str(total_dim) + ' ' + top_uom + u"²"
                else:
                    if (metric_type) == 'volume':
                        total_dim = str(total_dim) + ' ' + top_uom + u"³"
                    else:
                        total_dim = str(total_dim)

            res['name'] = res['name'] + " [" + line.product_dimension.name_get()[0][1] + "]"
            res['prodlot_id'] = lot_id
            res['total_dimension_display'] = total_dim

        return res

    def _get_dimension_lot_id(self, cr, uid, product_id, dimension_id, context=None):
        stock_lot_pool = self.pool.get('stock.production.lot')
        product_pool = self.pool.get('product.product')
        dimension_pool = self.pool.get('product.dimension')

        lot_ids = stock_lot_pool.search(cr, uid, [('product_id', '=', product_id), ('dimension_id', '=', dimension_id)])
        if lot_ids:
            return lot_ids[0]
        else:
            product_name = product_pool.browse(cr, uid, product_id).name_get()[0][1]
            dimension_name = dimension_pool.browse(cr, uid, dimension_id).name_get()[0][1]

            lot_name = product_name + " [" + dimension_name + "]"

            lot_id = stock_lot_pool.create(cr, uid, {'name': lot_name,
                                                     'product_id': product_id,
                                                     'dimension_id': dimension_id})
            return lot_id


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'

    # def _get_total_dimension(self, cr, uid, ids, name, args, context=None):
    #     res = {}
    #     for line in self.browse(cr, uid, ids):
    #         res[line.id] = {'total_dimension': None, 'total_dimension_display': None}
    #         uom_obj = line.product_dimension.uom_id
    #
    #         product_qty = line.product_uom_qty
    #         var_x = line.product_dimension.var_x
    #         var_y = line.product_dimension.var_y
    #         var_z = line.product_dimension.var_z
    #
    #         if line.product_dimension.metric_type == 'lineal':
    #             res[line.id]['total_dimension'] = var_x * product_qty
    #             res[line.id]['total_dimension_display'] = str(var_x * product_qty) + uom_obj.name
    #         elif line.product_dimension.metric_type == 'area':
    #             res[line.id]['total_dimension'] = var_x * var_y * product_qty
    #             res[line.id]['total_dimension_display'] = str(var_x * var_y * product_qty) + uom_obj.name + u"²"
    #         elif line.product_dimension.metric_type == 'volume':
    #             res[line.id]['total_dimension'] = var_x * var_y * var_z * product_qty
    #             res[line.id]['total_dimension_display'] = str(var_x * var_y * var_z * product_qty) + uom_obj.name + u"³"
    #         else:
    #             res[line.id]['total_dimension'] = None
    #             res[line.id]['total_dimension_display'] = None
    #     return res

    _columns = {
        'lot_id': fields.many2one('stock.production.lot', 'Lote', copy=True),
        'product_dimension': fields.many2one('product.dimension', 'Dimension'),
    }

    # def get_total_dimension(self, cr, uid, ids, context=None):
    #     res = {}
    #     for line in self.browse(cr, uid, ids):
    #         res[line.id] = None
    #         uom_obj = line.product_dimension.uom_id
    #
    #         product_qty = line.product_uom_qty
    #         var_x = line.product_dimension.var_x
    #         var_y = line.product_dimension.var_y
    #         var_z = line.product_dimension.var_z
    #
    #         if line.product_dimension.metric_type == 'lineal':
    #             res[line.id] = var_x * product_qty
    #         elif line.product_dimension.metric_type == 'area':
    #             res[line.id] = var_x * var_y * product_qty
    #         elif line.product_dimension.metric_type == 'volume':
    #             res[line.id] = var_x * var_y * var_z * product_qty
    #         else:
    #             res[line.id] = None
    #     return res
    #
    # def get_metric_type(self, cr, uid, ids, context=None):
    #     res = {}
    #     for line in self.browse(cr, uid, ids):
    #         res[line.id] = None
    #         uom_obj = line.product_dimension.uom_id
    #
    #         res[line.id] = line.product_dimension.metric_type
    #
    #     return res

    # def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
    #                       uom=False, qty_uos=0, uos=False, name='', partner_id=False,
    #                       lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False,
    #                       flag=False, context=None):
    #
    #     res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
    #                                                          uom=uom, qty_uos=qty_uos, uos=uos, name=name,
    #                                                          partner_id=partner_id,
    #                                                          lang=lang, update_tax=update_tax, date_order=date_order,
    #                                                          packaging=packaging, fiscal_position=fiscal_position,
    #                                                          flag=flag, context=context)
    #
    #     context = context or {}
    #
    #     # TODO: This pricelist must be according dimensions given on sale order line
    #     dimension = context.get('product_dimension')
    #     if dimension and product:
    #         dim_pool = self.pool.get('product.dimension')
    #         metric = dim_pool.browse(cr, uid, dimension).get_total_computed()
    #
    #         warning_msgs = ""
    #
    #         if not pricelist:
    #             warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
    #                          'Please set one before choosing a product.')
    #             warning_msgs += _("No Pricelist ! : ") + warn_msg + "\n\n"
    #         else:
    #             price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
    #                                                                  product, qty or 1.0, partner_id, {
    #                                                                      'uom': uom or res.get('product_uom'),
    #                                                                      'date': date_order,
    #                                                                      'metric': metric or False,
    #                                                                  })[pricelist]
    #             if price is False:
    #                 warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
    #                              "You have to change either the product, the quantity or the pricelist.")
    #
    #                 warning_msgs += _("No valid pricelist line found ! :") + warn_msg + "\n\n"
    #                 res['value'].update({'price_unit': 0})
    #             else:
    #                 res['value'].update({'price_unit': price})
    #
    #         # NBA. Change product description to specify dimension
    #         dim_name = dim_pool.name_get(cr, uid, dimension) or ''
    #         name_change = 'name' in res['value'] and res['value']['name'] or False
    #         if not name_change:
    #             prod_data = \
    #             self.pool.get('product.product').read(cr, uid, [product], ['default_code', 'name'], context=context)[0]
    #             name_change = "[%s] %s" % (prod_data['default_code'], prod_data['name'])
    #         res['value'].update({'name': "%s (%s)" % (name_change, dim_name[0][1])})
    #
    #     # Set the product domain
    #     if product:
    #         product_obj = self.pool.get('product.product').browse(cr, uid, product)
    #         # To be sure that we're adding a domain
    #         if not res['domain']:
    #             res['domain'] = {}
    #
    #         dimension_ids = []
    #
    #         if product_obj.dimension_ids:
    #             for dimension in product_obj.dimension_ids:
    #                 if product_obj.metric_type:
    #                     if dimension.metric_type == product_obj.metric_type:
    #                         dimension_ids.append(dimension.id)
    #                 else:
    #                     dimension_ids.append(dimension.id)
    #
    #             res['domain']['product_dimension'] = [('id', 'in', dimension_ids)]
    #         elif product_obj.metric_type:
    #             dimension_ids = self.pool.get('product.dimension').search(cr, uid, [
    #                 ('metric_type', '=', product_obj.metric_type)])
    #             res['domain']['product_dimension'] = [('id', 'in', dimension_ids)]
    #
    #         # To be sure that product_dimension is between dimension_ids
    #         if dimension_ids:
    #             if context.get('product_dimension'):
    #                 if context.get('product_dimension') not in dimension_ids:
    #                     res['value'].update({'product_dimension': False})
    #                     res['value'].update({'name': name_change})
    #                     if not res.get('warning'):
    #                         res['warning'] = {}
    #                     res['warning'].update({'title': _('Dimension removed'),
    #                                            'message': _(
    #                                                'La dimensión seleccionada no es valida para este producto, por favor seleccione otra dimensión')})
    #         else:
    #             res['domain']['product_dimension'] = []
    #
    #     return res

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id=account_id,
                                                                            context=context)
        if not line.invoiced:
            res.update({'product_dimension': line.product_dimension and line.product_dimension.id or False})
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom', 'product_uom_qty', 'product_dimension')
    def product_uom_change(self):
        if not self.product_uom:
            self.price_unit = 0.0
            return {}

        self._compute_tax_id()

        # ctx = dict(self._context)
        # dimension = ctx['product_dimension']
        dimension = self.product_dimension
        vals = {}
        res = {}
        res.setdefault('domain', {})
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        # Aqui se corrige la descripcion de la linea de la venta con datos
        # del produccto y descripción de dimensión
        if product.description_sale:
            name += '\n' + product.description_sale

        if dimension:
            vals['name'] = name + ' (' + dimension.name_get()[0][1] + ')'
        else:
            vals['name'] = name
        ids_d = self.product_id.dimension_ids.ids
        # Actualizar domain dinamicamente para no tener que aplicar restricción de medidas
        res['domain'] = {'product_dimension': [('id', 'in', ids_d)]}

        if dimension and self.order_id.pricelist_id:
            # Control de tarifa y dimensiones permitidas
            price_products = self.env['product.pricelist.item'].search(
                [("pricelist_id", "=", self.order_id.pricelist_id.id), ("product_id", "=", self.product_id.id)])
            # Realizar busqueda de producto en esta parte
            dimension_ids = self.product_id.dimension_ids.ids
            if price_products:
                price_product = price_products[0]
                valido = True
                for item in dimension_ids:
                    if item == self.product_dimension.id:
                        valido = False
                if valido:
                    vals['product_dimension'] = False
                    vals['price_unit'] = 0.0
                    vals['product_uom_qty'] = 0.0
                    res = {'warning': {
                        'title': _('Advertencia'),
                        'message': _(
                            u'La dimensión seleccionada no es valida para este producto, por favor seleccione otra dimensión')
                    }}
                else:
                    lot_ids = self.env['stock.production.lot'].search(
                        [('product_id', '=', self.product_id.id), ('dimension_id', '=', dimension.id)])
                    if lot_ids:
                        vals['lot_id'] = lot_ids[0].id
                        # if self.product_id.metric_type == 'lineal':
                        #     if dimension.var_y == 0 and dimension.var_z == 0:
                        #         #if (dimension.var_x < price_product.min_metric or dimension.var_x > price_product.max_metric):
                        #          if valido:
                        #             vals['product_dimension'] = False
                        #             vals['price_unit'] = 0.0
                        #             res = {'warning': {
                        #                 'title': _('Advertencia'),
                        #                 'message': _(u'La dimensión seleccionada no es valida para este producto, por favor seleccione otra dimensión')
                        #             }}
                        # if self.product_id.metric_type == 'volume':
                        #     total_volume = dimension.var_x * dimension.var_y * dimension.var_z
                        #     #if (total_volume < price_product.min_metric or total_volume > price_product.max_metric):
                        #     if valido:
                        #         vals['product_dimension'] = False
                        #         vals['price_unit'] = 0.0
                        #         res = {'warning': {
                        #             'title': _('Advertencia'),
                        #             'message': _(
                        #                 u'La dimensión seleccionada no es valida para este producto, por favor seleccione otra dimensión')
                        #         }}

        metric = self.product_dimension.get_total_computed()
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date_order=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position'),
                metric=metric,
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id,
                                                                              self.tax_id)
        self.update(vals)
        return res

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if self.product_dimension:
            res.update({
                'product_dimension': self.product_dimension.id,
            })
        return res
