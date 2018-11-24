# © 2017 Miguel Angel Callisaya Mamani
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3


{
    'name': 'UFV Inventarios',
    'version': '11.0.1.0.0',
    "author": "PoiesisConsulting"
              "Miguel Angel Callisaya Mamani",
    'category': 'Purchase Management',
    'website': 'http://www.poiesisconsulting.com',
    'summary': 'Actualización Inventarios UFV',
    'depends': [
        #'poi_bol_base',
        'stock',
        'stock_landed_costs'
    ],
    'data': [
        'data/ufv_inventory_sequence.xml',
        #'data/base_config.xml',
        'views/ufv_inventory_view.xml',
        'views/product_view.xml',
        #'security/ir.model.access.csv',
    ],
    'installable': True,
}
