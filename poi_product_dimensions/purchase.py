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
from openerp.tools.translate import _


class purchase_order(osv.osv):
    _inherit='purchase.order'

    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        res=super(purchase_order, self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context)

        if order_line.product_dimension:
            lot_id=self._get_dimension_lot_id(cr, uid, order_line.product_id.id, order_line.product_dimension.id, context=context)
            res['name']=res['name']+" ["+order_line.product_dimension.name_get()[0][1]+"]"
            res['prodlot_id']=lot_id

        return res

    def _get_dimension_lot_id(self, cr, uid, product_id, dimension_id, context=None):
        stock_lot_pool = self.pool.get('stock.production.lot')
        product_pool = self.pool.get('product.product')
        dimension_pool = self.pool.get('product.dimension')

        lot_ids=stock_lot_pool.search(cr, uid, [('product_id','=',product_id),('dimension_id','=',dimension_id)])
        if lot_ids:
            return lot_ids[0]
        else:
            product_name=product_pool.browse(cr, uid, product_id).name_get()[0][1]
            dimension_name=dimension_pool.browse(cr, uid, dimension_id).name_get()[0][1]

            lot_name=product_name+" ["+dimension_name+"]"

            lot_id=stock_lot_pool.create(cr, uid, {'name': lot_name,
                                            'product_id': product_id,
                                            'dimension_id': dimension_id})
            return lot_id

class purchase_order_line(osv.osv):
    _inherit='purchase.order.line'

    def _get_total_dimension(self, cr, uid, ids, name, args, context=None):
        res={}
        for line in self.browse(cr, uid, ids):
            res[line.id]={'total_dimension': None, 'total_dimension_display': None}
            uom_obj=line.product_dimension.uom_id

            product_qty=line.product_qty
            var_x=line.product_dimension.var_x
            var_y=line.product_dimension.var_y
            var_z=line.product_dimension.var_z

            if line.product_dimension.metric_type=='lineal':
                res[line.id]['total_dimension']=var_x*product_qty
                res[line.id]['total_dimension_display'] = str(var_x*product_qty)+uom_obj.name
            elif line.product_dimension.metric_type=='area':
                res[line.id]['total_dimension']=var_x*var_y*product_qty
                res[line.id]['total_dimension_display'] = str(var_x*var_y*product_qty)+uom_obj.name+u"²"
            elif line.product_dimension.metric_type=='volume':
                res[line.id]['total_dimension']=var_x*var_y*var_z*product_qty
                res[line.id]['total_dimension_display'] = str(var_x*var_y*var_z*product_qty)+uom_obj.name+u"³"
            else:
                res[line.id]['total_dimension']=None
                res[line.id]['total_dimension_display']=None
        return res

    _columns={
        'product_dimension': fields.many2one('product.dimension','Dimension'),
        'total_dimension': fields.function(_get_total_dimension, type="float", string="Total Metric w/o unit", store=True, multi="total_dimension"),
        'total_dimension_display': fields.function(_get_total_dimension, type="char", string="Total Metric", multi="total_dimension"),
    }

    def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None, dimension=None):
        """
        onchange handler of product_uom.
        """
        if not uom_id:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        return self.onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, context=context, dimension=dimension)


    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None, dimension=None):

        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, context=context)

        context = context or {}
        product_product = self.pool.get('product.product')
        product_pricelist = self.pool.get('product.pricelist')
        if product_id:
            product = product_product.browse(cr, uid, product_id, context=context)

        if dimension and product_id:
            metric=self.pool.get('product.dimension').browse(cr, uid, dimension).total_computed

            if pricelist_id:
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                        product.id, qty or 1.0, partner_id or False, {'uom': uom_id,
                                                                      'date': date_order,
                                                                      'metric': metric or False,})[pricelist_id]
                if price is False:
                    res['value'].update({'price_unit': 0})
            else:
                price = product.standard_price

            res['value'].update({'price_unit': price})


        #Set the product domain
        if product_id:
            if product.dimension_ids:
                dimension_ids=[]
                for dimension in product.dimension_ids:
                    if dimension.metric_type==product.metric_type:
                        dimension_ids.append(dimension.id)
                if not res['domain']:
                    res['domain']={}
                res['domain']['product_dimension']=[('id','=',dimension_ids)]

        return res