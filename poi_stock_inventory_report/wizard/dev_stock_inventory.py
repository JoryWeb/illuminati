# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Devintelle Solutions (<http://devintellecs.com/>).
#
##############################################################################

import io
from datetime import datetime
from odoo import models, fields,api, _
import xlwt
from xlwt import easyxf
import base64
import itertools
from operator import itemgetter
import operator

class dev_stock_inventory(models.TransientModel):
    _name = "dev.stock.inventory"

    @api.model
    def _get_company_id(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company',string='Company',required="1", default=_get_company_id)
    warehouse_ids = fields.Many2many('stock.warehouse',string='Warehouse',required="1")
    location_id = fields.Many2one('stock.location',string='Location', domain="[('usage','!=','view')]")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    filter_by = fields.Selection([('product','Product'),('category','Product Category')],string='Filter By', default='product')
    category_id = fields.Many2one('product.category',string='Category')
    product_ids = fields.Many2many('product.product',string='Products')
    is_group_by_category = fields.Boolean('Group By Category')
    is_zero = fields.Boolean('With Zero Values')

    @api.multi
    def get_before_incoming_qty(self,product, warehouse_id):
        state = 'done'
        move_type = 'incoming'
        m_type = ''
        if self.location_id:
            m_type = 'and sm.location_dest_id = %s'
        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                              JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                              JOIN product_product as pp ON pp.id = sm.product_id \
                              where sm.date < %s and spt.warehouse_id = %s \
                              and spt.code = %s """ + m_type + """and sm.product_id = %s \
                              and sm.state = %s and sm.company_id = %s
                              """

        start_date = str(self.start_date) + ' 00:00:00'
        if self.location_id:
            params = (start_date,warehouse_id.id, move_type, self.location_id.id, product.id, state,
                      self.company_id.id)
        else:
            params = (start_date, warehouse_id.id, move_type, product.id, state, self.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0

    @api.multi
    def get_before_outgoing_qty(self, product, warehouse_id):
        state = 'done'
        move_type = 'outgoing'
        m_type = ''
        if self.location_id:
            m_type = 'and sm.location_id = %s'

        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                                  JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                                  JOIN product_product as pp ON pp.id = sm.product_id \
                                  where sm.date < %s and spt.warehouse_id = %s \
                                  and spt.code = %s """ + m_type + """and sm.product_id = %s \
                                  and sm.state = %s and sm.company_id = %s
                                  """

        start_date = str(self.start_date) + ' 00:00:00'

        if self.location_id:
            params = (start_date, warehouse_id.id, move_type, self.location_id.id, product.id, state,
                      self.company_id.id)
        else:
            params = (start_date, warehouse_id.id, move_type, product.id, state, self.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0

    @api.multi
    def get_availabel_quantity(self, product, warehouse_id):
        in_qty = self.get_before_incoming_qty(product, warehouse_id)
        out_qty = self.get_before_outgoing_qty(product, warehouse_id)
        adjust_qty = self.get_begining_adjustment_qty(product, warehouse_id)
        total_qty = in_qty - out_qty + adjust_qty
        return total_qty



    @api.multi
    def get_begining_adjustment_qty(self, product, warehouse_id):
        state = 'done'
        parent_left = self.location_id.parent_left
        parent_right = self.location_id.parent_right
        if not self.location_id:
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

        start_date = str(self.start_date) + ' 00:00:00'

        params = (start_date, tuple(sq_location_ids), product.id, state, self.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0
        
    
    
    @api.multi
    def get_receive_qty(self, product, warehouse_id):
        state = 'done'
        move_type = 'incoming'
        m_type = ''
        if self.location_id:
            m_type = 'and sm.location_dest_id = %s'
        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                      JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                      JOIN product_product as pp ON pp.id = sm.product_id \
                      where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
                      and spt.code = %s """ + m_type + """and sm.product_id = %s \
                      and sm.state = %s and sm.company_id = %s
                      """

        start_date = str(self.start_date)+ ' 00:00:00'
        end_date = str(self.end_date) + ' 23:59:59'

        if self.location_id:
            params = (start_date, end_date, warehouse_id.id, move_type, self.location_id.id, product.id, state,
                      self.company_id.id)
        else:
            params = (start_date, end_date, warehouse_id.id, move_type, product.id, state,self.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0

    @api.multi
    def get_sale_qty(self, product, warehouse_id):
        state = 'done'
        move_type = 'outgoing'
        m_type = ''
        if self.location_id:
            m_type = 'and sm.location_id = %s'

        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                          JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                          JOIN product_product as pp ON pp.id = sm.product_id \
                          where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
                          and spt.code = %s """ + m_type + """and sm.product_id = %s \
                          and sm.state = %s and sm.company_id = %s
                          """

        start_date = str(self.start_date) + ' 00:00:00'
        end_date = str(self.end_date) + ' 23:59:59'

        if self.location_id:
            params = (start_date, end_date, warehouse_id.id, move_type, self.location_id.id, product.id, state,
                      self.company_id.id)
        else:
            params = (start_date, end_date, warehouse_id.id, move_type, product.id, state, self.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0

    @api.multi
    def get_internal_qty(self, product, warehouse_id):
        state = 'done'
        move_type = 'internal'
        m_type = ''
        if self.location_id:
            m_type = 'and sm.location_dest_id = %s'

        query = """select sum(sm.product_uom_qty) from stock_move as sm \
                              JOIN stock_picking_type as spt ON spt.id = sm.picking_type_id \
                              JOIN product_product as pp ON pp.id = sm.product_id \
                              where sm.date >= %s and sm.date <= %s and spt.warehouse_id = %s \
                              and spt.code = %s """ + m_type + """and sm.product_id = %s \
                              and sm.state = %s and sm.company_id = %s
                              """

        start_date = str(self.start_date) + ' 00:00:00'
        end_date = str(self.end_date) + ' 23:59:59'

        if self.location_id:
            params = (start_date, end_date, warehouse_id.id, move_type, self.location_id.id, product.id, state,
                      self.company_id.id)
        else:
            params = (start_date, end_date, warehouse_id.id, move_type, product.id, state, self.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0

    @api.multi
    def get_adjustment_qty(self, product, warehouse_id):
        state = 'done'
        parent_left = self.location_id.parent_left
        parent_right = self.location_id.parent_right
        if not self.location_id:
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

        start_date = str(self.start_date) + ' 00:00:00'
        end_date = str(self.end_date) + ' 23:59:59'

        params = (start_date, end_date, tuple(sq_location_ids), product.id, state, self.company_id.id)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        if result[0].get('sum'):
            return result[0].get('sum')
        return 0.0


    def get_product(self):
        product_pool=self.env['product.product']
        if not self.filter_by:
            product_ids = product_pool.search([('type','!=','service')])
            return product_ids
        elif self.filter_by == 'product' and self.product_ids:
            return self.product_ids
        elif self.filter_by == 'category' and self.category_id:
            product_ids = product_pool.search([('categ_id','child_of',self.category_id.id),('type','!=','service')])
            return product_ids

    @api.multi
    def group_by_lines(self,lst):
        n_lst = sorted(lst, key=itemgetter('category'))
        groups = itertools.groupby(n_lst, key=operator.itemgetter('category'))
        group_lines = [{'category': k, 'values': [x for x in v]} for k, v in groups]
        return group_lines

    @api.multi
    def get_lines(self,warehouse_id):
        lst=[]
        product_ids = self.get_product()
        for product in product_ids:
            beginning_qty = self.get_availabel_quantity(product, warehouse_id)
            received_qty = self.get_receive_qty(product, warehouse_id)
            sale_qty = self.get_sale_qty(product,warehouse_id)
            internal_qty = self.get_internal_qty(product, warehouse_id)
            adjust_qty = self.get_adjustment_qty(product, warehouse_id)
            ending_qty = (beginning_qty + received_qty + adjust_qty) - sale_qty
            if not self.is_zero:
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
    def print_pdf(self):
        data = self.read()
        datas = {
            'form': self.id
        }
        return self.env.ref('poi_stock_inventory_report.print_dev_stock_inventory').report_action(self, data=datas)


    @api.multi
    def export_stock_ledger(self):
        workbook = xlwt.Workbook()
        filename = 'Existencias.xls'
        # Style
        main_header_style = easyxf('font:height 400;pattern: pattern solid, fore_color gray25;'
                                   'align: horiz center;font: color black; font:bold True;'
                                   "borders: top thin,left thin,right thin,bottom thin")

        header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz center;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")

        group_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz left;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")

        text_left = easyxf('font:height 150; align: horiz left;' "borders: top thin,bottom thin")
        text_right_bold = easyxf('font:height 200; align: horiz right;font:bold True;' "borders: top thin,bottom thin")
        text_right_bold1 = easyxf('font:height 200; align: horiz right;font:bold True;' "borders: top thin,bottom thin", num_format_str='0.00')
        text_center = easyxf('font:height 150; align: horiz center;' "borders: top thin,bottom thin")
        text_right = easyxf('font:height 150; align: horiz right;' "borders: top thin,bottom thin",
                            num_format_str='0.00')

        worksheet = []
        for l in range(0, len(self.warehouse_ids)):
            worksheet.append(l)
        work=0
        for warehouse_id in self.warehouse_ids:
            worksheet[work] = workbook.add_sheet(warehouse_id.name)
            for i in range(0, 9):
                worksheet[work].col(i).width = 140 * 30

            worksheet[work].write_merge(0, 1, 0, 9, 'INVENTARIO DE EXISTENCIAS', main_header_style)

            worksheet[work].write(4, 0, 'Compañia', header_style)
            worksheet[work].write(4, 1, 'Almacén', header_style)
            worksheet[work].write(4, 2, 'Ubicación', header_style)
            worksheet[work].write(4, 3, 'Fecha de inicio', header_style)
            worksheet[work].write(4, 4, 'Fecha fin', header_style)
            worksheet[work].write(4, 5, 'Generado por', header_style)
            worksheet[work].write(4, 6, 'Generado en', header_style)



            worksheet[work].write(5, 0, self.company_id.name, text_center)
            worksheet[work].write(5, 1, warehouse_id.name, text_center)
            worksheet[work].write(5, 2, self.location_id.name or '', text_center)
            start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
            start_date = start_date.strftime("%d-%m-%Y")
            worksheet[work].write(5, 3, start_date, text_center)
            end_date = datetime.strptime(self.end_date, '%Y-%m-%d')
            end_date = end_date.strftime("%d-%m-%Y")
            worksheet[work].write(5, 4, end_date, text_center)
            worksheet[work].write(5, 5, self.env.user.name, text_center)
            g_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            worksheet[work].write(5, 6, g_date, text_center)



            tags = ['Inicial', 'Recibido', 'Ventas', 'Interno', 'Ajustes', 'Final']

            r= 8
            worksheet[work].write_merge(r, r, 0, 3, 'Productos', header_style)
            c = 4
            for tag in tags:
                worksheet[work].write(r, c, tag, header_style)
                c+=1

            lines=self.get_lines(warehouse_id)
            if not self.is_group_by_category:
                r=9
                b_qty = r_qty = s_qty = i_qty = a_qty = e_qty = 0
                for line in lines:
                    b_qty += line.get('beginning_qty')
                    r_qty += line.get('received_qty')
                    s_qty += line.get('sale_qty')
                    i_qty += line.get('internal_qty')
                    a_qty += line.get('adjust_qty')
                    e_qty += line.get('ending_qty')
                    worksheet[work].write_merge(r, r, 0, 3, line.get('product'), text_left)
                    c=4
                    worksheet[work].write(r, c, line.get('beginning_qty'), text_right)
                    c+=1
                    worksheet[work].write(r, c, line.get('received_qty'), text_right)
                    c+=1
                    worksheet[work].write(r, c, line.get('sale_qty'), text_right)
                    c += 1
                    worksheet[work].write(r, c, line.get('internal_qty'), text_right)
                    c += 1
                    worksheet[work].write(r, c, line.get('adjust_qty'), text_right)
                    c += 1
                    worksheet[work].write(r, c, line.get('ending_qty'), text_right)
                    r+=1
                worksheet[work].write_merge(r, r, 0, 3, 'TOTAL', text_right_bold)
                c = 4
                worksheet[work].write(r, c, b_qty, text_right_bold1)
                c += 1
                worksheet[work].write(r, c, r_qty, text_right_bold1)
                c += 1
                worksheet[work].write(r, c, s_qty, text_right_bold1)
                c += 1
                worksheet[work].write(r, c, i_qty, text_right_bold1)
                c += 1
                worksheet[work].write(r, c, a_qty, text_right_bold1)
                c += 1
                worksheet[work].write(r, c, e_qty, text_right_bold1)
                r += 1
            else:
                lines = self.group_by_lines(lines)
                r = 9
                for l_val in lines:
                    worksheet[work].write_merge(r, r, 0, 9, l_val.get('category'), group_style)
                    r+=1
                    b_qty = r_qty = s_qty = i_qty = a_qty = e_qty =0
                    for line in l_val.get('values'):
                        b_qty += line.get('beginning_qty')
                        r_qty += line.get('received_qty')
                        s_qty += line.get('sale_qty')
                        i_qty += line.get('internal_qty')
                        a_qty += line.get('adjust_qty')
                        e_qty += line.get('ending_qty')
                        worksheet[work].write_merge(r, r, 0, 3, line.get('product'), text_left)
                        c = 4
                        worksheet[work].write(r, c, line.get('beginning_qty'), text_right)
                        c += 1
                        worksheet[work].write(r, c, line.get('received_qty'), text_right)
                        c += 1
                        worksheet[work].write(r, c, line.get('sale_qty'), text_right)
                        c += 1
                        worksheet[work].write(r, c, line.get('internal_qty'), text_right)
                        c += 1
                        worksheet[work].write(r, c, line.get('adjust_qty'), text_right)
                        c += 1
                        worksheet[work].write(r, c, line.get('ending_qty'), text_right)
                        r += 1
                    worksheet[work].write_merge(r, r, 0, 3, 'TOTAL', text_right_bold)
                    c = 4
                    worksheet[work].write(r, c, b_qty, text_right_bold1)
                    c += 1
                    worksheet[work].write(r, c, r_qty , text_right_bold1)
                    c += 1
                    worksheet[work].write(r, c, s_qty , text_right_bold1)
                    c += 1
                    worksheet[work].write(r, c, i_qty , text_right_bold1)
                    c += 1
                    worksheet[work].write(r, c, a_qty , text_right_bold1)
                    c += 1
                    worksheet[work].write(r, c, e_qty , text_right_bold1)
                    r += 1



            work+=1

        fp = io.BytesIO()
        workbook.save(fp)
        export_id = self.env['dev.stock.inventory.excel'].create(
            {'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
        fp.close()

        return {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'dev.stock.inventory.excel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }



class dev_stock_inventory_excel(models.TransientModel):
    _name = "dev.stock.inventory.excel"

    excel_file = fields.Binary('Excel Report')
    file_name = fields.Char('Excel File')

