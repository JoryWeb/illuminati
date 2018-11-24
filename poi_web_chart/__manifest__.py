{
    'name': 'Web Charts',
    'category': 'Hidden',
    'description': """
Web Charts for Web Client.
===========================

    * Parse a <chart> view but allows changing dynamically the presentation
""",
    'version': '1.0',
    'depends': ['web'],
    'data' : [
        'views/poi_web_chart.xml',
    ],
    'qweb' : [
        'static/src/xml/*.xml',
    ],
    'installable': False,
    'auto_install': True
}
