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

class account_invoice_line(osv.osv):
    _inherit='account.invoice.line'

    def _get_total_dimension(self, cr, uid, ids, name, args, context=None):
        res={}
        for line in self.browse(cr, uid, ids):
            res[line.id]={'total_dimension': None, 'total_dimension_display': None}
            uom_obj=line.product_dimension.uom_id

            product_qty=line.quantity
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


    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):

        res=super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom_id, qty=qty, name=name, type=type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, context=context, company_id=company_id)

        if not context:
            context={}

        dimension=context.get('product_dimension')

        #Set the product domain
        if product:
            product_obj=self.pool.get('product.product').browse(cr, uid, product)
            #To be sure that we're adding a domain
            if not res['domain']:
                res['domain']={}

            dimension_ids=[]

            if product_obj.dimension_ids:
                for dimension in product_obj.dimension_ids:
                    if product_obj.metric_type:
                        if dimension.metric_type==product_obj.metric_type:
                            dimension_ids.append(dimension.id)
                    else:
                        dimension_ids.append(dimension.id)

                res['domain']['product_dimension']=[('id','in',dimension_ids)]
            elif product_obj.metric_type:
                dimension_ids=self.pool.get('product.dimension').search(cr, uid, [('metric_type','=',product_obj.metric_type)])
                res['domain']['product_dimension']=[('id','in',dimension_ids)]

            #To be sure that product_dimension is between dimension_ids
            if dimension_ids:
                if context.get('product_dimension'):
                    if context.get('product_dimension') not in dimension_ids:
                        res['value'].update({'product_dimension': False})
                        if not res.get('warning'):
                            res['warning']={}
                        res['warning'].update({'title': _('Dimension removed'),
                                               'message': _('Dimension selected is not valid for this product, please select another dimension')})
            else:
                res['domain']['product_dimension']=[]


        return res

account_invoice_line()