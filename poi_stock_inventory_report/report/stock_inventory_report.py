# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Devintelle Software Solutions (<http://devintellecs.com>).
#
##############################################################################
import time
from datetime import datetime
from dateutil import relativedelta
import itertools
from operator import itemgetter
import operator

from datetime import datetime, timedelta
from odoo import api, models


class stock_inv_report(models.AbstractModel):
    _name = 'report.poi_stock_inventory_report.stock_inventory_template'


    @api.multi
    def get_warehouse_data(self,data):
        return data
        
    @api.multi    
    def get_wizard_data(self,data):
        return data
        
    @api.multi
    def get_availabel_quantity(self, product, warehouse_id,data):
        in_qty = self.get_before_incoming_qty(product, warehouse_id,data)
        out_qty = self.get_before_outgoing_qty(product, warehouse_id,data)
        adjust_qty = self.get_begining_adjustment_qty(product, warehouse_id,data)
        total_qty = in_qty - out_qty + adjust_qty
        return total_qty
        
    
    @api.multi
    def get_begining_adjustment_qty(self, product, warehouse_id,data):
        state = 'done'
        parent_left = data.location_id.parent_left
        parent_right = data.location_id.parent_right
        if not data.location_id:
            parent_left = warehouse_id.view_location_id.parent_left
            parent_right = warehouse_id.view_location_id.parent_right

        sq_location_ids = self.env['stock.location'].search(
            [('parent_left', '>=', parent_left), ('parent_left', '<', parent_right)]).ids

        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                                  JOIN product_product as pp ON pp.id = sm.product_id \
                                  where sm.date < %s and \
                                  sm.location_dest_id in %s and sm.product_id = %s and sm.picking_type_id is null\
                                  and sm.state = %s and sm.company_id = %s
                                  """

        start_date = str(data.start_date) + ' 00:00:00'

        params = (start_date, tuple(sq_location_ids), product.id, state, data.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0
        
    def get_product(self,data):
        product_pool=self.env['product.product']
        if not data.filter_by:
            product_ids = product_pool.search([('type','!=','service')])
            return product_ids
        elif data.filter_by == 'product' and data.product_ids:
            return data.product_ids
        elif data.filter_by == 'category' and data.category_id:
            product_ids = product_pool.search([('categ_id','child_of',data.category_id.id),('type','!=','service')])
            return product_ids
            
    @api.multi
    def get_sale_qty(self, product, warehouse_id,data):
        state = 'done'
        move_type = 'outgoing'
        m_type = ''
        if data.location_id:
            m_type = 'and sm.location_id = %s'

        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                          JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                          JOIN product_product as pp ON pp.id = sm.product_id \
                          where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
                          and spt.code = %s """ + m_type + """and sm.product_id = %s \
                          and sm.state = %s and sm.company_id = %s
                          """

        start_date = str(data.start_date) + ' 00:00:00'
        end_date = str(data.end_date) + ' 23:59:59'

        if data.location_id:
            params = (start_date, end_date, warehouse_id.id, move_type, data.location_id.id, product.id, state,
                      data.company_id.id)
        else:
            params = (start_date, end_date, warehouse_id.id, move_type, product.id, state, data.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0
        
    @api.multi
    def get_adjustment_qty(self, product, warehouse_id,data):
        state = 'done'
        parent_left = data.location_id.parent_left
        parent_right = data.location_id.parent_right
        if not data.location_id:
            parent_left = warehouse_id.view_location_id.parent_left
            parent_right = warehouse_id.view_location_id.parent_right

        sq_location_ids = self.env['stock.location'].search(
            [('parent_left', '>=', parent_left), ('parent_left', '<', parent_right)]).ids

        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                                  JOIN product_product as pp ON pp.id = sm.product_id \
                                  where sm.date >= %s and sm.date <= %s and \
                                  sm.location_dest_id in %s and sm.product_id = %s and sm.picking_type_id is null\
                                  and sm.state = %s and sm.company_id = %s
                                  """

        start_date = str(data.start_date) + ' 00:00:00'
        end_date = str(data.end_date) + ' 23:59:59'

        params = (start_date, end_date, tuple(sq_location_ids), product.id, state, data.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0
    
    @api.multi
    def get_lines(self,data):
        lst=[]
        for warehouse_id in data.warehouse_ids:
            product_ids = self.get_product(data)
            for product in product_ids:
                beginning_qty = self.get_availabel_quantity(product, warehouse_id,data)
                received_qty = self.get_receive_qty(product, warehouse_id,data)
                sale_qty = self.get_sale_qty(product,warehouse_id,data)
                internal_qty = self.get_internal_qty(product, warehouse_id,data)
                adjust_qty = self.get_adjustment_qty(product, warehouse_id,data)
                ending_qty = (beginning_qty + received_qty + adjust_qty) - sale_qty
                if not data.is_zero:
                    if beginning_qty != 0 or received_qty != 0 or sale_qty != 0 or  adjust_qty != 0 or ending_qty != 0:
                        lst.append({
                            'category':product.categ_id.name or 'Untitle',
                            'product':product.name,
                            'beginning_qty':beginning_qty,
                            'received_qty':received_qty,
                            'sale_qty':sale_qty,
                            'internal_qty':internal_qty,
                            'adjust_qty':adjust_qty,
                            'ending_qty':ending_qty,
                        })
                else:
                    lst.append({
                        'category': product.categ_id.name or 'Untitle',
                        'product': product.name,
                        'beginning_qty': beginning_qty,
                        'received_qty': received_qty,
                        'sale_qty': sale_qty,
                        'internal_qty': internal_qty,
                        'adjust_qty': adjust_qty,
                        'ending_qty': ending_qty,
                    })
            return lst
        

    @api.multi
    def get_before_incoming_qty(self,product, warehouse_id,data):
        state = 'done'
        move_type = 'incoming'
        m_type = ''
        if data.location_id:
            m_type = 'and sm.location_dest_id = %s'
        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                              JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                              JOIN product_product as pp ON pp.id = sm.product_id \
                              where sm.date < %s and spt.warehouse_id = %s \
                              and spt.code = %s """ + m_type + """and sm.product_id = %s \
                              and sm.state = %s and sm.company_id = %s
                              """

        start_date = str(data.start_date) + ' 00:00:00'
        if data.location_id:
            params = (start_date,warehouse_id.id, move_type, data.location_id.id, product.id, state,
                      data.company_id.id)
        else:
            params = (start_date, warehouse_id.id, move_type, product.id, state, data.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0
        
    @api.multi
    def get_before_outgoing_qty(self, product, warehouse_id,data):
        state = 'done'
        move_type = 'outgoing'
        m_type = ''
        if data.location_id:
            m_type = 'and sm.location_id = %s'

        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                                  JOIN product_product as pp ON pp.id = sm.product_id \
                                  where sm.date < %s and spt.warehouse_id = %s \
                                  and spt.code = %s """ + m_type + """and sm.product_id = %s \
                                  and sm.state = %s and sm.company_id = %s
                                  """

        start_date = str(data.start_date) + ' 00:00:00'

        if data.location_id:
            params = (start_date, warehouse_id.id, move_type, data.location_id.id, product.id, state,
                      data.company_id.id)
        else:
            params = (start_date, warehouse_id.id, move_type, product.id, state, data.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0
        
    @api.multi
    def get_receive_qty(self, product, warehouse_id,data):
        state = 'done'
        move_type = 'incoming'
        m_type = ''
        if data.location_id:
            m_type = 'and sm.location_dest_id = %s'
        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                      JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                      JOIN product_product as pp ON pp.id = sm.product_id \
                      where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
                      and spt.code = %s """ + m_type + """and sm.product_id = %s \
                      and sm.state = %s and sm.company_id = %s
                      """

        start_date = str(data.start_date)+ ' 00:00:00'
        end_date = str(data.end_date) + ' 23:59:59'

        if data.location_id:
            params = (start_date, end_date, warehouse_id.id, move_type, data.location_id.id, product.id, state,
                      data.company_id.id)
        else:
            params = (start_date, end_date, warehouse_id.id, move_type, product.id, state,data.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0
        
    @api.multi
    def get_internal_qty(self, product, warehouse_id,data):
        state = 'done'
        move_type = 'internal'
        m_type = ''
        if data.location_id:
            m_type = 'and sm.location_dest_id = %s'

        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                              JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                              JOIN product_product as pp ON pp.id = sm.product_id \
                              where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
                              and spt.code = %s """ + m_type + """and sm.product_id = %s \
                              and sm.state = %s and sm.company_id = %s
                              """

        start_date = str(data.start_date) + ' 00:00:00'
        end_date = str(data.end_date) + ' 23:59:59'

        if data.location_id:
            params = (start_date, end_date, warehouse_id.id, move_type, data.location_id.id, product.id, state,
                      data.company_id.id)
        else:
            params = (start_date, end_date, warehouse_id.id, move_type, product.id, state, data.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0
    
        
        
    @api.multi
    def get_report_values(self, docids, data=None):
        docs = self.env['dev.stock.inventory'].browse(data['form'])
        return {
            'doc_ids': docs.ids,
            'doc_model': 'dev.stock.inventory',
            'docs': docs,
            'proforma': True,
            'get_warehouse_data':self.get_warehouse_data(docs.warehouse_ids),
            'get_wizard_data':self.get_wizard_data(docs),
            'get_lines':self.get_lines(docs)
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
