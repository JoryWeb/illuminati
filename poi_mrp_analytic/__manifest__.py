# Copyright 2013 Julius Network Solutions
# Copyright 2015 Clear Corp
# Copyright 2016 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "MRP Analytic",
    "summary": "Cuentas analíticas en producción",
    "version": "9.0.1.0.0",
    "author": "Julius Network Solutions,"
              "ClearCorp, OpenSynergy Indonesia,"
              "Odoo Community Association (OCA)",
    "website": "http://www.julius.fr/",
    "category": "Production",
    "license": "AGPL-3",
    "depends": [
        "stock_analytic", "mrp"
    ],
    "data": [
        "views/mrp_views.xml",
    ],
    'installable': False,
}
