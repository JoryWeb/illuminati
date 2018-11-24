{
    'name': "Poiesis Account Move Templates",
    'version': '1.0',
    'category': 'Accounting',
    'summary': "Templates for recurring Journal Entries",
    'author': "Poiesis Consulting",
    'website': 'http://www.poiesisconsulting.com',
    'depends': ['analytic', 'account', 'poi_trace'],
    'data': [
        'security/ir.model.access.csv',
        'views/move_template.xml',
        'wizard/select_template.xml',
    ],

    'installable': True,
}
