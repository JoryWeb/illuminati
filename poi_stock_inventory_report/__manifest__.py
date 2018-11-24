# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Devintelle Solutions (<http://devintellecs.com/>).
#
##############################################################################
{
    'name': 'Stock Inventory Real Time Report(PDF/XLS)',
    'version': '1.1',
    'sequence':1,
    'category': 'Stock',
    'description': """
        Print Stock Inventory Report -Beginning, Received, Sales, Internal, Adjustment, Ending
        
        Inventory Report, Beginning Stock, Received Stock, Sales Stock, Internal Stock , Adjustment Stock, Ending  Stock
        
        Real Time Inventory Report
        """,
    'summary': 'Print Stock Inventory Report -Beginning, Received, Sales, Internal, Adjustment, Ending',
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com/',
    'depends': ['sale_stock','purchase'],
    'data': [
        'wizard/dev_stock_inventory_views.xml',
        'report/stock_inventory_template.xml',
        'report/dev_stock_inventory_menu.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price':49.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
