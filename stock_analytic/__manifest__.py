# Copyright 2013 Julius Network Solutions
# Copyright 2015 Clear Corp
# Copyright 2016 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Cuentas Analíticas Inventarios",
    "summary": "Agraga cuenta analitica a movimientos de inventario",
    "version": "11.0.1.0.0",
    "author": "Julius Network Solutions,"
              "ClearCorp, OpenSynergy Indonesia,"
              "Odoo Community Association (OCA)",
    "website": "http://www.julius.fr/",
    "category": "Warehouse Management",
    "license": "AGPL-3",
    "depends": [
        "stock_account",
        "analytic",
    ],
    "data": [
        "views/stock_move_views.xml",
        "views/stock_inventory_views.xml",
    ],
    'installable': True,
}
