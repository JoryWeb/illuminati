# © 2017 Miguel Angel Callisaya Mamani
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3


{
    'name': 'Plan Anual de Ventas',
    'version': '9.0.1.0.0',
    "author": "PoiesisConsulting"
              "Miguel Angel Callisaya Mamani",
    'category': 'Purchase Management',
    'website': 'http://www.poiesisconsulting.com',
    'summary': 'Planificación de compras Toyosa',
    'depends': [
        'base',
        'poi_x_toyosa',
    ],
    'data': [
        'data/original_annual_plan_sequence.xml',
        'views/original_annual_plan_view.xml',
        #'security/purchase_landed_cost_security.xml',
        #'security/ir.model.access.csv',
    ],
    'installable': False,
}
