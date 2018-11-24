# -*- coding: utf-8 -*-
{
    'name': "citasRMAM",

    'summary': """
        Calendario de citas""",

    'description': """
        Visualiza citas
    """,

    'author': "Rafael Manuel Alfonso Moreno",
    'website': "http://www.google.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Citas',
    'version': '1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],

    	'images': [
        'static/description/imagen.png',
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'installable': True,
    'auto_install': False,  
}