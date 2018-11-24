# (c) 2010 NaN Projectes de Programari Lliure, S.L. (http://www.NaN-tic.com)
# (c) 2014 Serv. Tec. Avanzados - Pedro M. Baeza
# (c) 2014 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Adaptaciones Alina",
    "version": "9.0.1.3.0",
    "category": "Base",
    "license": "AGPL-3",
    "author": "Poiesis Consulting "
              "Serv. Tecnol. Avanzados - Miguel Angel Callisaya, ",
    "website": "http://www.poiesisconsulting.com",
    "contributors": [
        "Miguel Angel <miguel.callisaya@poiesisconsulting.com>",
    ],
    "depends": [
        "mrp",
        "product",
        "account",
        "poi_bank",
    ],
    "data": [
        #"data/quality_control_data.xml",
        "security/landicorp_control_security.xml",
        #"security/ir.model.access.csv",
        #"wizard/qc_test_wizard_view.xml",
        "views/mrp_production_view.xml",
        "views/product_supplierinfo_view.xml",
        "views/product_view.xml",
        "views/stock_view.xml",
        "views/res_partner_view.xml",
        "views/report_mrporder_alina.xml",
        "views/account_payment_view.xml",
        "mrp_report_alina.xml",
    ],
    "demo": [
        #"demo/quality_control_demo.xml",
    ],
    "installable": False,
}
