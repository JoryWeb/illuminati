# © 2017 Miguel Angel Callisaya Mamani
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3

{
    'name': 'Solicitud de Armado de Motocicletas',
    'version': '9.0.1.0.0',
    "author": "PoiesisConsulting"
              " Miguel Angel Callisaya Mamani",
    'category': 'Inventory',
    'website': 'http://www.poiesisconsulting.com',
    'summary': 'Armado de Motocicletas',
    'depends': [
        'stock',
    ],
    'data': [
        'data/poi_stock_armado_sequence.xml',
        'views/poi_stock_armado_view.xml',
        #'security/purchase_landed_cost_security.xml',
        #'security/ir.model.access.csv',
    ],
    'installable': False,
}
