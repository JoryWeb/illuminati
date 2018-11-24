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

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp

class product_dimension(osv.osv):
    _name='product.dimension'

    def _get_total_computed(self, cr, uid, ids, name, args, context=None):
        res={}
        for dimension in self.browse(cr, uid, ids):
            if dimension.metric_type=='lineal':
                res[dimension.id]=dimension.var_x
            elif dimension.metric_type=='area':
                res[dimension.id]=dimension.var_x*dimension.var_y
            elif dimension.metric_type=='volume':
                res[dimension.id]=dimension.var_x*dimension.var_y*dimension.var_z
        return res

    def _get_total_uom(self, cr, uid, ids, name, args, context=None):
        res={}
        for dimension in self.browse(cr, uid, ids):
            if dimension.uom_id:
                if dimension.metric_type=='lineal':
                    res[dimension.id]=dimension.uom_id.name
                elif dimension.metric_type=='area':
                    res[dimension.id]=dimension.uom_id.name+u"²"
                elif dimension.metric_type=='volume':
                    res[dimension.id]=dimension.uom_id.name+u"³"
        return res

    _columns = {
        'metric_type': fields.selection([('lineal', 'Lineal'), ('area', 'Area'), ('volume', 'Volume')], 'Metric Type'),
        'var_x': fields.float('X', digits_compute = dp.get_precision('Metric')),
        'var_y': fields.float('Y', digits_compute = dp.get_precision('Metric')),
        'var_z': fields.float('Z', digits_compute = dp.get_precision('Metric')),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure'),
        'total_computed': fields.function(_get_total_computed, type="float", string="Total", store=True, digits_compute= dp.get_precision('TotalMetric')),
        'uom_total': fields.function(_get_total_uom, type="char", string="Total UOM"),
    }

    def get_total_computed(self, cr, uid, ids, context=None):
        total_dimension = 0
        if ids:
            dimension = self.browse(cr, uid, ids[0])
            if dimension.metric_type=='lineal':
                total_dimension=dimension.var_x
            elif dimension.metric_type=='area':
                total_dimension=dimension.var_x*dimension.var_y
            elif dimension.metric_type=='volume':
                total_dimension=dimension.var_x*dimension.var_y*dimension.var_z
        return total_dimension


    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (int)):
            ids = [ids]

        res=[]
        for dimension in self.browse(cr, uid, ids):
            if dimension.uom_id:
                uom_name=dimension.uom_id.name
            else:
                uom_name=''
            if dimension.metric_type=='lineal':
                res.append((dimension.id, str(dimension.var_x)+uom_name))
            elif dimension.metric_type=='area':
                res.append((dimension.id, str(dimension.var_x)+uom_name+' x '+str(dimension.var_y)+uom_name))
            elif dimension.metric_type=='volume':
                res.append((dimension.id, str(dimension.var_x)+uom_name+' x '+str(dimension.var_y)+uom_name+' x '+str(dimension.var_z)+uom_name))
        return res


    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []

        if name:
            query_to_exe = """
                SELECT product_dimension.id
                FROM product_dimension
                WHERE
                product_dimension.id>0
                """
            words=name.split(' ')
            for word in words:
                query_to_exe+="""
                    AND (cast(product_dimension.var_x as text) ilike '%"""+word+"""%' OR cast(product_dimension.var_y as text) ilike '%"""+word+"""%' OR cast(product_dimension.var_z as text) ilike '%"""+word+"""%')
                    """
            query_to_exe += """LIMIT """+str(limit)
            cr.execute(query_to_exe)
            vals=cr.fetchall()

            products=[]

            for a in vals:
                products.append(a[0])

            ids=products

        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

    def onchange_dimensions(self, cr, uid, ids, metric_type, uom_id, var_x, var_y, var_z, context=None):
        uom_pool=self.pool.get('product.uom')

        res={}
        res['value']={}
        if metric_type=='lineal':
            res['value']['total_computed']=var_x
        elif metric_type=='area':
            res['value']['total_computed']=var_x*var_y
        elif metric_type=='volume':
            res['value']['total_computed']=var_x*var_y*var_z

        if uom_id:
            uom_obj=uom_pool.browse(cr, uid, uom_id)
            if metric_type=='lineal':
                res['value']['uom_total'] = uom_obj.name
            elif metric_type=='area':
                res['value']['uom_total'] = uom_obj.name+u"²"
            elif metric_type=='volume':
                res['value']['uom_total'] = uom_obj.name+u"³"

        return res
