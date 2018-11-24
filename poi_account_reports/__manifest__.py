# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Accounting Reports',
    'author' : 'Poiesis Consulting, Odoo SA',
    'summary': 'View and create reports',
    'description': """
Accounting Reports
====================
* General Ledger
* Trial Balance

ToDo:
-----
* Balance Sheet
* Cash Flow
* Profit and Loss
* Income Statements

    """,
    'depends': ['account',
                #'poi_account_advanced',
                #'poi_account_analytic',
                #'poi_account_sequence'
                ],
    'data': [
        #'security/ir.model.access.csv',
        'data/reports_menu.xml',
        'views/poi_account_reports.xml',
        'views/account_report_view.xml',
        'views/report_financial.xml',
        'data/general_ledger.xml',
        'data/trial_balance.xml',
        #'report/account_asset_report.xml',
        #'views/printable_reports.xml',
    ],
    'qweb': [
        'static/src/xml/account_report_backend.xml',
    ],
    'auto_install': False,
    'installable': False,
    'sequence': 1,
    'application': True,
}
